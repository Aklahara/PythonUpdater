#!/bin/bash
CURRENT_WORKING_DIRECTORY=$CWD

LINK=$1
VERSION=$2

main_run()
{
wget -O ~/"Python-$VERSION.tgz" "$LINK"
cd ~ || exit
tar zxvf ~/"Python-$VERSION.tgz"
cd ~/"Python-$VERSION" || exit
./configure --enable-optimizations
make -j$(($(nproc) - 2))
sudo make -j$(($(nproc) - 2)) altinstall
cd "$CURRENT_WORKING_DIRECTORY" || exit
}

main_run
# Capture and write the exit status of the script
EXIT_STATUS=$?
echo $EXIT_STATUS > /tmp/install_python_exit_status
exit $EXIT_STATUS
