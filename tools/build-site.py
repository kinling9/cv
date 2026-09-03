#!/usr/bin/env python3
"""Generate the static HTML CV from the LaTeX sources.

Generating rather than hand-writing the HTML keeps the .tex files the single
source of truth: editing employment.tex updates the PDF and the web page
together, so the two cannot drift apart.

This script deliberately never reads personal.tex, and `make docs` runs it over
a tree exported with `git ls-files`, where that file is absent anyway.
tools/check-docs.sh then greps the generated HTML as a final check.
"""

import argparse
import html
import io
import os
import re
import shutil

# ---------------------------------------------------------------- LaTeX ----


def strip_comments(text):
    """Drop % comments, honouring \\% escapes."""
    out = []
    for line in text.split("\n"):
        buf, i = [], 0
        while i < len(line):
            c = line[i]
            if c == "\\" and i + 1 < len(line):
                buf.append(line[i:i + 2])
                i += 2
                continue
            if c == "%":
                break
            buf.append(c)
            i += 1
        out.append("".join(buf))
    return "\n".join(out)


def read_group(s, i):
    """s[i] must be '{'. Return (contents, index just past the '}')."""
    if i >= len(s) or s[i] != "{":
        raise ValueError("expected '{' at %d" % i)
    depth, start = 0, i + 1
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    raise ValueError("unbalanced braces")


def read_optional(s, i):
    """Read a [...] argument if present. Return (contents_or_None, new_i)."""
    j = i
    while j < len(s) and s[j] in " \t\n":
        j += 1
    if j < len(s) and s[j] == "[":
        depth, start = 0, j + 1
        k = j
        while k < len(s):
            if s[k] == "\\":
                k += 2
                continue
            if s[k] == "[":
                depth += 1
            elif s[k] == "]":
                depth -= 1
                if depth == 0:
                    return s[start:k], k + 1
            k += 1
    return None, i


# Commands rendered as a wrapping tag around one argument.
WRAP = {
    "textbf": "strong",
    "textsc": "strong",
    "emph": "em",
    "textit": "em",
    "texttt": "code",
    "underline": "u",
}

# Commands with no argument, replaced by literal text.
LITERAL = {
    "LaTeX": "LaTeX",
    "TeX": "TeX",
    "ldots": "\u2026",
    "dots": "\u2026",
    "textbackslash": "\\",
    "hfill": "",
    "noindent": "",
    "par": "",
    "centering": "",
    "small": "",
    "normalsize": "",
}

# Commands whose arguments are dropped entirely (layout-only).
DROP_ARGS = {
    "setlength": 2,
    "vspace": 1,
    "hspace": 1,
    "noentry": 1,
    "label": 1,
    "index": 1,
}


def to_html(s, cites=None):
    """Convert an inline LaTeX fragment to HTML."""
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]

        if c == "\\":
            m = re.match(r"\\([a-zA-Z]+)\*?", s[i:])
            if not m:
                # Escaped literal such as \& \_ \% \# \{ \}
                if i + 1 < n:
                    out.append(html.escape(s[i + 1]))
                    i += 2
                else:
                    i += 1
                continue

            cmd = m.group(1)
            j = i + m.end()

            if cmd in LITERAL:
                out.append(html.escape(LITERAL[cmd]) if cmd == "textbackslash"
                           else LITERAL[cmd])
                i = j
                continue

            if cmd in DROP_ARGS:
                for _ in range(DROP_ARGS[cmd]):
                    _, j = read_optional(s, j)
                    if j < n and s[j] == "{":
                        _, j = read_group(s, j)
                i = j
                continue

            if cmd in WRAP:
                _, j = read_optional(s, j)
                if j < n and s[j] == "{":
                    arg, j = read_group(s, j)
                    tag = WRAP[cmd]
                    out.append("<%s>%s</%s>" % (tag, to_html(arg, cites), tag))
                i = j
                continue

            if cmd == "href":
                url, j = read_group(s, j)
                text, j = read_group(s, j)
                out.append('<a href="%s">%s</a>'
                           % (html.escape(url, quote=True), to_html(text, cites)))
                i = j
                continue

            if cmd == "url":
                url, j = read_group(s, j)
                out.append('<a href="%s">%s</a>'
                           % (html.escape(url, quote=True), html.escape(url)))
                i = j
                continue

            if cmd == "cite":
                keys, j = read_group(s, j)
                refs = [k.strip() for k in keys.split(",") if k.strip()]
                if cites is not None:
                    cites.extend(refs)
                links = ", ".join(
                    '<a class="cite" href="#pub-%s">%s</a>'
                    % (html.escape(k, quote=True), html.escape(k))
                    for k in refs)
                out.append('<span class="cites">[%s]</span>' % links)
                i = j
                continue

            # Unknown command: drop the command, keep any braced argument.
            _, j = read_optional(s, j)
            if j < n and s[j] == "{":
                arg, j = read_group(s, j)
                out.append(to_html(arg, cites))
            i = j
            continue

        if c == "{":
            arg, i = read_group(s, i)
            out.append(to_html(arg, cites))
            continue

        if c == "}":
            i += 1
            continue

        if c == "~":
            out.append("&nbsp;")
            i += 1
            continue

        if c == "$":
            i += 1
            continue

        if c == "-":
            run = len(s[i:]) - len(s[i:].lstrip("-"))
            dash = {2: "\u2013", 3: "\u2014"}.get(run, "-" * run)
            out.append(dash)
            i += run
            continue

        out.append(html.escape(c))
        i += 1

    text = "".join(out)
    text = re.sub(r"[ \t\n]+", " ", text)
    return text.strip()


