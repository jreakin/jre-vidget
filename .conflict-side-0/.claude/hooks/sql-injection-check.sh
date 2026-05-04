#!/bin/bash
# PostToolUse hook: SQL Injection Check
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to src/**/*.py
# Severity: BLOCK
# Note: jre-vidget has no DB today; this fires if one is ever added

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */tests/*|*/test_*|*_test.py|*/conftest.py)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

# Look for f-string or %-format SQL construction — classic injection vector
# Use double quotes to avoid the bash single-quote-can't-escape-itself trap
MATCHES=$(grep -nE "(execute|executemany|raw)\s*\(\s*f[\"']|%\s*\(.*\)\s*[\"'].*SELECT|[\"'].*SELECT.*[\"'].*%.*[\"']" "$FILE" 2>/dev/null)

if [[ -n "$MATCHES" ]]; then
  echo "SQL INJECTION RISK: Possible string-formatted SQL detected in $FILE"
  echo "$MATCHES"
  echo "  Use parameterised queries: cursor.execute('SELECT ... WHERE id = ?', (id,))"
  echo "  Never interpolate user input directly into SQL strings."
  exit 2  # BLOCK -- non-zero exit causes Claude Code to surface this as an error
fi
