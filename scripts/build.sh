#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Build the benchmark driver and tests.  Usage: scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TP=third_party
MKL_LIB=$TP/mkl/mkl-2024.2.2.data/data/lib
MKL_INC=$TP/mkl/mkl_include-2024.2.2.data/data/include
CFLAGS="-O3 -march=native -mtune=native -Wall -Wno-unused-function -Wno-unknown-pragmas -I$TP/fftw/include -I$MKL_INC"
mkdir -p build
python3 scripts/gen_codelets.py csrc/dft/codelets_gen.h
[ build/impl_ducc.o -nt csrc/bench/impl_ducc.cpp ] && [ build/impl_ducc.o -nt csrc/bench/impl.h ] || g++ -std=c++17 -O3 -march=native -I$TP/src/ducc/src -Icsrc/bench -c csrc/bench/impl_ducc.cpp -o build/impl_ducc.o
for f in threading string_utils; do
  [ build/ducc_$f.o -nt $TP/src/ducc/src/ducc0/infra/$f.cc ] || g++ -std=c++17 -O3 -march=native -I$TP/src/ducc/src -c $TP/src/ducc/src/ducc0/infra/$f.cc -o build/ducc_$f.o
done
gcc $CFLAGS -c csrc/bench/impl_ext.c -o build/impl_ext.o
gcc $CFLAGS -c csrc/bench/impl_ours.c -o build/impl_ours.o
gcc $CFLAGS -c csrc/bench/bench_dft.c -o build/bench_dft.o
g++ -o build/bench_dft build/bench_dft.o build/impl_ours.o build/impl_ext.o build/impl_ducc.o build/ducc_threading.o build/ducc_string_utils.o \
    $TP/fftw/lib/libfftw3.a -L$MKL_LIB -l:libmkl_intel_lp64.so.2 -l:libmkl_sequential.so.2 -l:libmkl_core.so.2 \
    -Wl,-rpath,$(realpath $MKL_LIB) -lquadmath -lm -lpthread
gcc $CFLAGS -o build/test_stockham csrc/tests/test_stockham.c -lquadmath -lm
echo "build ok"
# protocol-sensitivity suite (scripts/fairness.py): the same driver with SweepFFT compiled for portable x86-64-v3
# (AVX2 + FMA, generic tuning) instead of -march=native; the libraries are unchanged
mkdir -p build/fair
CF3="${CFLAGS/-march=native -mtune=native/-march=x86-64-v3 -mtune=generic}"
for f in impl_ext impl_ours bench_dft; do gcc $CF3 -c csrc/bench/$f.c -o build/fair/$f.o; done
g++ -o build/fair/bench_dft_v3 build/fair/bench_dft.o build/fair/impl_ours.o build/fair/impl_ext.o build/impl_ducc.o \
    build/ducc_threading.o build/ducc_string_utils.o $TP/fftw/lib/libfftw3.a -L$MKL_LIB -l:libmkl_intel_lp64.so.2 \
    -l:libmkl_sequential.so.2 -l:libmkl_core.so.2 -Wl,-rpath,$(realpath $MKL_LIB) -lquadmath -lm -lpthread
echo "build v3 ok"
# multithreaded benchmark: OpenMP pmfft_mt, threaded MKL (GNU OpenMP layer), FFTW with OpenMP; $BENCH_THREADS threads
if [ -f $TP/fftw/lib/libfftw3_omp.a ]; then
  mkdir -p build/mt
  for f in impl_ours impl_ext bench_dft; do gcc $CFLAGS -fopenmp -DBENCH_MT -c csrc/bench/$f.c -o build/mt/$f.o; done
  g++ -fopenmp -o build/bench_dft_mt build/mt/bench_dft.o build/mt/impl_ours.o build/mt/impl_ext.o build/impl_ducc.o \
      build/ducc_threading.o build/ducc_string_utils.o $TP/fftw/lib/libfftw3_omp.a $TP/fftw/lib/libfftw3.a \
      -L$MKL_LIB -l:libmkl_intel_lp64.so.2 -l:libmkl_gnu_thread.so.2 -l:libmkl_core.so.2 \
      -Wl,-rpath,$(realpath $MKL_LIB) -lquadmath -lm -lpthread
  echo "build mt ok"
else
  echo "skipping bench_dft_mt: $TP/fftw/lib/libfftw3_omp.a missing (FFTW built without OpenMP);"
  echo "  run scripts/setup_third_party.sh to rebuild FFTW with --enable-openmp"
fi
gcc $CFLAGS -o build/bench_conv csrc/bench/bench_conv.c $TP/fftw/lib/libfftw3.a -L$MKL_LIB -l:libmkl_intel_lp64.so.2 -l:libmkl_sequential.so.2 -l:libmkl_core.so.2 -Wl,-rpath,$(realpath $MKL_LIB) -lm -lpthread
gcc $CFLAGS -o build/bench_transpose csrc/tests/bench_transpose.c -lm
gcc $CFLAGS -o build/traffic_calib csrc/tests/traffic_calib.c -lm
gcc $CFLAGS -pthread -o build/stream_load csrc/tests/stream_load.c
echo "build2 ok"
gcc $CFLAGS -o build/bench_2d csrc/bench/bench_2d.c $TP/fftw/lib/libfftw3.a -L$MKL_LIB -l:libmkl_intel_lp64.so.2 -l:libmkl_sequential.so.2 -l:libmkl_core.so.2 -Wl,-rpath,$(realpath $MKL_LIB) -lm -lpthread
echo "build3 ok"
