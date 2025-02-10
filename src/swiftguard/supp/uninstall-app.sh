#!/bin/sh

set -eu

SWIFTGUARD_APP="$1"
SUDOERS_PATH="$2"

LOG_FILE="/tmp/uninstall-app.log"

# Redirect stdout and stderr to a log file.
exec 1>>"$LOG_FILE" 2>&1


echo "----------------------------------------"
echo "$(date '+%Y-%m-%d %H:%M:%S'): Starting uninstallation of swiftGuard."
echo ""
echo "Variables:"
echo "APP_DIR: $SWIFTGUARD_APP"
echo "SUDOERS_FILE: $SUDOERS_PATH"
echo "LOG_FILE: $LOG_FILE"
echo ""


# If not all arguments are provided, print usage and exit.
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 SWIFTGUARD_APP SUDOERS_PATH"
    echo "----------------------------------------"
    exit 1
fi


# Ensure we are running as root.
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root."
    echo "----------------------------------------"
    exit 1
fi


if [ -f "$SUDOERS_PATH" ]; then
    if rm -f "$SUDOERS_PATH"; then
        echo "Success: Deleted custom sudoers file."
    else
        echo "Error: Failed to delete custom sudoers file."
        echo "----------------------------------------"
        exit 1
    fi
else
    echo "Skipped: Custom sudoers file does not exist."
fi


if ! killall "$(basename "$SWIFTGUARD_APP")"; then
    echo "Error: Failed to send kill command the swiftGuard app."
    echo "----------------------------------------"
    exit 1
else
    echo "Success: Sent kill command to the swiftGuard app."
fi


# Wait and ensure the swiftGuard app is closed.
while pgrep -f "$(basename "$SWIFTGUARD_APP")" >/dev/null; do
    sleep 1
done

if [ $? -eq 0 ]; then
    echo "Success: The swiftGuard app was closed."
else
    echo "Error: Failed to close the swiftGuard app."
    echo "----------------------------------------"
    exit 1
fi


if rm -rf "$SWIFTGUARD_APP"; then
    echo "Success: swiftGuard.app was deleted."
else
    echo "Error: Failed to delete swiftGuard.app."
    echo "----------------------------------------"
    exit 1
fi

(
  sleep 3
  rm -f "$LOG_FILE"
  rm -f -- "$0"
) &
echo "Success: Deleted log file and uninstall script itself."


echo "Success: Uninstalled swiftGuard. Bye ..."
echo "----------------------------------------"
exit 0
