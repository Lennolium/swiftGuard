#!/bin/sh

set -e

# Define colors for log
_info()    { echo "\033[1m[INFO]\033[0m $1" ; }
_ok()      { echo "\033[32m[OK]\033[0m $1" ; }
_error()   { echo "\033[31m[ERROR]\033[0m $1" ; }
_warn()   { echo "\033[33m[WARN]\033[0m $1" ; }
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

target_arch="arm64"
if [ "$(uname -m)" != "$target_arch" ]; then
    _warn "You are using $(uname -m) architecture. Run build-app.sh instead."
    exit
fi

# Check if Python3.11 is installed and install it if not.
_info "Checking and installing requirements ..."
if test ! "$(which python3.11)"; then
    _info "Python3.11 is not installed! Installing with Homebrew ..."
    /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    brew update
    brew install python@3.11
else
    _ok "Python3.11 is installed."
fi

# Checking for needed source files.
_info "Checking if src/swiftGuard is present (needed for building)."
if [ ! -d "src/swiftGuard" ]; then
  _error "No src/swiftGuard directory found. Please clone the whole repository first."
  exit 1
fi

# Check if PySide6 is installed and install it if not.
_info "Updating Qt resource file ..."
if test ! "$(which pyside6-rcc)"; then
    _info "PySide6 is not installed! Installing with Homebrew ..."
    brew install pyside
fi

# Updating the Qt resource file (.qrc -> .py).
if pyside6-rcc src/swiftguard/resources/resources.qrc -o src/swiftguard/resources/resources_rc.py
then
    _ok "Resource file successfully compiled."
else
    _error "Could not update resource file!"
    _error "Using old pre-compiled resource file."
fi

# Generate sha256 hash file of installer and check it.
_info "Generating SHA256SUMS file for in-app integrity check ..."
cd src/swiftguard
sha256sum "install/dev.lennolium.swiftguard.plist" > install/SHA256SUMS
sha256sum "install/RELEASE_KEY.asc" >> install/SHA256SUMS
sha256sum "install/swiftguard.ini" >> install/SHA256SUMS
sha256sum "install/swiftguard.service" >> install/SHA256SUMS
sha256sum "resources/ACKNOWLEDGMENTS" >> install/SHA256SUMS
sha256sum "resources/mail-template.txt" >> install/SHA256SUMS
sha256sum "resources/mail-template.html" >> install/SHA256SUMS
sha256sum "resources/resources_rc.py" >> install/SHA256SUMS
sha256sum "utils/__init__.py" >> install/SHA256SUMS
sha256sum "utils/autostart.py" >> install/SHA256SUMS
sha256sum "utils/conf.py" >> install/SHA256SUMS
sha256sum "utils/enc.py" >> install/SHA256SUMS
sha256sum "utils/hash.py" >> install/SHA256SUMS
sha256sum "utils/helpers.py" >> install/SHA256SUMS
sha256sum "utils/listeners.py" >> install/SHA256SUMS
sha256sum "utils/log.py" >> install/SHA256SUMS
sha256sum "utils/notif.py" >> install/SHA256SUMS
sha256sum "utils/upgrade.py" >> install/SHA256SUMS
sha256sum "utils/workers.py" >> install/SHA256SUMS
sha256sum "__init__.py" >> install/SHA256SUMS
sha256sum "__main__.py" >> install/SHA256SUMS
sha256sum "const.py" >> install/SHA256SUMS
if sha256sum -c install/SHA256SUMS
then
    _ok "SHA256SUMS file successfully generated and checked."
else
    _error "SHA256SUMS file check failed!"
    exit 1
fi

_info "Generating PGP detached signature for SHA256SUMS file ..."
release_key=$(grep "GPG_RELEASE_FP = .*" < const.py | sed 's/^.*GPG_RELEASE_FP *= *"\(.*\)"$/\1/')
# echo "$release_key" | gpg --import
if gpg --default-key $release_key --armor --yes --detach-sign install/SHA256SUMS
then
    _ok "PGP signature successfully generated."
else
    _error "PGP signature generation failed!"
    exit 1
fi
if gpg --verify install/SHA256SUMS.asc install/SHA256SUMS
then
    _ok "Verified generated signature."
else
    _error "PGP signature check failed!"
    exit 1
fi

# Back to project root dir.
cd ../..

# Creating dist folder.
mkdir -p dist/

# Delete the content of dist folder (to remove old .app builds).
_info "Deleting old builds in /dist folder (all files get deleted!)."
rm -Rf dist/*

# Creating build folder.
mkdir -p build/

# Delete the content of build folder (to remove old builds).
_info "Deleting old builds in /build folder (all files get deleted!)."
rm -Rf build/*

# Check if venv is created and do so if not.
if ! [ -d "./venv" ] ; then
    _info "Creating virtual environment, so we do not pollute the system."
    python3.11 -m venv venv
else
    _ok "Looks like a virtual environment (venv) is already created."
fi

# Activate venv and install requirements.
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install --upgrade PyInstaller pyinstaller-hooks-contrib

# Build the app.
_info "Building the .app file. This can take a while ..."
if pyinstaller --noconfirm "pyinstaller.spec" -- arm64
then
    _ok "PyInstaller successfully created build."
    _ok "Find swiftGuard.app in /dist folder."
    app_size_raw=$(du -sh dist/swiftGuard)
    app_size=${app_size_raw:1:4}
    _ok "File size: $app_size"
    _ok "SCRIPT FINISHED!"
else
    _error "BUILD FAILED!"
fi

