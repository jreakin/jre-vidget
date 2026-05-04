#!/usr/bin/env bash
# scripts/setup-secrets.sh
#
# Creates the required GitHub Secrets for jre-vidget in your forked repo.
# Secrets are set as "REPLACE_ME — <description>" placeholders so they show
# up in Settings → Secrets → Actions and you know exactly what to fill in.
#
# Requirements:
#   - GitHub CLI installed: https://cli.github.com/
#   - Authenticated:        gh auth login
#
# Usage:
#   bash scripts/setup-secrets.sh
#   bash scripts/setup-secrets.sh --force   # overwrite existing values

set -euo pipefail

FORCE=false
for arg in "$@"; do
  [[ "$arg" == "--force" ]] && FORCE=true
done

# ---------------------------------------------------------------------------
# Detect repo
# ---------------------------------------------------------------------------
if ! command -v gh &>/dev/null; then
  echo "❌  GitHub CLI not found. Install it from https://cli.github.com/"
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "❌  Not logged in to GitHub CLI. Run: gh auth login"
  exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [[ -z "$REPO" ]]; then
  echo "❌  Could not detect repo. Run this script from inside the cloned repo."
  exit 1
fi

echo ""
echo "Setting up secrets for: $REPO"
echo ""

# ---------------------------------------------------------------------------
# Helper: set a placeholder secret if not already set (or if --force)
# ---------------------------------------------------------------------------
set_secret() {
  local name="$1"
  local description="$2"

  local existing
  existing=$(gh secret list --repo "$REPO" --json name -q '.[].name' 2>/dev/null | grep -Fxc "$name" || echo "0")

  if [[ "$existing" -gt 0 && "$FORCE" != "true" ]]; then
    echo "  ✅  $name — already set (use --force to overwrite)"
    return
  fi

  printf "REPLACE_ME — %s" "$description" \
    | gh secret set "$name" --repo "$REPO"
  echo "  📝  $name — placeholder set"
}

# ---------------------------------------------------------------------------
# Required secrets
# ---------------------------------------------------------------------------
echo "Required secrets:"
set_secret "VIDGET_CLIENT_ID" \
  "Google OAuth Client ID. See docs/SETUP.md step 2."

set_secret "VIDGET_CLIENT_SECRET" \
  "Google OAuth Client Secret. See docs/SETUP.md step 2."

set_secret "VIDGET_REFRESH_TOKEN" \
  "YouTube refresh token. Run: vidget auth login  then copy from ~/.vidget/config.json. See docs/SETUP.md step 3."

echo ""
echo "Optional secrets:"
set_secret "VIDGET_REPORT_TOKEN" \
  "Fine-grained GitHub PAT with issues:write on jreakin/jre-vidget. Enables automatic error reporting upstream. See docs/SETUP.md."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
SECRETS_URL="https://github.com/$REPO/settings/secrets/actions"
SETUP_URL="https://github.com/$REPO/blob/main/docs/SETUP.md"

echo ""
echo "✅  Done. Placeholders created."
echo ""
echo "Next steps:"
echo "  1. Open Settings → Secrets → Actions in your browser:"
echo "     $SECRETS_URL"
echo ""
echo "  2. Click each secret and replace 'REPLACE_ME — ...' with the real value."
echo "     Full instructions: $SETUP_URL"
echo ""
echo "  3. Run the Bootstrap workflow again to verify all secrets are configured."
echo ""
