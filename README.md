# CV — Min Wei / 魏民

LaTeX sources for my curriculum vitae, maintained in two languages:

- [`English/`](English/) — English version, builds with **pdfLaTeX**
- [`Chinese/`](Chinese/) — 中文版, builds with **XeLaTeX** (uses `ctex`)

**Read it online:** <https://kinling9.github.io/cv/> — [English](https://kinling9.github.io/cv/)
· [中文](https://kinling9.github.io/cv/zh.html)
· PDF: [English](docs/cv-en.pdf) · [中文](docs/cv-zh.pdf)

Both directories share the same layout: `cv-llt.tex` is the master file and each
section — `education`, `employment`, `publications`, `skills`, `misc` — lives in
its own `.tex` file. The publication list is generated from `own-bib.bib` through
`biblatex` + `biber`.

## Building

Needs GNU Make and a TeX distribution providing `curve`, `biblatex`, `biber`,
`fontawesome5` and `simpleicons`; TeX Live 2022 or newer covers all of them.

```sh
make          # or `make private` -- the full CV, for actual applications
make public   # everything published: both PDFs and the HTML site, into docs/
make site     # just regenerate the HTML, skipping the slow LaTeX runs
make clean
```

`make private` builds in place, picking up `personal.tex` and `photo.jpg`, and
leaves the PDFs in `English/` and `Chinese/` where git ignores them.

`make public` regenerates everything committed under `docs/`, which is what
GitHub Pages serves. It copies the repository into a scratch tree using
`git ls-files`, which lists *tracked* files only — so the gitignored
`personal.tex` and `photo.jpg` cannot reach the build at all. It then re-reads
the real values out of `personal.tex` and greps the finished PDFs and HTML for
them, refusing to publish if anything shows up. That check runs standalone too:

```sh
sh tools/check-public.sh docs/*
```

Re-run `make public` and commit `docs/` whenever the CV content changes,
otherwise the published PDFs and web pages drift from the sources.

### The web version

`tools/build-site.py` generates `docs/index.html` and `docs/zh.html` straight
from the same `.tex` section files and `own-bib.bib`. Nothing about the CV
content is duplicated in HTML, so the site cannot fall out of step with the
PDF — editing `employment.tex` updates both.

The generator handles the small set of macros these files actually use
(`rubric`, `subrubric`, `entry*`, `textbf`, `emph`, `itemize`, `cite`, …) and
formats the bibliography itself. `make4ht` was tried first and rejected: it
corrupted ligatures (`workflow` became `work\0ow`), emitted no headings, and
dropped the publication list entirely.

## Private contact details

Phone number and WeChat ID are **not** kept in this repository. They are read
from `personal.tex`, which is gitignored. To build with your own details:

```sh
cp English/personal-example.tex English/personal.tex   # then edit
cp Chinese/personal-example.tex Chinese/personal.tex
```

When `personal.tex` is missing the CV still compiles — those header fields are
just left out, with no placeholder text typeset. `photo.jpg` is gitignored and
handled the same way: the photo block is skipped when the file isn't present.

## Credits

This CV is built on **[A Customised CurVe CV][template]** by **LianTze Lim**,
published on Overleaf under [CC BY 4.0][ccby]. The overall layout and
`settings.sty` are used essentially as published; the header and contact fields
are the main local changes.

That template in turn builds on the **[CurVe][curve]** LaTeX class by
**Didier Verna**, distributed under the [LPPL][lppl].

The CV content itself — education, employment, publications and awards — is my
own work.

[template]: https://www.overleaf.com/latex/templates/a-customised-curve-cv/mvmbhkwsnmwv
[ccby]:     https://creativecommons.org/licenses/by/4.0/
[curve]:    https://ctan.org/pkg/curve
[lppl]:     https://www.latex-project.org/lppl.txt