def render_body(body, cites):
    """Convert an entry body (may contain \\par and itemize) to HTML blocks."""
    blocks = []

    def flush_text(chunk):
        for part in re.split(r"\\par\b", chunk):
            h = to_html(part, cites)
            if h:
                blocks.append("<p>%s</p>" % h)

    pos = 0
    for m in re.finditer(r"\\begin\{itemize\}(.*?)\\end\{itemize\}", body, re.S):
        flush_text(body[pos:m.start()])
        items = re.split(r"\\item\b", m.group(1))
        lis = []
        for it in items[1:]:
            h = to_html(it, cites)
            if h:
                lis.append("<li>%s</li>" % h)
        if lis:
            blocks.append("<ul>%s</ul>" % "".join(lis))
        pos = m.end()
    flush_text(body[pos:])
    return "\n".join(blocks)


def parse_rubrics(path, cites):
    """Parse one section file into [{'title', 'groups': [{'sub', 'entries'}]}]."""
    text = strip_comments(io.open(path, encoding="utf-8").read())
    sections = []
    for rm in re.finditer(r"\\begin\{rubric\}\s*\{", text):
        title, after = read_group(text, rm.end() - 1)
        end = text.find("\\end{rubric}", after)
        inner = text[after:end if end != -1 else len(text)]

        groups, current = [], {"sub": None, "entries": []}
        pos = 0
        # Walk \subrubric and \entry* markers in order.
        markers = list(re.finditer(r"\\subrubric\s*\{|\\entry\*?\s*\[", inner))
        for idx, mm in enumerate(markers):
            stop = markers[idx + 1].start() if idx + 1 < len(markers) else len(inner)
            if mm.group(0).startswith("\\subrubric"):
                sub, after_sub = read_group(inner, mm.end() - 1)
                if current["entries"]:
                    groups.append(current)
                current = {"sub": to_html(sub, cites), "entries": []}
                pos = after_sub
            else:
                key, after_key = read_optional(inner, mm.end() - 1)
                body = inner[after_key:stop]
                current["entries"].append({
                    "key": to_html(key or "", cites),
                    "body": render_body(body, cites),
                })
        if current["entries"] or current["sub"]:
            groups.append(current)
        sections.append({"title": to_html(title, cites), "groups": groups})
    return sections


# ------------------------------------------------------------------ bib ----


def parse_bib(path):
    text = io.open(path, encoding="utf-8").read()
    entries, i = [], 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        m = re.match(r"@(\w+)\s*\{", text[at:])
        if not m:
            i = at + 1
            continue
        etype = m.group(1).lower()
        brace = at + m.end() - 1
        try:
            body, nxt = read_group(text, brace)
        except ValueError:
            break
        key, _, rest = body.partition(",")
        fields, p = {}, 0
        while p < len(rest):
            fm = re.compile(r"\s*([a-zA-Z\-]+)\s*=\s*").match(rest, p)
            if not fm:
                break
            name, p = fm.group(1).lower(), fm.end()
            if p < len(rest) and rest[p] == "{":
                val, p = read_group(rest, p)
            elif p < len(rest) and rest[p] == '"':
                q = rest.find('"', p + 1)
                val, p = rest[p + 1:q], q + 1
            else:
                vm = re.compile(r"[^,]*").match(rest, p)
                val, p = vm.group(0), vm.end()
            fields[name] = val.strip()
            while p < len(rest) and rest[p] in ", \n\t":
                p += 1
        fields["type"] = etype
        fields["key"] = key.strip()
        entries.append(fields)
        i = nxt
    return entries


