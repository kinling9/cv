# Build the CV.
#
#   make           Build both PDFs in place. Output stays in English/ and
#                  Chinese/ and is gitignored.
#   make docs      Rebuild everything published under docs/ -- both PDFs and
#                  the HTML site -- from tracked files only.
#   make site      Rebuild just the HTML, skipping the slow LaTeX runs.
#   make check     Check docs/ before committing.
#   make clean     Remove LaTeX build artefacts.
#   make distclean clean, and drop docs/ as well.

BUILDDIR := .build
DOCSDIR  := docs

LATEXMK := latexmk -interaction=nonstopmode -halt-on-error

.PHONY: all docs site check stage clean distclean

all:
	@echo "==> English"
	cd English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese"
	cd Chinese && $(LATEXMK) -xelatex cv-llt.tex

# --------------------------------------------------------------------- docs --
#
# `stage` populates $(BUILDDIR) from `git ls-files`, which lists tracked files
# only. Anything gitignored is therefore absent from the build by construction
# rather than by a step someone has to remember, and cv-llt.tex falls back to
# personal-example.tex for the fields it cannot find.

stage:
	@rm -rf $(BUILDDIR)
	@mkdir -p $(BUILDDIR) $(DOCSDIR)
	@git ls-files -z | tar --null -T - -cf - | tar -xf - -C $(BUILDDIR)
	@for f in $(BUILDDIR)/*/personal.tex $(BUILDDIR)/*/photo.jpg; do \
		test ! -e "$$f" || { echo "ERROR: $$f reached the docs build"; exit 1; }; \
	done

docs: stage
	@echo "==> English PDF"
	cd $(BUILDDIR)/English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese PDF"
	cd $(BUILDDIR)/Chinese && $(LATEXMK) -xelatex cv-llt.tex
	cp $(BUILDDIR)/English/cv-llt.pdf $(DOCSDIR)/cv-en.pdf
	cp $(BUILDDIR)/Chinese/cv-llt.pdf $(DOCSDIR)/cv-zh.pdf
	@echo "==> HTML site"
	python3 tools/build-site.py --source $(BUILDDIR) --out $(DOCSDIR)
	@rm -rf $(BUILDDIR)
	@$(MAKE) --no-print-directory check

site: stage
	@echo "==> HTML site"
	python3 tools/build-site.py --source $(BUILDDIR) --out $(DOCSDIR)
	@rm -rf $(BUILDDIR)
	@$(MAKE) --no-print-directory check

check:
	@echo "==> checking docs/"
	@sh tools/check-docs.sh $(DOCSDIR)/*

# -------------------------------------------------------------------- clean --

clean:
	-cd English && $(LATEXMK) -C cv-llt.tex
	-cd Chinese && $(LATEXMK) -C cv-llt.tex
	rm -rf $(BUILDDIR)

distclean: clean
	rm -rf $(DOCSDIR)
