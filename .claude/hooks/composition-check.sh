#!/bin/bash
# PostToolUse hook — composition threshold guard for web/src/**/*.tsx
# Fires on every Edit/Write to a .tsx file and warns when limits are exceeded.
#
# Thresholds (per AGENTS.md Component Composition Rules):
#   useState hooks  : ≤ 8 per component
#   Lines of code   : ≤ 300 per file

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

# Only fire on .tsx files
[[ "$FILE" == *.tsx ]] || exit 0

WARNINGS=""

LOC=$(wc -l < "$FILE" 2>/dev/null || echo 0)
USESTATE_COUNT=$(grep -c 'useState' "$FILE" 2>/dev/null || echo 0)

if [ "$USESTATE_COUNT" -gt 8 ]; then
  WARNINGS="${WARNINGS}COMPOSITION WARNING: $FILE has $USESTATE_COUNT useState hooks (limit: 8).\n"
  WARNINGS="${WARNINGS}  → Extract state into a custom hook in web/src/hooks/\n"
  WARNINGS="${WARNINGS}  → Check web/src/hooks/README.md for existing hooks before creating new ones.\n"
fi

if [ "$LOC" -gt 300 ]; then
  WARNINGS="${WARNINGS}COMPOSITION WARNING: $FILE is $LOC lines (limit: 300).\n"
  WARNINGS="${WARNINGS}  → Split into smaller sub-components.\n"
fi

if [ -n "$WARNINGS" ]; then
  echo -e "$WARNINGS"
fi
