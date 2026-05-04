#!/bin/bash
# PostToolUse hook: Router Boundary Check
# Enforces: Scalable Python Project Structure Playbook
# Trigger: Edit/Write to src/**/*.py
# Severity: WARN
# Rule: cli.py (the router) must not contain business logic — it delegates to engine/publisher

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

if [[ "$FILE" != *.py ]]; then
  exit 0
fi

BASENAME=$(basename "$FILE")

if [[ "$BASENAME" != "cli.py" ]]; then
  exit 0
fi

WARNINGS=""

# Warn if cli.py imports yt_dlp directly (should go through engine)
if grep -nE '^\s*import yt_dlp|^\s*from yt_dlp' "$FILE" 2>/dev/null | grep -q .; then
  WARNINGS="${WARNINGS}ROUTER BOUNDARY: cli.py imports yt_dlp directly.\n"
  WARNINGS="${WARNINGS}  → Route through engine.py instead.\n"
fi

# Warn if cli.py imports googleapiclient directly (should go through publisher/auth)
if grep -nE '^\s*import googleapiclient|^\s*from googleapiclient' "$FILE" 2>/dev/null | grep -q .; then
  WARNINGS="${WARNINGS}ROUTER BOUNDARY: cli.py imports googleapiclient directly.\n"
  WARNINGS="${WARNINGS}  → Route through publisher.py / auth.py instead.\n"
fi

# Warn on large inline logic blocks (>20 lines in a single command function)
# Heuristic: a @app.command function body that's very long
LONG_CMDS=$(awk '/^@app\.command/{cmd=1; count=0} cmd{count++} count>25{print NR": command function exceeds 25 lines — extract to engine/publisher"; cmd=0; count=0}' "$FILE" 2>/dev/null)
if [[ -n "$LONG_CMDS" ]]; then
  WARNINGS="${WARNINGS}ROUTER BOUNDARY: $FILE has a long command handler.\n"
  WARNINGS="${WARNINGS}  → $LONG_CMDS\n"
  WARNINGS="${WARNINGS}  → cli.py should validate inputs and delegate; logic lives in engine/publisher.\n"
fi

if [[ -n "$WARNINGS" ]]; then
  echo -e "$WARNINGS"
fi
