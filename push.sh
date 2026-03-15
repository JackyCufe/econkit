#!/bin/bash
# 一键推送到 GitHub + ModelScope
set -e
MSG=${1:-"chore: update"}
git add -A
git commit -m "$MSG" 2>/dev/null || echo "nothing to commit"
git push origin main
git push modelscope main
echo "✅ 已推送到 GitHub + ModelScope"
