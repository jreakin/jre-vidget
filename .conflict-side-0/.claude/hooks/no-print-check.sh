#!/bin/bash
# PostToolUse hook: No print() in Production Code
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to src/**/*.py
# Severity: WARN
# Skips: tests/, cli.py (uses console.print legitimately)

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

case "$FILE" in
  */tests/*|*/test_*|*_test.py|*/scripts/*|*/conftest.py|*__main__.py|*/cli.py)
    exit 0
    ;;
esac

case "$FILE" in
  */src/*)
    ;;
  *)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

PRINT_CALLS=$(grep -nE '^\s*print\(' "$FILE" 2>/dev/null | grep -vE '^\s*#' 2>/dev/null)

if [[ -n "$PRINT_CALLS" ]]; then
  COUNT=$(echo "$PRINT_CALLS" | wc -l | tr -d ' ')
  WARNINGS="NO PRINT: $FILE has $COUNT print() call(s) in production code.\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$PRINT_CALLS"
  WARNINGS="${WARNINGS}  Use structlog.get_logger() for engine/config/checks modules.\n"
  WARNINGS="${WARNINGS}  Use console.print() (Rich) only in cli.py and ui.py.\n"
  echo -e "$WARNINGS"
fi
