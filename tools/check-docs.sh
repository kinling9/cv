#!/bin/sh
# Confirm that nothing from a local personal.tex reached docs/.
#
# `make docs` builds from git-tracked files only, so this should already hold.
# This is the independent check on top of that: it reads whatever values
# personal.tex defines and looks for them in the generated PDFs and HTML.
# Run standalone with:
#
#     sh tools/check-docs.sh docs/*

set -eu

status=0
secrets=$(mktemp)
trap 'rm -f "$secrets" "$secrets".raw' EXIT

# Pull the value out of each \newcommand{\cvsomething}{value}, then undo the
# LaTeX escaping so it matches what actually gets typeset.
for f in */personal.tex; do
    [ -e "$f" ] || continue
    sed -n 's/.*\\newcommand{\\cv[a-z]*}{\(..*\)}.*/\1/p' "$f" \
        | sed 's/\\_/_/g; s/\\&/\&/g; s/\\%/%/g; s/\\#/#/g' \
        >> "$secrets".raw
done
sort -u "$secrets".raw > "$secrets" 2>/dev/null || true

if [ ! -s "$secrets" ]; then
    echo "  no personal.tex found - nothing to check against"
    exit 0
fi

have_pdftotext=yes
command -v pdftotext >/dev/null 2>&1 || have_pdftotext=no

for target in "$@"; do
    [ -e "$target" ] || continue          # unmatched glob, or not built yet

    case "$target" in
        *.pdf)
            if [ "$have_pdftotext" = no ]; then
                echo "  WARNING: pdftotext missing, cannot check $target" >&2
                continue
            fi
            text=$(pdftotext "$target" - 2>/dev/null || true)
            ;;
        *.html|*.htm|*.css|*.txt|*.md|*.json)
            text=$(cat "$target")
            ;;
        *)
            continue                      # nothing meaningful to scan
            ;;
    esac

    leaked=0
    while IFS= read -r secret; do
        [ -n "$secret" ] || continue
        if printf '%s' "$text" | grep -qF -- "$secret"; then
            echo "  LEAK: $target contains '$secret'" >&2
            leaked=1
        fi
    done < "$secrets"

    if [ "$leaked" -eq 0 ]; then
        echo "  ok: $target"
    else
        status=1
    fi
done

if [ "$status" -ne 0 ]; then
    echo "Refusing to publish: the public build is not clean." >&2
fi
exit "$status"
