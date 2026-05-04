#!/usr/bin/env bash
# Deploy vidget-auth worker + set secrets
# Usage: ./deploy.sh
# Requires: wrangler CLI, CLOUDFLARE_API_TOKEN env var (or `wrangler login`)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Installing dependencies..."
npm ci

echo "🚀 Deploying worker..."
npx wrangler deploy

echo ""
echo "✅ Worker deployed."
echo ""
echo "Next: set secrets (run interactively — wrangler will prompt for each value):"
echo ""
echo "  npx wrangler secret put GITHUB_CLIENT_ID"
echo "  npx wrangler secret put GITHUB_CLIENT_SECRET"
echo "  npx wrangler secret put ALLOWED_ORIGIN"
echo ""
echo "ALLOWED_ORIGIN should be your GitHub Pages URL, e.g.:"
echo "  https://YOUR_USERNAME.github.io/jre-vidget"
