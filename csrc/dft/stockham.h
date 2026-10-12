// SPDX-License-Identifier: GPL-2.0-or-later
// Stockham autosort mixed-radix engine (DIF), batched, AVX2.
//
// Data layout: B interleaved transforms of length n, element (b, i) at complex index b + B*i.
// Each radix-R pass is one sweep over the array; f = log2 R butterfly levels are fused per
// sweep (idea I2, "simultaneous butterfly layers").  Output is in natural order (no bit-reversal
// pass, idea I9).  The kernel used for each pass is a generated codelet (idea I10).
#pragma once
#include "../common/common.h"
#include "codelets_gen.h"

#define SH_MAXPASS 64

typedef struct {
    int64_t n, B;          // transform length, batch (initial stride)
    int npass;
    int radix[SH_MAXPASS];
    int64_t m[SH_MAXPASS];  // n_cur / R at each pass
    int64_t s[SH_MAXPASS];  // stride at each pass
    double *tw[SH_MAXPASS]; // twiddles: s>=2 layout [p][r-1] complex; s==1 layout [p/2][r-1] V
    void (*fn[SH_MAXPASS])(int64_t, int64_t, const double *restrict, const double *restrict, double *restrict);
    int mode;               // codelet variant 0=opt 1=plain 2=naive
} sh_plan;

typedef void (*sh_pass_fn)(int64_t, int64_t, const double *restrict, const double *restrict, double *restrict);
static sh_pass_fn sh_get_pass(int R, int mode, int kind);
static inline int sh_kind(int R, int64_t m, int64_t s);

// Factor n into radices <= rmax (powers of two first, largest first; then 3,5,7).
// Returns 0 if n has a prime factor > 7.
static int sh_factor(int64_t n, int rmax, int *rad) {
    int np = 0;
    int64_t k = n;
    int l2 = 0;
    while ((k & 1) == 0) { k >>= 1; l2++; }
    int lr = 0; while ((1 << (lr + 1)) <= rmax) lr++;
    if (lr < 1) lr = 1;
    // split l2 into chunks of at most lr, as even as possible (avoid a radix-2 tail)
    if (l2 > 0) {
        int cnt = (l2 + lr - 1) / lr;
        int base = l2 / cnt, extra = l2 % cnt;
        for (int i = 0; i < cnt; i++) rad[np++] = 1 << (base + (i < extra ? 1 : 0));
    }
    const int odd[3] = {3, 5, 7};
    for (int i = 0; i < 3; i++) while (k % odd[i] == 0) { rad[np++] = odd[i]; k /= odd[i]; }
    if (k != 1) return 0;
    return np;
}

static sh_plan *sh_plan_create_radices(int64_t n, int64_t B, const int *rad, int np, int mode) {
    sh_plan *P = (sh_plan *)calloc(1, sizeof(sh_plan));
    P->n = n; P->B = B; P->mode = mode; P->npass = np;
    int64_t ncur = n, s = B;
    for (int i = 0; i < np; i++) {
        int R = rad[i];
        int64_t m = ncur / R;
        P->radix[i] = R; P->m[i] = m; P->s[i] = s;
        P->fn[i] = sh_get_pass(R, mode, sh_kind(R, m, s));
        if (!P->fn[i]) { fprintf(stderr, "no pass kernel for radix %d\n", R); exit(1); }
        if (s == 1 && (R % 2 == 0) && (m % 2 == 0)) {
            double *t = (double *)xmalloc(sizeof(double) * 4 * (R - 1) * (m / 2) + 64);
            for (int64_t p = 0; p < m; p += 2)
                for (int r = 1; r < R; r++) {
                    double *d = t + 4 * ((p / 2) * (R - 1) + (r - 1));
                    twiddle(r * p, ncur, d + 0, d + 1);
                    twiddle(r * (p + 1), ncur, d + 2, d + 3);
                }
            P->tw[i] = t;
        } else {
            double *t = (double *)xmalloc(sizeof(double) * 2 * (R - 1) * m + 64);
            for (int64_t p = 0; p < m; p++)
                for (int r = 1; r < R; r++) twiddle(r * p, ncur, t + 2 * (p * (R - 1) + r - 1), t + 2 * (p * (R - 1) + r - 1) + 1);
            P->tw[i] = t;
        }
        ncur = m; s *= R;
    }
    return P;
}

