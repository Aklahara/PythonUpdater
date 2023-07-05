#!/bin/bash

# Build dependencies
sudo apt-get update
sudo apt-get build-dep -y python3 || exit
sudo apt-get upgrade -y pkg-config build-essential gdb lcov pkg-config \
        libbz2-dev libffi-dev libgdbm-dev libgdbm-compat-dev liblzma-dev \
        libncurses5-dev libreadline6-dev libsqlite3-dev libssl-dev \
        lzma lzma-dev tk-dev uuid-dev zlib1g-dev

# Fetch the latest and active Python release information
echo "Downloading release information"
RELEASES_INFO=$(wget -O - https://www.python.org/downloads/)
echo
echo "Downloading pre-release information"
PRE_RELEASES_INFO=$(wget -O - https://www.python.org/download/pre-releases/)
echo

# Extract the active release version numbers (-v "2.7" because it is commented)
ACTIVE_RELEASE_VERSIONS=$(echo "$RELEASES_INFO" | grep -oP '>\K\d\.\d+(?=<)' | grep -v "2.7")
TO_BE_UPDATED=()

for CHECK_VERSION in $ACTIVE_RELEASE_VERSIONS; do
    PRE_RELEASE=0
    # Extract the latest release version number
    LATEST_RELEASE_VERSION=$(echo "$RELEASES_INFO" | grep -oP "Python \K$CHECK_VERSION.\d+")
    # Get the current Python version
    CURRENT_PYTHON_VERSION=$(python"$CHECK_VERSION" --version | grep -oP "\d.\d+.\d+(\w\d+)?") || CURRENT_PYTHON_VERSION=None

    if ! [[ "$LATEST_RELEASE_VERSION" ]]; then
        LATEST_RELEASE_VERSION=$(echo "$PRE_RELEASES_INFO" | grep -oP "Python \K\d.\d+.\d\D\d")
        PRE_RELEASE=1
    fi

    LATEST_RELEASE_VERSION=$(echo "$LATEST_RELEASE_VERSION" | sort -Vr | head -n 1)

    if [ "$LATEST_RELEASE_VERSION" != "$CURRENT_PYTHON_VERSION" ]; then
        TO_BE_UPDATED+=("$LATEST_RELEASE_VERSION")
        echo "New release available: $LATEST_RELEASE_VERSION (Your version: $CURRENT_PYTHON_VERSION)"
        if [ "$PRE_RELEASE" == 0 ]; then
            gnome-terminal -- bash -c "./InstallPython.sh https://www.python.org/ftp/python/$LATEST_RELEASE_VERSION/Python-$LATEST_RELEASE_VERSION.tgz $LATEST_RELEASE_VERSION; exec bash"
        else
            gnome-terminal -- bash -c "./InstallPython.sh https://www.python.org/ftp/python/$(echo "$LATEST_RELEASE_VERSION" | grep -oP "\d.\d+.\d+")/Python-$LATEST_RELEASE_VERSION.tgz $LATEST_RELEASE_VERSION; exec bash"
        fi
    else
        echo "$CURRENT_PYTHON_VERSION" is the newest version.
    fi
done
if [[ "${#TO_BE_UPDATED[@]}" -eq 0 ]]; then
    echo
    echo "All Python versions are up to date"
fi
