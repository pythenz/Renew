#!/usr/bin/env bash
# Auto-commit all changes in the repository, then push.
# Usage: ./scripts/auto_commit.sh "optional commit message"
# If no commit message is provided, a timestamped default will be used.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$REPO_ROOT"

# Ensure were
