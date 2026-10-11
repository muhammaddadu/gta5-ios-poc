#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/sh
exec python3 scripts/audit_git.py
HOOK
chmod +x .git/hooks/pre-commit
printf '%s\n' 'Installed staged-file audit hook. This is a guardrail, not a rights determination.'