def format_authors(raw, highlight="Wei"):
    parts = re.split(r"\s+and\s+", raw)
    names = []
    for nm in parts:
        nm = " ".join(nm.split())
        if not nm:
            continue
        if nm == "others":
            names.append("<em>et al.</em>")
            continue
        if "," in nm:
            family, given = [x.strip() for x in nm.split(",", 1)]
        else:
            bits = nm.split()
            family, given = bits[-1], " ".join(bits[:-1])
        initials = " ".join(
            g[0] + "." for g in re.split(r"[\s\-]+", given) if g)
        disp = ("%s %s" % (initials, family)).strip()
        disp = to_html(disp)
        if family == highlight:
            disp = "<strong>%s</strong>" % disp
        names.append(disp)
    return ", ".join(names)


def order_publications(entries):
    """Newest first, matching the PDF's sorting=ydnt."""
    return sorted(entries, key=lambda e: (e.get("year", ""), e.get("key", "")),
                  reverse=True)


def render_publications(entries, heading, cited_keys):
    rows = []
    for e in entries:
        venue = e.get("booktitle") or e.get("journal") or e.get("publisher") or ""
        bits = []
        title = to_html(e.get("title", ""))
        bits.append('<span class="pub-title">%s</span>' % title)
        if venue:
            bits.append('<span class="pub-venue">%s</span>' % to_html(venue))
        meta = []
        if e.get("volume"):
            meta.append("vol.&nbsp;%s" % to_html(e["volume"]))
        if e.get("pages"):
            meta.append("pp.&nbsp;%s" % to_html(e["pages"].replace("--", "\u2013")))
        if meta:
            bits.append('<span class="pub-meta">%s</span>' % ", ".join(meta))
        star = ' <span class="pub-flag" title="cited in this CV">&#9733;</span>' \
            if e.get("key") in cited_keys else ""
        rows.append(
            '<li id="pub-%s" class="pub">'
            '<span class="pub-year">%s</span>'
            '<span class="pub-body"><span class="pub-authors">%s</span>%s%s</span>'
            "</li>" % (
                html.escape(e.get("key", ""), quote=True),
                to_html(e.get("year", "")),
                format_authors(e.get("author", "")),
                ". " + ". ".join(bits) + ".",
                star,
            ))
    return ('<section class="rubric"><h2>%s</h2><ol class="pubs">%s</ol></section>'
            % (html.escape(heading), "".join(rows)))


# ----------------------------------------------------------------- page ----


def parse_header(path):
    text = strip_comments(io.open(path, encoding="utf-8").read())
    info = {}
    m = re.search(r"\\LARGE\\bfseries\\sffamily\s+([^}\n]+)", text)
    info["name"] = m.group(1).strip() if m else "Curriculum Vitae"
    m = re.search(r"\\href\{(https://github\.com/[^}]+)\}\{\\texttt\{([^}]+)\}\}", text)
    if m:
        info["github"] = (m.group(1), m.group(2))
    m = re.search(r"mailto:([^}]+)\}", text)
    if m:
        info["email"] = m.group(1)
    m = re.search(r"\\makerubrichead\{", text)
    return info


