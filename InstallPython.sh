#!/bin/bash
CURRENT_WORKING_DIRECTORY=$CWD

link=$1
wget -O ~/"Python-$LATEST_RELEASE_VERSION.tgz" "$link"
cd ~ || exit
tar zxvf ~/"Python-$LATEST_RELEASE_VERSION.tgz"
cd ~/"Python-$LATEST_RELEASE_VERSION" || exit
./configure --enable-optimizations
make -j
sudo make -j altinstall
cd "$CURRENT_WORKING_DIRECTORY" || exit
