#!/bin/bash
CURRENT_WORKING_DIRECTORY=$CWD

LINK=$1
VERSION=$2
shift 2

PGO=0; LTO=0; NO_GIL=0; JIT=0

for arg in "$@"; do
    case "$arg" in
        --pgo)    PGO=1 ;;
        --lto)    LTO=1 ;;
        --no-gil) NO_GIL=1 ;;
        --jit)    JIT=1 ;;
    esac
done

wget -O ~/"Python-$VERSION.tgz" "$LINK"
cd ~ || exit 1
tar zxvf ~/"Python-$VERSION.tgz"
cd ~/"Python-$VERSION" || exit 1

CONFIGURE_FLAGS=()
[[ $PGO    == 1 ]] && CONFIGURE_FLAGS+=(--enable-optimizations)
[[ $LTO    == 1 ]] && CONFIGURE_FLAGS+=(--with-lto)
[[ $NO_GIL == 1 ]] && CONFIGURE_FLAGS+=(--disable-gil)
[[ $JIT    == 1 ]] && CONFIGURE_FLAGS+=(--enable-experimental-jit)

./configure "${CONFIGURE_FLAGS[@]}"
make -j 16
sudo make -j 16 altinstall
cd "$CURRENT_WORKING_DIRECTORY" || exit 1