CSS = """
:root{
  --bg:#ffffff; --fg:#1a1a1a; --muted:#6b6b6b; --rule:#e3e3e3;
  --accent:#1f4e79; --chip:#f4f6f8; --link:#1f4e79;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#15171a; --fg:#e6e6e6; --muted:#9aa0a6; --rule:#2c3035;
    --accent:#8ab4f8; --chip:#1e2126; --link:#8ab4f8;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
       "Helvetica Neue","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
}
.wrap{max-width:56rem; margin:0 auto; padding:2.5rem 1.25rem 4rem}
a{color:var(--link)}
a:hover{text-decoration:none}

header.cv{border-bottom:2px solid var(--accent); padding-bottom:1rem; margin-bottom:2rem}
header.cv h1{margin:0 0 .4rem; font-size:2.1rem; letter-spacing:-.01em}
.contact{display:flex; flex-wrap:wrap; gap:.4rem 1.1rem; color:var(--muted); font-size:.95rem}
.contact a{text-decoration:none}
.actions{display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1rem}
.actions a{
  display:inline-block; padding:.4rem .85rem; border:1px solid var(--rule);
  border-radius:999px; background:var(--chip); text-decoration:none; font-size:.9rem;
}
.actions a[aria-current="page"]{border-color:var(--accent); color:var(--accent); font-weight:600}

.rubric{margin:0 0 2.25rem}
.rubric h2{
  font-size:1.02rem; text-transform:uppercase; letter-spacing:.09em;
  color:var(--accent); margin:0 0 .9rem; padding-bottom:.35rem;
  border-bottom:1px solid var(--rule);
}
.rubric h3{font-size:.95rem; margin:1.4rem 0 .7rem; color:var(--muted)}

.entry{display:grid; grid-template-columns:11rem 1fr; gap:0 1.5rem; margin-bottom:1.15rem}
.entry-key{color:var(--muted); font-size:.9rem; padding-top:.15rem}
.entry-body>p{margin:0 0 .45rem}
.entry-body>p:last-child{margin-bottom:0}
.entry-body ul{margin:.3rem 0 .5rem; padding-left:1.15rem}
.entry-body li{margin:.15rem 0}

.pubs{list-style:none; margin:0; padding:0; counter-reset:pub}
.pub{display:grid; grid-template-columns:11rem 1fr; gap:0 1.5rem; margin-bottom:.9rem}
.pub-year{color:var(--muted); font-size:.9rem}
.pub-venue{font-style:italic; color:var(--muted)}
.pub-flag{color:var(--accent)}
.cites{font-size:.85rem}
.cite{text-decoration:none}
code{background:var(--chip); padding:.05em .3em; border-radius:3px; font-size:.9em}

footer.cv{margin-top:3rem; padding-top:1rem; border-top:1px solid var(--rule);
          color:var(--muted); font-size:.85rem}
footer.cv a{color:var(--muted)}

@media (max-width:640px){
  .wrap{padding:1.75rem 1rem 3rem}
  header.cv h1{font-size:1.65rem}
  .entry,.pub{grid-template-columns:1fr; gap:.15rem}
  .entry-key,.pub-year{font-weight:600; color:var(--accent); font-size:.85rem}
}
@media print{
  .actions{display:none}
  body{background:#fff; color:#000}
  .wrap{max-width:none; padding:0}
}
"""

PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="wrap">
<header class="cv">
  <h1>{name}</h1>
  <div class="contact">{contact}</div>
  <nav class="actions">{actions}</nav>
