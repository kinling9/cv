# Build the CV in two flavours.
#
#   make           same as `make private`
#   make private   Full CV, including the phone number, WeChat ID and photo
#                  taken from the gitignored personal.tex / photo.jpg. These
#                  are the PDFs to send with an actual application. Output
#                  stays in English/ and Chinese/ and is gitignored.
#   make public    Sanitised CV for publishing. Built from git-tracked files
#                  only, so personal.tex and photo.jpg are structurally absent
#                  rather than deleted by hand. Output lands in public/ and is
#                  committed, so the PDFs are readable straight from GitHub.
#   make clean     Remove LaTeX build artefacts.
#   make distclean clean, and drop public/ as well.

BUILDDIR  := .build
PUBLICDIR := public

LATEXMK := latexmk -interaction=nonstopmode -halt-on-error

.PHONY: all private public verify clean distclean

all: private

# ------------------------------------------------------------------ private --

private:
	@echo "==> English (private)"
	cd English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese (private)"
	cd Chinese && $(LATEXMK) -xelatex cv-llt.tex

# ------------------------------------------------------------------- public --
#
# The safety of this target rests on one thing: it builds from `git ls-files`,
# which lists tracked files only. personal.tex and photo.jpg are gitignored, so
# they cannot reach $(BUILDDIR) -- there is no step here that could be forgotten
# or reordered into leaking them. cv-llt.tex then falls back to
# personal-example.tex and omits the contact rows.

public:
	@rm -rf $(BUILDDIR)
	@mkdir -p $(BUILDDIR) $(PUBLICDIR)
	@git ls-files -z | tar --null -T - -cf - | tar -xf - -C $(BUILDDIR)
	@for f in $(BUILDDIR)/*/personal.tex $(BUILDDIR)/*/photo.jpg; do \
		test ! -e "$$f" || { echo "ERROR: $$f reached the public build"; exit 1; }; \
	done
	@echo "==> English (public)"
	cd $(BUILDDIR)/English && $(LATEXMK) -pdf cv-llt.tex
	@echo "==> Chinese (public)"
	cd $(BUILDDIR)/Chinese && $(LATEXMK) -xelatex cv-llt.tex
	cp $(BUILDDIR)/English/cv-llt.pdf $(PUBLICDIR)/cv-en.pdf
	cp $(BUILDDIR)/Chinese/cv-llt.pdf $(PUBLICDIR)/cv-zh.pdf
	@rm -rf $(BUILDDIR)
	@$(MAKE) --no-print-directory verify

# Belt and braces: read the real values out of personal.tex and confirm they
# are absent from the PDFs that are about to be committed.
verify:
	@echo "==> verifying public PDFs"
	@sh tools/check-public.sh $(PUBLICDIR)/cv-en.pdf $(PUBLICDIR)/cv-zh.pdf

# -------------------------------------------------------------------- clean --

clean:
	-cd English && $(LATEXMK) -C cv-llt.tex
	-cd Chinese && $(LATEXMK) -C cv-llt.tex
	rm -rf $(BUILDDIR)

distclean: clean
	rm -rf $(PUBLICDIR)
