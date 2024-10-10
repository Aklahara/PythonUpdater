#!/bin/bash
CURRENT_WORKING_DIRECTORY=$CWD

LINK=$1
VERSION=$2
GIL_JIT=$3

wget -O ~/"Python-$VERSION.tgz" "$LINK"
cd ~ || exit 1
tar zxvf ~/"Python-$VERSION.tgz"
cd ~/"Python-$VERSION" || exit 1
if [[ $GIL_JIT ]] && [[ "$VERSION" = "3.13"* ]] ; then
    ./configure --enable-optimizations --with-lto --disable-gil --enable-experimental-jit
else
    ./configure --enable-optimizations --with-lto
fi
make -j 16
sudo make -j 16 altinstall
cd "$CURRENT_WORKING_DIRECTORY" || exit 1
