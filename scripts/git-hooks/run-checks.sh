#!/usr/bin/env bash
# Shared checks for the pre-commit and pre-push hooks (see CLAUDE.md "Checks to run after changing
# committed files"). This repo is PUBLIC, so every check fails closed: if a check cannot run, the
# hook stops rather than letting the commit through.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

fail=0

# 1. Never let real source material or secrets into a commit.
#    (A pre-push run has nothing staged, so this only bites on pre-commit.)
staged="$(git diff --cached --name-only)"
if printf '%s\n' "$staged" | grep -qE '^(reference/|\.env$)'; then
  echo "BLOCKED: reference/ or .env is staged. Unstage it with: git restore --staged <path>"
  fail=1
fi

# 2. Real-name scan (must print nothing). Fails closed if the identifier list is missing.
ids="reference/real-identifiers.txt"
if [ ! -f "$ids" ]; then
  echo "BLOCKED: $ids not found, so the real-name scan cannot run."
  fail=1
else
  hits="$(grep -rniwF --exclude-dir=reference --exclude-dir=.venv --exclude-dir=.git \
    -f <(grep -vE '^(#|$)' "$ids") . 2>/dev/null)"
  if [ -n "$hits" ]; then
    echo "BLOCKED: real-name scan found matches (file:line shown, fix before committing):"
    # Show file and line only, so this output never re-prints the real name itself.
    printf '%s\n' "$hits" | cut -d: -f1,2
    fail=1
  fi
fi

# 3. Framework validator.
if [ ! -x .venv/bin/aamad ]; then
  echo "BLOCKED: .venv/bin/aamad not found, so the framework validator cannot run."
  fail=1
else
  out="$(.venv/bin/aamad validate 2>&1)"
  status=$?
  printf '%s\n' "$out"
  if [ "$status" -ne 0 ]; then
    # TEMPORARY exception (operator decision, block B1): the validator hard-fails on a missing
    # qa.md as soon as 2.build/ has any file, but @qa.eng writes it much later. Ignore ONLY that
    # exact line; every other ERROR still blocks. REMOVE this exception once qa.md exists.
    other_errors="$(printf '%s\n' "$out" | grep '^\[ERROR\]' \
      | grep -v 'project-context/2.build/qa.md: Build artifact missing')"
    if [ -n "$other_errors" ]; then
      echo "BLOCKED: aamad validate reported issues."
      fail=1
    else
      echo "NOTE: ignoring only the known 'qa.md missing' finding (temporary, see run-checks.sh)."
    fi
  fi
fi

exit "$fail"
