# Build the CV in two flavours.
#
#   make           same as `make private`
#   make private   Full CV, including the phone number, WeChat ID and photo
#                  taken from the gitignored personal.tex / photo.jpg. These
#                  are the PDFs to send with an actual application. Output
#                  stays in English/ and Chinese/ and is gitignored.
#   make public    Everything published from this repository: both PDFs and the
#                  HTML site, into docs/. Served by GitHub Pages.
#   make site      Just regenerate the HTML, skipping the slow LaTeX runs.
#   make clean     Remove LaTeX build artefacts.
#   make distclean clean, and drop docs/ as well.

BUILDDIR  := .build
PUBLICDIR := docs

LATEXMK := latexmk -interaction=nonstopmode -halt-on-error

.PHONY: all private public site verify export clean distclean

all: private

# ------------------------------------------------------------------ private --

private:
	@echo "==> English (private)"
	cd English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese (private)"
	cd Chinese && $(LATEXMK) -xelatex cv-llt.tex

# ------------------------------------------------------------------- public --
#
# The safety of the public build rests on `export`: it populates $(BUILDDIR)
# from `git ls-files`, which lists tracked files only. personal.tex and
# photo.jpg are gitignored, so they cannot reach the build -- the guarantee is
# structural, not a step someone has to remember. cv-llt.tex then falls back to
# personal-example.tex and omits the contact rows.

export:
	@rm -rf $(BUILDDIR)
	@mkdir -p $(BUILDDIR) $(PUBLICDIR)
	@git ls-files -z | tar --null -T - -cf - | tar -xf - -C $(BUILDDIR)
	@for f in $(BUILDDIR)/*/personal.tex $(BUILDDIR)/*/photo.jpg; do \
		test ! -e "$$f" || { echo "ERROR: $$f reached the public build"; exit 1; }; \
	done

public: export
	@echo "==> English PDF (public)"
	cd $(BUILDDIR)/English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese PDF (public)"
	cd $(BUILDDIR)/Chinese && $(LATEXMK) -xelatex cv-llt.tex
	cp $(BUILDDIR)/English/cv-llt.pdf $(PUBLICDIR)/cv-en.pdf
	cp $(BUILDDIR)/Chinese/cv-llt.pdf $(PUBLICDIR)/cv-zh.pdf
	@echo "==> HTML site"
	python3 tools/build-site.py --source $(BUILDDIR) --out $(PUBLICDIR)
	@rm -rf $(BUILDDIR)
	@$(MAKE) --no-print-directory verify

site: export
	@echo "==> HTML site"
	python3 tools/build-site.py --source $(BUILDDIR) --out $(PUBLICDIR)
	@rm -rf $(BUILDDIR)
	@$(MAKE) --no-print-directory verify

# Belt and braces: read the real values out of personal.tex and confirm they
# are absent from every file about to be committed.
verify:
	@echo "==> verifying published files"
	@sh tools/check-public.sh $(PUBLICDIR)/*

# -------------------------------------------------------------------- clean --

clean:
	-cd English && $(LATEXMK) -C cv-llt.tex
	-cd Chinese && $(LATEXMK) -C cv-llt.tex
	rm -rf $(BUILDDIR)

distclean: clean
	rm -rf $(PUBLICDIR)
