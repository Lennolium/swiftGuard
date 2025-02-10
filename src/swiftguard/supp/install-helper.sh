#!/bin/sh

set -eu

HELPER_BINARY="$1"
HELPER_EXPECTED_HASH="$2"
CURRENT_USER="$3"
SUDOERS_FILE="$4"

SWIFTGUARD_DIR=$(realpath "$(dirname "$0")/../")
LOG_FILE="$SWIFTGUARD_DIR/supp/install-helper.log"
SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: sha256:$HELPER_EXPECTED_HASH $HELPER_BINARY"


# If not all arguments are provided, print usage and exit.
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 HELPER_BINARY HELPER_EXPECTED_HASH CURRENT_USER SUDOERS_FILE"
    exit 1
fi


#HELPER_BINARY="$SWIFTGUARD_DIR/bin/dev.lennolium.swiftguardhelper"
#HELPER_EXPECTED_HASH="db6d2557c3cb97aa353195b911a5f826fe16c72774a936d6151a18cad063802a"
#CURRENT_USER="${SUDO_USER:-${USER:-$(whoami):-ALL}}"
#SUDOERS_FILE="/etc/sudoers.d/dev_lennolium_swiftguardhelper"  # Dots not allowed.
## SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: $HELPER_BINARY"
#SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: sha256:$HELPER_EXPECTED_HASH $HELPER_BINARY"

# TODO: remove later!
HELPER_BINARY="/Applications/swifthelper.app/Contents/Resources/dev.lennolium.swiftguardhelper"
SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: sha256:$HELPER_EXPECTED_HASH $HELPER_BINARY"


# Redirect stdout and stderr to a log file.
exec 1>>"$LOG_FILE" 2>&1

echo "----------------------------------------"
chown "$CURRENT_USER" "$LOG_FILE"
chmod 600 "$LOG_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S'): Starting installation of helper and its wrapper binary."


# Print out all variables for debugging.
echo ""
echo "Variables:"
echo "LOG_FILE: $LOG_FILE"
echo "APP_DIR: $SWIFTGUARD_DIR"
echo "SUDOERS_FILE: $SUDOERS_FILE"
echo "HELPER_BINARY: $HELPER_BINARY"
echo "HELPER_EXPECTED_HASH: $HELPER_EXPECTED_HASH"
echo "CURRENT_USER: $CURRENT_USER"
echo "SUDOERS_LINE: $SUDOERS_LINE"
echo ""


# Validate that the helper binary exists.
if [ ! -f "$HELPER_BINARY" ]; then
    echo "Error: Helper binary not found at $HELPER_BINARY."
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Found helper binary."
fi


# Ensure that CURRENT_USER is not empty or root.
if [ -z "$CURRENT_USER" ] || [ "$CURRENT_USER" = "root" ]; then
    echo "Error: Current user is empty or root."
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Current user is $CURRENT_USER."
fi


# Create the sudoers file.
# This allows the current user to run the helper binary as root without a password.
# So the helper binary can be auto-started at boot time.
echo "$SUDOERS_LINE" > "$SUDOERS_FILE"


# Check if the sudoers file was created successfully and is not empty.
if [ ! -s "$SUDOERS_FILE" ]; then
    echo "Error: Failed to create sudoers file."
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Created sudoers file."
fi


# Test the sudoers file for syntax errors.
if ! visudo -c -f "$SUDOERS_FILE"; then
    echo "Error: Sudoers file contains syntax errors. Removing it."
    rm -f "$SUDOERS_FILE"
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Sudoers file was checked for syntax errors."
fi


# Give the created sudoers file strict permissions.
chmod 440 "$SUDOERS_FILE"


# Validate that the sudoers file has the right permissions.
if [ "$(stat -f %A "$SUDOERS_FILE")" != "440" ]; then
    echo "Error: Sudoers file has wrong permissions. Removing it."
    rm -f "$SUDOERS_FILE"
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Sudoers file has correct permissions."
fi

# Everything was successful.
echo "Success: Helper binary installed successfully."
echo "----------------------------------------"
exit 0

