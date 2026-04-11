#!/bin/bash
# 构建脚本：确保 manifest 模板每次都同步到 dist 目录，并自动递增版本号
set -e

DIST_TEMPLATES=".buildozer/android/platform/build-arm64-v8a/dists/autobookkeeping/templates"
DIST_MANIFEST=".buildozer/android/platform/build-arm64-v8a/dists/autobookkeeping/src/main/AndroidManifest.xml"
SPEC="buildozer.spec"

export PATH="/Users/l/Library/Python/3.9/bin:$PATH"

# 读取当前版本号并递增 patch 位
CURRENT=$(grep '^version' "$SPEC" | sed 's/version = //')
MAJOR=$(echo "$CURRENT" | cut -d. -f1)
MINOR=$(echo "$CURRENT" | cut -d. -f2)
PATCH=$(echo "$CURRENT" | cut -d. -f3)
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"

echo "Bumping version: $CURRENT -> $NEW_VERSION"
sed -i '' "s/^version = .*/version = $NEW_VERSION/" "$SPEC"

# 如果 dist 已存在，同步模板并清除缓存的 manifest
if [ -d "$DIST_TEMPLATES" ]; then
    echo "Syncing AndroidManifest.tmpl.xml to dist templates..."
    cp AndroidManifest.tmpl.xml "$DIST_TEMPLATES/AndroidManifest.tmpl.xml"
    rm -f "$DIST_MANIFEST"
    echo "Manifest cache cleared."
fi

python3 -m buildozer android debug
echo "APK: bin/autobookkeeping-${NEW_VERSION}-arm64-v8a-debug.apk"
