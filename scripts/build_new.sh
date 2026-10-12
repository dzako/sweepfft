#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Build build/bench_dft_new (safe while sweeps use build/bench_dft).
set -euo pipefail
cd "$(dirname "$0")/.."
TP=third_party; MKL_LIB=$TP/mkl/mkl-2024.2.2.data/data/lib; MKL_INC=$TP/mkl/mkl_include-2024.2.2.data/data/include
CF="-O3 -march=native -mtune=native -Wall -Wno-unused-function -I$TP/fftw/include -I$MKL_INC"
mkdir -p build/new
gcc $CF -c csrc/bench/impl_ours.c -o build/new/impl_ours.o
gcc $CF -c csrc/bench/bench_dft.c -o build/new/bench_dft.o
g++ -o build/bench_dft_new build/new/bench_dft.o build/new/impl_ours.o build/impl_ext.o build/impl_ducc.o build/ducc_threading.o build/ducc_string_utils.o \
  $TP/fftw/lib/libfftw3.a -L$MKL_LIB -l:libmkl_intel_lp64.so.2 -l:libmkl_sequential.so.2 -l:libmkl_core.so.2 -Wl,-rpath,$(realpath $MKL_LIB) -lquadmath -lm -lpthread