</header>
{sections}
<footer class="cv">
{footer}
</footer>
</div>
</body>
</html>
"""


def build_page(src_dir, lang_cfg, out_dir, other):
    cites = []
    before, after = [], []

    # Sections before the publication list, then the ones after it, matching
    # the ordering of the PDF.
    for fname, bucket in (("education", before), ("employment", before),
                          ("skills", after), ("misc", after)):
        path = os.path.join(src_dir, fname + ".tex")
        if not os.path.exists(path):
            continue
        for sec in parse_rubrics(path, cites):
            bucket.append(render_section(sec))

    bib = os.path.join(src_dir, "own-bib.bib")
    pubs_html, numbering = "", {}
    if os.path.exists(bib):
        entries = order_publications(parse_bib(bib))
        numbering = {e["key"]: n for n, e in enumerate(entries, 1)}
        pubs_html = render_publications(entries, lang_cfg["pubs"], set(cites))

    sections_html = before + ([pubs_html] if pubs_html else []) + after
    page_body = "\n".join(sections_html)

    # \cite{key} was rendered with the raw key as its text; swap in the number
    # the entry ends up with in the list, so the page reads like the PDF.
    def renumber(m):
        key = m.group("key")
        return '%s%s</a>' % (m.group("head"), numbering.get(key, key))

    page_body = re.sub(
        r'(?P<head><a class="cite" href="#pub-(?P<key>[^"]+)">)[^<]*</a>',
        renumber, page_body)

    info = parse_header(os.path.join(src_dir, "cv-llt.tex"))
    contact = []
    if "github" in info:
        contact.append('<a href="%s">github.com/%s</a>'
                       % (html.escape(info["github"][0], quote=True),
                          html.escape(info["github"][1])))
    if "email" in info:
        contact.append('<a href="mailto:%s">%s</a>'
                       % (html.escape(info["email"], quote=True),
                          html.escape(info["email"])))

    actions = [
        '<a href="%s" aria-current="page">%s</a>' % (lang_cfg["self"], lang_cfg["label"]),
        '<a href="%s">%s</a>' % (other["self"], other["label"]),
        '<a href="%s">%s</a>' % (lang_cfg["pdf"], lang_cfg["pdf_label"]),
    ]

    page = PAGE.format(
        lang=lang_cfg["html_lang"],
        title=html.escape("%s \u2014 %s" % (info["name"], lang_cfg["cv_word"])),
        desc=html.escape(lang_cfg["desc"] % info["name"]),
        name=html.escape(info["name"]),
        contact=" ".join(contact),
        actions="".join(actions),
        sections=page_body,
        footer=lang_cfg["footer"],
    )
    with io.open(os.path.join(out_dir, lang_cfg["self"]), "w", encoding="utf-8") as fh:
        fh.write(page)
    return lang_cfg["self"]


def render_section(sec):
    out = ['<section class="rubric"><h2>%s</h2>' % sec["title"]]
    for g in sec["groups"]:
        if g["sub"]:
            out.append("<h3>%s</h3>" % g["sub"])
        for e in g["entries"]:
            out.append('<div class="entry"><div class="entry-key">%s</div>'
                       '<div class="entry-body">%s</div></div>'
                       % (e["key"], e["body"]))
    out.append("</section>")
    return "\n".join(out)


LANGS = {
    "en": {
        "dir": "English", "self": "index.html", "label": "English",
        "html_lang": "en", "cv_word": "CV",
        "pdf": "cv-en.pdf", "pdf_label": "PDF \u2193",
        "pubs": "Research Publications",
        "desc": "Curriculum vitae of %s.",
        "footer": 'Generated from the LaTeX sources at '
                  '<a href="https://github.com/kinling9/cv">github.com/kinling9/cv</a>. '
                  'Layout based on LianTze Lim\'s '
                  '<a href="https://www.overleaf.com/latex/templates/'
                  'a-customised-curve-cv/mvmbhkwsnmwv">A Customised CurVe CV</a> '
                  '(CC BY 4.0).',
    },
    "zh": {
        "dir": "Chinese", "self": "zh.html", "label": "\u4e2d\u6587",
        "html_lang": "zh-CN", "cv_word": "\u7b80\u5386",
        "pdf": "cv-zh.pdf", "pdf_label": "PDF \u2193",
        "pubs": "\u5b66\u672f\u8bba\u6587",
        "desc": "%s \u7684\u4e2a\u4eba\u7b80\u5386\u3002",
        "footer": '\u7531 LaTeX \u6e90\u6587\u4ef6\u751f\u6210\uff1a'
                  '<a href="https://github.com/kinling9/cv">github.com/kinling9/cv</a>\u3002'
                  '\u6a21\u677f\u57fa\u4e8e LianTze Lim \u7684 '
                  '<a href="https://www.overleaf.com/latex/templates/'
                  'a-customised-curve-cv/mvmbhkwsnmwv">A Customised CurVe CV</a>'
                  '\uff08CC BY 4.0\uff09\u3002',
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=".", help="tree holding English/ and Chinese/")
    ap.add_argument("--out", default="docs", help="output directory")
    args = ap.parse_args()

    if not os.path.isdir(args.out):
        os.makedirs(args.out)

    for code, cfg in LANGS.items():
        src = os.path.join(args.source, cfg["dir"])
        if not os.path.isdir(src):
            print("  skipping %s: %s not found" % (code, src))
            continue
        other = LANGS["zh" if code == "en" else "en"]
        name = build_page(src, cfg, args.out, other)
        print("  wrote %s" % os.path.join(args.out, name))

    with io.open(os.path.join(args.out, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS.lstrip())
    print("  wrote %s" % os.path.join(args.out, "style.css"))

    # Jekyll would otherwise try to process the directory on GitHub Pages.
    open(os.path.join(args.out, ".nojekyll"), "w").close()


if __name__ == "__main__":
    main()
