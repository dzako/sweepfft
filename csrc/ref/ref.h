// SPDX-License-Identifier: GPL-2.0-or-later
// Quad-precision (__float128) reference DFT for accuracy measurement.
// Power-of-two n: iterative radix-2.  Other n: Bluestein in quad precision on top of it.
#pragma once
#include <quadmath.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef __float128 q_t;
typedef struct { q_t re, im; } qc;

static inline qc qc_mul(qc a, qc b) { return (qc){a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re}; }

// exp(sign * 2 pi i k / n)
static inline qc qc_root(int64_t k, int64_t n, int sign) {
    k %= n; if (k < 0) k += n;
    q_t a = 2 * M_PIq * (q_t)k / (q_t)n;
    return (qc){cosq(a), sign * sinq(a)};
}

static void qfft_pow2(qc *x, int64_t n, int sign) {
    for (int64_t i = 1, j = 0; i < n; i++) {
        int64_t bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) { qc t = x[i]; x[i] = x[j]; x[j] = t; }
    }
    qc *w = (qc *)malloc(sizeof(qc) * (n / 2 + 1));
    for (int64_t k = 0; k < n / 2; k++) w[k] = qc_root(k, n, sign);
    for (int64_t len = 2; len <= n; len <<= 1) {
        int64_t step = n / len;
        for (int64_t i = 0; i < n; i += len)
            for (int64_t j = 0; j < len / 2; j++) {
                qc u = x[i + j], v = qc_mul(x[i + j + len / 2], w[j * step]);
                x[i + j] = (qc){u.re + v.re, u.im + v.im};
                x[i + j + len / 2] = (qc){u.re - v.re, u.im - v.im};
            }
    }
    free(w);
}

// Forward DFT (sign -1), arbitrary n, input/output interleaved doubles; output in quad.
static void ref_dft(const double *in, int64_t n, qc *out) {
    if ((n & (n - 1)) == 0) {
        for (int64_t i = 0; i < n; i++) out[i] = (qc){in[2 * i], in[2 * i + 1]};
        qfft_pow2(out, n, -1);
        return;
    }
    if (n <= 512) {
        for (int64_t k = 0; k < n; k++) {
            qc acc = {0, 0};
            for (int64_t j = 0; j < n; j++) {
                qc t = qc_mul((qc){in[2 * j], in[2 * j + 1]}, qc_root((j * k) % n, n, -1));
                acc.re += t.re; acc.im += t.im;
            }
            out[k] = acc;
        }
        return;
    }
    int64_t M = 1; while (M < 2 * n - 1) M <<= 1;
    qc *a = (qc *)calloc(M, sizeof(qc)), *b = (qc *)calloc(M, sizeof(qc));
    qc *chirp = (qc *)malloc(sizeof(qc) * n);
    for (int64_t k = 0; k < n; k++) chirp[k] = qc_root((k * k) % (2 * n), 2 * n, -1); // exp(-pi i k^2/n)
    for (int64_t k = 0; k < n; k++) a[k] = qc_mul((qc){in[2 * k], in[2 * k + 1]}, chirp[k]);
    for (int64_t k = 0; k < n; k++) {
        qc c = {chirp[k].re, -chirp[k].im};
        b[k] = c; if (k) b[M - k] = c;
    }
    qfft_pow2(a, M, -1); qfft_pow2(b, M, -1);
    for (int64_t i = 0; i < M; i++) a[i] = qc_mul(a[i], b[i]);
    qfft_pow2(a, M, 1);
    for (int64_t k = 0; k < n; k++) {
        qc v = qc_mul(a[k], chirp[k]);
        out[k] = (qc){v.re / M, v.im / M};
    }
    free(a); free(b); free(chirp);
}

// Relative errors: rms = ||y - ref||_2 / ||ref||_2 ; max = max_k |y_k - ref_k| / max_k |ref_k|
static void ref_errors(const double *y, const qc *ref, int64_t n, double *rms, double *mx) {
    q_t num = 0, den = 0, mnum = 0, mden = 0;
    for (int64_t k = 0; k < n; k++) {
        q_t dr = (q_t)y[2 * k] - ref[k].re, di = (q_t)y[2 * k + 1] - ref[k].im;
        q_t e2 = dr * dr + di * di, r2 = ref[k].re * ref[k].re + ref[k].im * ref[k].im;
        num += e2; den += r2;
        if (e2 > mnum) mnum = e2;
        if (r2 > mden) mden = r2;
    }
    *rms = (double)sqrtq(num / den);
    *mx = (double)sqrtq(mnum / mden);
}
