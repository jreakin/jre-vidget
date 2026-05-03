#!/bin/bash
# PostToolUse hook: Environment Variable Leak Check
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to *.py (not config.py)
# Severity: WARN

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

BASENAME=$(basename "$FILE")
case "$BASENAME" in
  config.py|settings.py|conf.py|env.py)
    exit 0
    ;;
esac

case "$FILE" in
  */tests/*|*/test_*|*_test.py|*/scripts/*|*/conftest.py)
    exit 0
    ;;
esac

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

WARNINGS=""

ENV_ACCESS=$(grep -nE '(os\.environ|os\.getenv|environ\.get|environ\[)' "$FILE" 2>/dev/null | grep -vE '^\s*#' 2>/dev/null)

if [[ -n "$ENV_ACCESS" ]]; then
  COUNT=$(echo "$ENV_ACCESS" | wc -l | tr -d ' ')
  WARNINGS="ENV LEAK: $FILE accesses environment variables directly ($COUNT occurrence(s)).\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$ENV_ACCESS"
  WARNINGS="${WARNINGS}  Centralize env var access in config.py (AppConfig).\n"
fi

DOTENV_ACCESS=$(grep -nE '(load_dotenv|dotenv_values|from\s+dotenv)' "$FILE" 2>/dev/null | grep -vE '^\s*#' 2>/dev/null)

if [[ -n "$DOTENV_ACCESS" ]]; then
  WARNINGS="${WARNINGS}ENV LEAK: $FILE loads dotenv directly — this should only happen in config.py.\n"
  while IFS= read -r line; do
    WARNINGS="${WARNINGS}  $line\n"
  done <<< "$DOTENV_ACCESS"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS"
fi
