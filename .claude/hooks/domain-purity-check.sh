#!/bin/bash
# PostToolUse hook: Domain Purity Check
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to src/**/*.py
# Severity: WARN
# Rule: engine.py must never import from ui.py; publisher.py must not import from cli.py

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

BASENAME=$(basename "$FILE")

# Check engine.py: must not import ui
if [[ "$BASENAME" == "engine.py" ]]; then
  if grep -nE '^\s*(import|from)\s+jre_vidget\.ui|^\s*from\s+\.\s*import.*ui' "$FILE" 2>/dev/null; then
    echo "DOMAIN PURITY: engine.py imports from ui.py — this violates the architecture."
    echo "  → UI concerns belong in cli.py only. See GUARDRAILS.md SIGN #1."
    echo "  → File: $FILE"
  fi
fi

# Check publisher.py: must not import from cli or ui
if [[ "$BASENAME" == "publisher.py" ]]; then
  if grep -nE '^\s*(import|from)\s+jre_vidget\.(cli|ui)|^\s*from\s+\.\s*import.*(cli|ui)' "$FILE" 2>/dev/null; then
    echo "DOMAIN PURITY: publisher.py imports from cli.py or ui.py — pure upload logic only."
    echo "  → publisher.py mirrors engine.py: no CLI, no Rich."
    echo "  → File: $FILE"
  fi
fi

# Check auth.py: must not import from cli or ui
if [[ "$BASENAME" == "auth.py" ]]; then
  if grep -nE '^\s*(import|from)\s+jre_vidget\.(cli|ui)|^\s*from\s+\.\s*import.*(cli|ui)' "$FILE" 2>/dev/null; then
    echo "DOMAIN PURITY: auth.py imports from cli.py or ui.py — credential logic only."
    echo "  → auth.py must be importable without Rich or Typer."
    echo "  → File: $FILE"
  fi
fi
