# CV — Min Wei / 魏民

LaTeX sources for my curriculum vitae, maintained in two languages:

- [`English/`](English/) — English version, builds with **pdfLaTeX**
- [`Chinese/`](Chinese/) — 中文版, builds with **XeLaTeX** (uses `ctex`)

Both directories share the same layout: `cv-llt.tex` is the master file and each
section — `education`, `employment`, `publications`, `skills`, `misc` — lives in
its own `.tex` file. The publication list is generated from `own-bib.bib` through
`biblatex` + `biber`.

## Building

Needs a TeX distribution providing `curve`, `biblatex`, `biber`, `fontawesome5`
and `simpleicons`; TeX Live 2022 or newer covers all of them.

```sh
cd English && latexmk -pdf     cv-llt.tex   # -> English/cv-llt.pdf
cd Chinese && latexmk -xelatex cv-llt.tex   # -> Chinese/cv-llt.pdf
```

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
