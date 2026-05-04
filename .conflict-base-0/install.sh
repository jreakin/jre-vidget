#!/usr/bin/env bash
set -euo pipefail

echo "🎬  Installing vidget..."

# Python check
python3 -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'" \
  || { echo "❌  Python 3.11+ is required."; exit 1; }

# Install package
pip3 install -e ".[dev]" --quiet

# ffmpeg check
if ! command -v ffmpeg &>/dev/null; then
  echo "⚠️  ffmpeg not found. Install with: brew install ffmpeg"
else
  echo "✅  ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
fi

echo ""
echo "✅  vidget installed! Try:"
echo "   vidget --help"
echo "   vidget --version"
echo "   vidget formats https://www.foxnews.com/video/6390070137112"