static sh_plan *sh_plan_create(int64_t n, int64_t B, int rmax, int mode) {
    int rad[SH_MAXPASS];
    int np = sh_factor(n, rmax, rad);
    if (np == 0 && n != 1) return NULL;
    return sh_plan_create_radices(n, B, rad, np, mode);
}

static void sh_plan_free(sh_plan *P) {
    if (!P) return;
    for (int i = 0; i < P->npass; i++) free(P->tw[i]);
    free(P);
}

// Pass kernels are stamped out per (codelet variant, radix) so the codelet inlines.
#define SH_DEF(MODE, R)                                                                              \
static void shq_##MODE##_##R(int64_t m, int64_t s, const double *restrict tw,                       \
                             const double *restrict x, double *restrict y) {                         \
    V a[R];                                                                                           \
    for (int64_t p = 0; p < m; p++) {                                                                 \
        const double *twp = tw + 2 * p * (R - 1);                                                     \
        V w[R];                                                                                       \
        for (int r = 1; r < R; r++) w[r] = vbroadcast_c(twp + 2 * (r - 1));                           \
        const double *xp = x + 2 * s * p; double *yp = y + 2 * s * R * p;                             \
        if (p == 0) {                                                                                 \
            for (int64_t q = 0; q < s; q += 2) {                                                      \
                for (int r = 0; r < R; r++) a[r] = VLOAD(xp + 2 * (q + s * r * m));                    \
                cl_##MODE##_##R(a);                                                                   \
                for (int r = 0; r < R; r++) VSTORE(yp + 2 * (q + s * r), a[r]);                        \
            }                                                                                         \
        } else {                                                                                      \
            for (int64_t q = 0; q < s; q += 2) {                                                      \
                for (int r = 0; r < R; r++) a[r] = VLOAD(xp + 2 * (q + s * r * m));                    \
                cl_##MODE##_##R(a);                                                                   \
                VSTORE(yp + 2 * q, a[0]);                                                             \
                for (int r = 1; r < R; r++) VSTORE(yp + 2 * (q + s * r), vcmul(a[r], w[r]));           \
            }                                                                                         \
        }                                                                                             \
    }                                                                                                 \
}                                                                                                     \
static void shp_##MODE##_##R(int64_t m, int64_t s, const double *restrict tw,                       \
                             const double *restrict x, double *restrict y) {                         \
    (void)s; V a[R + 1];                                                                              \
    for (int64_t p = 0; p < m; p += 2) {                                                              \
        for (int r = 0; r < R; r++) a[r] = VLOADU(x + 2 * (p + r * m));                               \
        cl_##MODE##_##R(a);                                                                           \
        const double *twp = tw + 4 * (p / 2) * (R - 1);                                               \
        for (int r = 1; r < R; r++) a[r] = vcmul(a[r], VLOAD(twp + 4 * (r - 1)));                       \
        for (int r = 0; r + 1 < R; r += 2) {                                                          \
            VSTOREU(y + 2 * (R * p + r), _mm256_permute2f128_pd(a[r], a[r + 1], 0x20));                \
            VSTOREU(y + 2 * (R * (p + 1) + r), _mm256_permute2f128_pd(a[r], a[r + 1], 0x31));          \
        }                                                                                             \
    }                                                                                                 \
}                                                                                                     \
static void shs_##MODE##_##R(int64_t m, int64_t s, const double *restrict tw,                       \
                             const double *restrict x, double *restrict y) {                         \
    V a[R];                                                                                           \
    for (int64_t p = 0; p < m; p++) {                                                                 \
        const double *twp = tw + 2 * p * (R - 1);                                                     \
        for (int64_t q = 0; q < s; q++) {                                                             \
            for (int r = 0; r < R; r++) a[r] = vbroadcast_c(x + 2 * (q + s * (p + r * m)));            \
            cl_##MODE##_##R(a);                                                                       \
            _mm_storeu_pd(y + 2 * (q + s * (R * p)), _mm256_castpd256_pd128(a[0]));                   \
            for (int r = 1; r < R; r++)                                                               \
                _mm_storeu_pd(y + 2 * (q + s * (R * p + r)),                                          \
                              _mm256_castpd256_pd128(vcmul(a[r], vbroadcast_c(twp + 2 * (r - 1))))); \
        }                                                                                             \
    }                                                                                                 \
}

