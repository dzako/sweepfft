#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Download and build the baseline libraries into third_party/ (not distributed with this repository):
#   FFTW 3.3.10   built from source, double precision, SIMD codelets for this CPU (AVX2/FMA, AVX-512 if present)
#   Intel MKL     2024.2.2 runtime + headers, unpacked from the official PyPI wheels (sequential DFTI is used)
#   ducc0         pinned commit of github.com/mreineck/ducc (header-mostly C++ FFT, the pocketfft successor)
# Requirements: curl, gcc/g++ (C11/C++17), make, unzip or python3, git.  Takes ~5 min (FFTW build).
#   scripts/setup_third_party.sh            # everything
#   THIRD_PARTY=/path scripts/setup_third_party.sh   # alternative location (then symlink it to third_party)
set -euo pipefail
cd "$(dirname "$0")/.."
TP=${THIRD_PARTY:-$PWD/third_party}
mkdir -p "$TP/src" "$TP/dl"
JOBS=$(nproc)

FFTW_VER=3.3.10
FFTW_SHA=56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467
MKL_VER=2024.2.2
DUCC_COMMIT=c48e4c6060d1f3b515740aca897be734050d892d

# ---- FFTW ----
if [ ! -f "$TP/fftw/lib/libfftw3_omp.a" ]; then   # (libfftw3_omp: threaded baseline for bench_dft_mt)
  echo "== FFTW $FFTW_VER"
  tgz="$TP/src/fftw-$FFTW_VER.tar.gz"
  [ -f "$tgz" ] || curl -fL -o "$tgz" "https://www.fftw.org/fftw-$FFTW_VER.tar.gz"
  echo "$FFTW_SHA  $tgz" | sha256sum -c -
  rm -rf "$TP/src/fftw-$FFTW_VER" && tar -xzf "$tgz" -C "$TP/src"
  simd="--enable-sse2 --enable-avx --enable-avx2 --enable-fma"
  grep -qw avx512f /proc/cpuinfo && simd="$simd --enable-avx512"
  (cd "$TP/src/fftw-$FFTW_VER" && ./configure --prefix="$TP/fftw" $simd --enable-openmp --disable-fortran CFLAGS="-O3 -march=native" > configure.out \
     && make -j"$JOBS" > make.out && make install > install.out)
  echo "   FFTW installed in $TP/fftw ($simd)"
fi

# ---- MKL (wheels are zip files; only the shared libraries and headers are used) ----
if [ ! -d "$TP/mkl/mkl-$MKL_VER.data" ]; then
  echo "== MKL $MKL_VER"
  for pkg in mkl mkl_include; do
    whl="$TP/dl/$pkg-$MKL_VER-py2.py3-none-manylinux1_x86_64.whl"
    if [ ! -f "$whl" ]; then
      url=$(curl -fsSL "https://pypi.org/pypi/${pkg/_/-}/$MKL_VER/json" | python3 -c "
import json, sys
for f in json.load(sys.stdin)['urls']:
    if f['filename'].endswith('manylinux1_x86_64.whl'): print(f['url'])")
      curl -fL -o "$whl" "$url"
    fi
    python3 -m zipfile -e "$whl" "$TP/mkl/"
  done
  echo "   MKL unpacked in $TP/mkl"
fi

# ---- ducc0 ----
if [ ! -d "$TP/src/ducc/src/ducc0" ]; then
  echo "== ducc0 @ ${DUCC_COMMIT:0:12}"
  git clone -q https://github.com/mreineck/ducc.git "$TP/src/ducc"
  git -C "$TP/src/ducc" checkout -q "$DUCC_COMMIT"
fi

if [ "$TP" != "$PWD/third_party" ] && [ ! -e third_party ]; then ln -s "$TP" third_party; fi
echo "third_party ready: $(ls "$TP")"
