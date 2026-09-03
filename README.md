# CV — Min Wei / 魏民

Curriculum vitae, written in LaTeX and maintained in two languages.

**Read it online:** <https://kinling9.github.io/cv/>
&nbsp;·&nbsp; [English](https://kinling9.github.io/cv/)
&nbsp;·&nbsp; [中文](https://kinling9.github.io/cv/zh.html)

**Download:** [English PDF](docs/cv-en.pdf) &nbsp;·&nbsp; [中文版 PDF](docs/cv-zh.pdf)

## Layout

- [`English/`](English/) — English version, builds with **pdfLaTeX**
- [`Chinese/`](Chinese/) — 中文版, builds with **XeLaTeX** (uses `ctex`)

Each directory has the same shape: `cv-llt.tex` is the master file, and every
section — `education`, `employment`, `publications`, `skills`, `misc` — lives in
its own `.tex` file. The publication list is generated from `own-bib.bib`
through `biblatex` + `biber`.

## Building

Needs GNU Make and a TeX distribution providing `curve`, `biblatex`, `biber`,
`fontawesome5` and `simpleicons`; TeX Live 2022 or newer covers all of them.

```sh
make        # build both PDFs
make docs   # rebuild everything published under docs/
make site   # rebuild just the HTML, skipping the LaTeX runs
make clean
```

`docs/` is what GitHub Pages serves — the two PDFs plus the web version.
Re-run `make docs` and commit `docs/` whenever the CV changes, otherwise the
published copies drift from the sources.

### The web version

`tools/build-site.py` generates `docs/index.html` and `docs/zh.html` from the
same section files and `own-bib.bib` that produce the PDFs. No CV content is
duplicated in HTML, so the site cannot fall out of step with the PDF — editing
`employment.tex` updates both.

The generator handles the small set of macros these files actually use
(`rubric`, `subrubric`, `entry*`, `textbf`, `emph`, `itemize`, `cite`, …) and
formats the bibliography itself. `make4ht` was tried first and rejected: it
corrupted ligatures, emitted no headings, and dropped the publication list.

## Credits

This CV is built on **[A Customised CurVe CV][template]** by **LianTze Lim**,
published on Overleaf under [CC BY 4.0][ccby]. The overall layout and
`settings.sty` are used essentially as published; the header is the main local
change.

That template in turn builds on the **[CurVe][curve]** LaTeX class by
**Didier Verna**, distributed under the [LPPL][lppl].

The CV content itself — education, employment, publications and awards — is my
own work.

[template]: https://www.overleaf.com/latex/templates/a-customised-curve-cv/mvmbhkwsnmwv
[ccby]:     https://creativecommons.org/licenses/by/4.0/
[curve]:    https://ctan.org/pkg/curve
[lppl]:     https://www.latex-project.org/lppl.txt
