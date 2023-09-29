#!/bin/sh

# Define colors for log
_info()    { echo "\033[1m[INFO]\033[0m $1" ; }
_ok()      { echo "\033[32m[OK]\033[0m $1" ; }
_error()   { echo "\033[31m[ERROR]\033[0m $1" ; }
_logo()   { echo "\033[1m $1\033[0m" ; }

# Check if architecture is x86_64, because some dependencies are
# throwing errors on arm64.
if [ "$(uname -m)" = arm64 ]; then
    _error "You are using arm64 architecture. This script will switch to x86_64 now."
    _error "After Terminal-Relaunch, you need to run this script again:"
    _logo "--->  ./build-app.sh   <---"
    _info "Press any key to continue ..."
    read -r wait
    exec arch -x86_64 /bin/zsh
fi

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

# Ask if the script should start with building the dmg.
_info "This script will build an .app file of swiftGuard. \nContinue? (y/n)"
read -r response
if  [ "$response" = "y" ]; then
		_ok "Let us begin!"
else
    _error "Script aborted."
    exit;
fi

# Check if Python3 is installed and install it if not.
_info "Checking and installing requirements ..."
if test ! "$(which python3)"; then
    _info "Python3 is not installed! Installing with Homebrew ..."
    /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    brew update
    brew install python3
else
    _ok "Python3 is installed."
fi

# Check if architecture is right
_info "Checking if architecture is right (using uname)
If you are using arm64 architecture, this script will switch to x86_64 now."
if [ `uname -m` = arm64 ]; then
    _error "You are using arm64 architecture. This script will switch to x86_64 now."
    _error "After Terminal-Relaunch, you need to run this script again:\n./build-app.sh"
    _info "Press any key to continue ..."
    read -r wait
    exec arch -x86_64 /bin/zsh
fi

# Checking for needed source files.
_info "Checking if src/swiftGuard is present (needed for building)."
if [ ! -d "src/swiftGuard" ]; then
  _error "No src/swiftGuard directory found. Please clone the whole repository first."
  exit 1
fi

# Creating dist folder.
mkdir -p dist/

# Delete the content of dist folder (to remove old .app builds).
_info "Deleting old builds in /dist folder (all files get deleted!)."
rm -R dist/*

# Creating build folder.
mkdir -p build/

# Delete the content of build folder (to remove old builds).
_info "Deleting old builds in /build folder (all files get deleted!)."
rm -R build/*

# Check if venv is created and do so if not.
if ! [ -d "./venv" ] ; then
    _info "Creating virtual environment, so we do not pollute your system."
    python3 -m venv venv
else
    _ok "Looks like a virtual environment (venv) is already created."
fi

# Activate venv and install requirements.
source venv/bin/activate
pip install -r requirements.txt
pip install --upgrade PyInstaller pyinstaller-hooks-contrib

# Build the app.
_info "Building the .app file. This can take a while ..."
if pyinstaller "pyinstaller.spec"
then
    _ok "Pyinstaller successfully created build."
else
    _error "Build failed!"
    exit 1
fi

# Finished: Open finder with the dmg folder.
_ok "swiftGuard.app was successfully created!"
_ok "SCRIPT FINISHED!"
_logo "--> Press any key to open dist folder and exit script...  <--"
read -r exit
cd dist || exit
open .
exit