#define SH_DEF_MODE(MODE) SH_DEF(MODE, 2) SH_DEF(MODE, 4) SH_DEF(MODE, 8) SH_DEF(MODE, 16) SH_DEF(MODE, 32)
SH_DEF_MODE(opt)
SH_DEF_MODE(plain)
SH_DEF_MODE(naive)
SH_DEF(opt, 3) SH_DEF(opt, 5) SH_DEF(opt, 7)

// kind: 0 = vec over q, 1 = vec over p, 2 = scalar
static sh_pass_fn sh_get_pass(int R, int mode, int kind) {
#define SH_CASE(MODE, RR) case RR: return kind == 0 ? shq_##MODE##_##RR : kind == 1 ? shp_##MODE##_##RR : shs_##MODE##_##RR;
    if (R == 3 || R == 5 || R == 7) mode = 0;
    if (mode == 0) { switch (R) { SH_CASE(opt, 2) SH_CASE(opt, 4) SH_CASE(opt, 8) SH_CASE(opt, 16) SH_CASE(opt, 32) SH_CASE(opt, 3) SH_CASE(opt, 5) SH_CASE(opt, 7) } }
    if (mode == 1) { switch (R) { SH_CASE(plain, 2) SH_CASE(plain, 4) SH_CASE(plain, 8) SH_CASE(plain, 16) SH_CASE(plain, 32) } }
    if (mode == 2) { switch (R) { SH_CASE(naive, 2) SH_CASE(naive, 4) SH_CASE(naive, 8) SH_CASE(naive, 16) SH_CASE(naive, 32) } }
#undef SH_CASE
    return 0;
}

static inline int sh_kind(int R, int64_t m, int64_t s) {
    if (s >= 2 && (s % 2 == 0)) return 0;
    if (s == 1 && R % 2 == 0 && m % 2 == 0) return 1;
    return 2;
}

// Execute: input in x, scratch in w (same size). Returns pointer (x or w) holding the result.
static double *sh_exec(const sh_plan *P, double *x, double *w) {
    double *src = x, *dst = w;
    for (int i = 0; i < P->npass; i++) {
        int R = P->radix[i];
        int64_t m = P->m[i], s = P->s[i];
        P->fn[i](m, s, P->tw[i], src, dst); (void)R;
        double *t = src; src = dst; dst = t;
    }
    return src;
}

// Convenience: out-of-place, result always in out; work is scratch of n*B complex.
static void sh_exec_oop(const sh_plan *P, const double *in, double *out, double *work) {
    size_t bytes = sizeof(double) * 2 * P->n * P->B;
    if (P->npass == 0) { if (out != in) memcpy(out, in, bytes); return; }
    // choose first buffer so that the final pass lands in out
    if (P->npass % 2 == 1) {
        // pass1: in->out, pass2: out->work, ... odd count ends in out when we start in->out
        double *src = (double *)in, *dst = out;
        for (int i = 0; i < P->npass; i++) {
            int R = P->radix[i]; int64_t m = P->m[i], s = P->s[i];
            P->fn[i](m, s, P->tw[i], src, dst); (void)R;
            src = dst; dst = (i % 2 == 0) ? work : out;
        }
    } else {
        double *src = (double *)in, *dst = work;
        for (int i = 0; i < P->npass; i++) {
            int R = P->radix[i]; int64_t m = P->m[i], s = P->s[i];
            P->fn[i](m, s, P->tw[i], src, dst); (void)R;
            src = dst; dst = (i % 2 == 0) ? out : work;
        }
    }
}
