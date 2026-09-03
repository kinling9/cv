#!/bin/sh
# Fail if a PDF destined for publication contains any value from personal.tex.
#
# `make public` builds from git-tracked files only, so a leak should already be
# impossible. This is the independent check on top of that: it reads the real
# values straight out of the gitignored personal.tex files and looks for them
# in the generated PDFs. Run standalone with:
#
#     sh tools/check-public.sh public/*.pdf

set -eu

status=0
secrets=$(mktemp)
trap 'rm -f "$secrets" "$secrets".raw' EXIT

# Pull the value out of each \newcommand{\cvsomething}{value}, then undo the
# LaTeX escaping so the string matches what actually gets typeset.
for f in */personal.tex; do
    [ -e "$f" ] || continue
    sed -n 's/.*\\newcommand{\\cv[a-z]*}{\(..*\)}.*/\1/p' "$f" \
        | sed 's/\\_/_/g; s/\\&/\&/g; s/\\%/%/g; s/\\#/#/g' \
        >> "$secrets".raw
done
sort -u "$secrets".raw > "$secrets" 2>/dev/null || true
rm -f "$secrets".raw

if [ ! -s "$secrets" ]; then
    echo "  no personal.tex found - nothing to check against"
    exit 0
fi

if ! command -v pdftotext >/dev/null 2>&1; then
    echo "  WARNING: pdftotext not installed, cannot verify PDFs" >&2
    exit 0
fi

for pdf in "$@"; do
    if [ ! -e "$pdf" ]; then
        echo "  missing: $pdf" >&2
        status=1
        continue
    fi
    text=$(pdftotext "$pdf" - 2>/dev/null || true)
    leaked=0
    while IFS= read -r secret; do
        [ -n "$secret" ] || continue
        if printf '%s' "$text" | grep -qF -- "$secret"; then
            echo "  LEAK: $pdf contains '$secret'" >&2
            leaked=1
        fi
    done < "$secrets"
    if [ "$leaked" -eq 0 ]; then
        echo "  ok: $pdf"
    else
        status=1
    fi
done

if [ "$status" -ne 0 ]; then
    echo "Refusing to publish: the public build is not clean." >&2
fi
exit "$status"
