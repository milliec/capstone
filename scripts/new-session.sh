#!/usr/bin/env bash
# Start a persona session in its OWN git worktree, so two sessions never share one working folder.
# Usage:  scripts/new-session.sh <persona> <new-branch> [base]
#   e.g.  scripts/new-session.sh frontend.eng frontend/calendar-fix
# Creates ../capstone-worktrees/<persona> on a NEW branch cut from <base> (default: main).
# See project-context/2.build/setup.md, "Persona sessions: one worktree each".
set -euo pipefail

persona="${1:-}"; branch="${2:-}"; base="${3:-main}"
if [ -z "$persona" ] || [ -z "$branch" ]; then
  echo "Usage: scripts/new-session.sh <persona> <new-branch> [base]"; exit 1
fi
case "$persona" in *[!a-z0-9.-]*|"") echo "Persona must be lowercase letters, digits, . or - (e.g. frontend.eng)"; exit 1;; esac
if [ "$branch" = "main" ]; then echo "Never work on main: give a new branch name."; exit 1; fi

# The MAIN folder (the first worktree), even if this script is run from inside another worktree.
cd "$(dirname "$0")/.."
common="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
main_dir="$(dirname "$common")"
dest="$(dirname "$main_dir")/capstone-worktrees/$persona"

if [ -e "$dest" ]; then echo "Already exists: $dest (one worktree per persona; remove it first)"; exit 1; fi

mkdir -p "$(dirname "$dest")"
git worktree add -b "$branch" "$dest" "$base"

# A symlink called "reference" is NOT matched by .gitignore's "reference/", so ignore it in the
# shared, uncommitted exclude file (applies to every worktree).
grep -qxF '/reference' "$common/info/exclude" 2>/dev/null || { mkdir -p "$common/info"; echo '/reference' >> "$common/info/exclude"; }

# Git-ignored things a worktree does not get from git:
[ -e "$main_dir/reference" ] && ln -s "$main_dir/reference" "$dest/reference"   # the hook's name scan needs it
[ -f "$main_dir/.env" ] && cp "$main_dir/.env" "$dest/.env"                      # a copy, so each session can differ
# Private docs: link each entry the worktree does not already have (the two tracked files are real files).
if [ -d "$main_dir/docs" ]; then
  mkdir -p "$dest/docs"
  for item in "$main_dir"/docs/*; do
    [ -e "$dest/docs/$(basename "$item")" ] || ln -s "$item" "$dest/docs/$(basename "$item")"
  done
fi

echo
echo "Worktree ready: $dest   (branch: $branch, from $base)"
echo "Next: cd \"$dest\" && make install     # its own .venv; never share one"
echo "Then open your Claude Code session in that folder."
