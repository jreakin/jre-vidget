#!/bin/bash
# PostToolUse hook: Domain Purity Check
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to src/**/*.py
# Severity: WARN
# Rule: engine.py must never import from ui.py; publisher/auth must not import from cli/ui

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE" ]]; then
  exit 0
fi

BASENAME=$(basename "$FILE")

# Matches both "import jre_vidget.ui" and "from jre_vidget import ui"
# and relative "from . import ui" / "from .ui import ..."
check_import() {
  local module="$1"
  grep -nE "^\s*(import|from)\s+jre_vidget\.${module}|^\s*from\s+jre_vidget\s+import.*\b${module}\b|^\s*from\s+\.\s*import.*\b${module}\b|^\s*from\s+\.${module}\s+import" "$FILE" 2>/dev/null
}

# engine.py must not import ui
if [[ "$BASENAME" == "engine.py" ]]; then
  MATCH=$(check_import "ui")
  if [[ -n "$MATCH" ]]; then
    echo "DOMAIN PURITY: engine.py imports from ui -- this violates the architecture."
    echo "$MATCH"
    echo "  UI concerns belong in cli.py only. See GUARDRAILS.md SIGN #1."
  fi
fi

# publisher.py must not import cli or ui
if [[ "$BASENAME" == "publisher.py" ]]; then
  MATCH_CLI=$(check_import "cli")
  MATCH_UI=$(check_import "ui")
  if [[ -n "$MATCH_CLI" ]]; then
    echo "DOMAIN PURITY: publisher.py imports from cli.py -- pure upload logic only."
    echo "$MATCH_CLI"
  fi
  if [[ -n "$MATCH_UI" ]]; then
    echo "DOMAIN PURITY: publisher.py imports from ui.py -- no Rich in publisher."
    echo "$MATCH_UI"
  fi
fi

# auth.py must not import cli or ui
if [[ "$BASENAME" == "auth.py" ]]; then
  MATCH_CLI=$(check_import "cli")
  MATCH_UI=$(check_import "ui")
  if [[ -n "$MATCH_CLI" ]]; then
    echo "DOMAIN PURITY: auth.py imports from cli.py -- credential logic only."
    echo "$MATCH_CLI"
  fi
  if [[ -n "$MATCH_UI" ]]; then
    echo "DOMAIN PURITY: auth.py imports from ui.py -- credential logic only."
    echo "$MATCH_UI"
  fi
fi
