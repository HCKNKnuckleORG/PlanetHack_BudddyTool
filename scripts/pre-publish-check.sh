#!/usr/bin/env bash
# Pre-publish validation - run before pushing to GitHub
# Ensures no usage data, secrets, or sensitive paths are staged

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[*] PlanetHack pre-publish check"
FAIL=0

# 1. Verify sensitive dirs are empty or gitignored
for dir in logs sessions reports issues; do
  if [ -d "$dir" ]; then
    count=$(find "$dir" -type f 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
      echo "[!] $dir/ has $count file(s) - ensure these are gitignored and not staged"
      FAIL=1
    fi
  fi
done

# 2. config.yaml must not be staged (contains local overrides)
if git rev-parse --git-dir >/dev/null 2>&1; then
  if git ls-files --error-unmatch config/config.yaml 2>/dev/null; then
    echo "[!] config/config.yaml is staged - should be gitignored"
    FAIL=1
  fi
fi

# 3. No known usage IPs/domains in tracked files
# Catch local paths that could leak username (venv, config samples, etc.)
BAD_PATTERNS="C:\\\\Users\\\\[a-zA-Z]+\\\\|/home/[a-zA-Z0-9_-]+/|Z:\\\\[a-zA-Z]+\\\\"
if git rev-parse --git-dir >/dev/null 2>&1; then
  for f in $(git ls-files 2>/dev/null); do
    if [ -f "$f" ] && grep -qE "$BAD_PATTERNS" "$f" 2>/dev/null; then
      echo "[!] $f may contain local paths (username leak)"
      FAIL=1
    fi
  done
fi

# 4. venv must not be staged
if git rev-parse --git-dir >/dev/null 2>&1; then
  if git ls-files venv 2>/dev/null | head -1 | grep -q .; then
    echo "[!] venv/ is staged - should be gitignored"
    FAIL=1
  fi
fi

if [ $FAIL -eq 0 ]; then
  echo "[+] Pre-publish check passed"
else
  echo "[!] Pre-publish check FAILED - fix issues before pushing"
  exit 1
fi
