#!/bin/sh

echo "[INFO] Creating needed and temp folders ..."

# Create a folder dmg to copy the finished .dmg in it.
mkdir -p dmg/

# Create a temp folder to copy the .app file to.
mkdir -p dist/dmg-temp

# Copy the .app bundle to the dmg-temp folder.
cp -R "dist/swiftGuard.app" dist/dmg-temp

echo "[INFO] Deleting content of /dmg folder"

# Delete the content of /dmg folder (to remove old dmgs).
rm -R dmg/*

echo "[INFO] DMG building started ..."

# Create the DMG. (optional:   --eula "LICENSE" \)
create-dmg \
  --volname "swiftGuard" \
  --volicon "img/dmg-icon/dmg-icon-macos@2x.icns" \
  --background "img/dmg-bg/dmg-bg-macos@2x.png" \
  --window-pos 200 120 \
  --window-size 660 400 \
  --icon-size 160 \
  --icon "swiftGuard.app" 180 170 \
  --hide-extension "swiftGuard.app" \
  --app-drop-link 480 170 \
  "dmg/swiftGuard.dmg" \
  "dist/dmg-temp/"

echo "[INFO] Generating sha256 checksum file ..."

# Generate sha256 hash file of installer.
sha256sum "dmg/swiftGuard.dmg" > dmg/checksum.sha256

echo "[INFO] Deleting temp files and folders ..."

# Empty the dmg-temp folder.
rm -R dist/dmg-temp/*

# Delete the dmg-temp folder.
rm -r dist/dmg-temp

echo "[INFO] swiftGuard.dmg and checksum.sha256 created in /dmg folder"

echo "[INFO] FINISHED!"
