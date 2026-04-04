#!/usr/bin/env bash
# Stage everything except catalog/charm-section-toc-cache.json (safe while the TOC scan is running).
# Usage:
#   ./scripts/commit-without-charm-toc-cache.sh              # stage + status only
#   ./scripts/commit-without-charm-toc-cache.sh "msg"      # stage + commit
set -euo pipefail
cd "$(dirname "$0")/.."
git add -- . ':(exclude)catalog/charm-section-toc-cache.json'
git status --short
if [ -n "${1:-}" ]; then
  git commit -m "$1"
fi
