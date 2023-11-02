#!/bin/sh

# Define colors for log
_info()    { echo "\033[1m[INFO]\033[0m $1" ; }
_ok()      { echo "\033[32m[OK]\033[0m $1" ; }
_error()   { echo "\033[31m[ERROR]\033[0m $1" ; }
_logo()   { echo "\033[1m $1\033[0m" ; }

# Header
echo ""
echo ""
_logo "  █▌     ▀▀▀▀▀▀ ║█    ╫█ ▐█µ   ▐█  ▄██▀▀██▌  ██     ▀└ █▌   ╒█▌ █µ      █▌  "
_logo " ▐█             ███▌  ██ ████  ██ ██     ╟█ ▐█     ▐█ ║█    ╫█ ║██▌  ╓███   "
_logo " ██     ▀▀▀▀▀▀ ╒█Γ└██▓█  █▌ ██▓█▌▐█      ██ ██     ██ ██       ██ ███▀ ██   "
_logo "┌▀             ██   ▀██ ║█   ╙██ └██   ╓██  █▌    ╒█▌ ██   ██ ╒█▌  ╙  ╒█Γ   "
_logo " -▀▀▀▀ ╝▀▀▀▀▀▀ ▀▀     ▀ ▀▀     ▀   ▀▀█▀▀   ╘▀▀▀▀▀ ╝▀   ▀██▀   ╝▀      ╝▀    "
_logo " "
_logo "     S  W  I  F  T  G  U  A  R  D    B  U  I  L  D     S  C  R  I  P  T     "
_logo " -------------------------------------------------------------------------  "
echo ""
echo ""

# Start.
_info "This script will build a dmg file for swiftGuard."

# Check if homebrew is installed and install it if not.
_info "Checking if homebrew is installed ..."
if test ! "$(which brew)"; then
    _info "Installing homebrew now ..."
    /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    brew update
else
    _ok "Homebrew is installed."
    brew update
fi

# Check if create-dmg is installed and install it if not.
_info "Checking if create-dmg is installed ..."
if test ! "$(which create-dmg)"; then
    _info "Installing create-dmg now ..."
    brew install create-dmg
else
    brew upgrade create-dmg
    _ok "create-dmg is installed."
fi

# Checking if swiftGuard.app is in /dist folder.
_info "Checking if swiftGuard.app is in /dist folder ..."

if [ ! -d "dist/swiftGuard.app" ]; then
  _error "swiftGuard.app not found in /dist folder. Please build the app first (using build-app.sh)."
  exit 1
fi

# Create a folder dmg to copy the finished .dmg in it.
_info "Creating needed folders ..."
mkdir -p dmg/

# Create a temp folder to copy the .app file to.
mkdir -p dist/dmg-temp

# Copy the .app bundle to the dmg-temp folder.
cp -R "dist/swiftGuard.app" dist/dmg-temp

# Delete the content of /dmg folder (to remove old dmgs).
_info "Making sure there is no content in /dmg folder."
rm -R dmg/*

# Create the DMG. (optional:   --eula "LICENSE" \)
_info ".dmg building started. This can take a while ..."
if create-dmg \
  --volname "swiftGuard" \
  --volicon "img/dmg-icon/dmg-icon-macos.icns" \
  --background "img/dmg-bg/dmg-bg-macos@2x.png" \
  --window-pos 200 120 \
  --window-size 660 400 \
  --icon-size 160 \
  --icon "swiftGuard.app" 180 170 \
  --hide-extension "swiftGuard.app" \
  --app-drop-link 480 170 \
  "dmg/swiftGuard.dmg" \
  "dist/dmg-temp/"
then
  _ok "create-dmg successfully created .dmg file without errors."
else
  _error "DMG BUILD FAILED!"
  rm -R dist/dmg-temp/*
  rm -r dist/dmg-temp
  exit 1
fi

# Empty and deleting the dmg-temp folder.
_info "Deleting temp files and folders ..."
rm -R dist/dmg-temp/*
rm -r dist/dmg-temp

# Generate sha256 hash file of installer and check it.
_info "Generating sha256 checksum file of dmg..."
cd dmg || exit
sha256sum "swiftGuard.dmg" > SHA256SUM
_info "Validate sha256 checksum ..."
sha256sum -c SHA256SUM

# Finished: Open finder with the dmg folder.
_ok "create-dmg successfully build dmg file."
_ok "Find swiftGuard.dmg in /dmg folder."
_ok "SCRIPT FINISHED!"
