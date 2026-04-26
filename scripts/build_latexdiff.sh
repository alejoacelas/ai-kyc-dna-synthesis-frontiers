#!/usr/bin/env bash
# Produce latexdiff files for paper/main.tex and paper/supplementary.tex
# against a baseline git ref (default: main branch, pre-revision).
#
# Usage:
#   scripts/build_latexdiff.sh                  # diff against `main`
#   scripts/build_latexdiff.sh <git-ref>        # diff against any ref/tag/commit
#
# Requires:
#   - latexdiff (ships with TeX Live / MacTeX; `brew install --cask mactex-no-gui`
#     or `tlmgr install latexdiff` if missing)
#   - git
#
# Outputs:
#   paper/main_diff.tex
#   paper/supplementary_diff.tex
#
# Compile the diffs with:
#   cd paper && latexmk -pdf main_diff.tex && latexmk -pdf supplementary_diff.tex

set -euo pipefail

BASELINE="${1:-main}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v latexdiff >/dev/null 2>&1; then
  echo "Error: latexdiff not found on PATH." >&2
  echo "Install with TeX Live/MacTeX, or: tlmgr install latexdiff" >&2
  exit 1
fi

if ! git rev-parse --verify "$BASELINE" >/dev/null 2>&1; then
  echo "Error: git ref '$BASELINE' not found." >&2
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

git show "$BASELINE":paper/main.tex         > "$TMPDIR/main_baseline.tex"
git show "$BASELINE":paper/supplementary.tex > "$TMPDIR/supplementary_baseline.tex"

EXCLUDE='label,ref,cite,citet,citep,citeauthor,citeyear,textbf,textit,emph,url,texttt,includegraphics'

latexdiff \
  --type=UNDERLINE \
  --exclude-safecmd="$EXCLUDE" \
  --math-markup=whole \
  "$TMPDIR/main_baseline.tex" paper/main.tex > paper/main_diff.tex

latexdiff \
  --type=UNDERLINE \
  --exclude-safecmd="$EXCLUDE" \
  --math-markup=whole \
  "$TMPDIR/supplementary_baseline.tex" paper/supplementary.tex > paper/supplementary_diff.tex

echo "Wrote:"
echo "  paper/main_diff.tex"
echo "  paper/supplementary_diff.tex"
echo
echo "Compile with:"
echo "  cd paper && latexmk -pdf main_diff.tex && latexmk -pdf supplementary_diff.tex"
