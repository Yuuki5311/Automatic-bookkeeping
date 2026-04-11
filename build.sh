#!/bin/bash
# 构建脚本：确保 manifest 模板每次都同步到 dist 目录
set -e

DIST_TEMPLATES=".buildozer/android/platform/build-arm64-v8a/dists/autobookkeeping/templates"
DIST_MANIFEST=".buildozer/android/platform/build-arm64-v8a/dists/autobookkeeping/src/main/AndroidManifest.xml"

export PATH="/Users/l/Library/Python/3.9/bin:$PATH"

# 如果 dist 已存在，同步模板并清除缓存的 manifest
if [ -d "$DIST_TEMPLATES" ]; then
    echo "Syncing AndroidManifest.tmpl.xml to dist templates..."
    cp AndroidManifest.tmpl.xml "$DIST_TEMPLATES/AndroidManifest.tmpl.xml"
    rm -f "$DIST_MANIFEST"
    echo "Manifest cache cleared."
fi

python3 -m buildozer android debug
