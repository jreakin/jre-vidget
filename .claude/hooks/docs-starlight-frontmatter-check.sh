#!/bin/bash
# PostToolUse hook — Starlight docs frontmatter sanity
# Enforces: Starlight pages under docs-site need YAML frontmatter with title.
# Trigger: Edit/Write to docs-site/src/content/docs/**/*.{md,mdx}
# Severity: WARN

read -r INPUT
FILE=$(echo "$INPUT" | jq -r '.file_path // empty')

case "$FILE" in
  *docs-site/src/content/docs/*.md | *docs-site/src/content/docs/*.mdx) ;;
  *)
    exit 0
    ;;
esac

[[ -f "$FILE" ]] || exit 0

if ! head -n 80 "$FILE" | grep -q '^title:'; then
  echo "STARLIGHT DOCS: ${FILE} — add YAML frontmatter with title: (required by Starlight)."
fi

if ! head -n 5 "$FILE" | grep -q '^---'; then
  echo "STARLIGHT DOCS: ${FILE} — Starlight docs usually start with --- frontmatter delimiters."
fi
