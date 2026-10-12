// SPDX-License-Identifier: GPL-2.0-or-later
// Depth-first recursive out-of-place DIT (FFTW-style) for in-cache / mid sizes.
//   rdit(n, in, istride, out):  R sub-transforms of x[r::R] (strided reads, contiguous outputs),
//   then an in-place radix-R combine pass with twiddles, vectorised over k.
// Leaves (n <= leaf) gather their strided input into an L1 buffer and run the Stockham engine.
// No permutation pass; every level after the leaves works on contiguous, cache-resident blocks.
#pragma once
#include "stockham.h"

typedef struct rdit_lvl {
    int64_t n, m; int R;       // n = R * m
    double *tw;                // [k/2][r-1] V layout: (w^{r k}, w^{r (k+1)})
    struct rdit_lvl *child;    // sub-level for size m (NULL -> leaf)
} rdit_lvl;

typedef struct {
    int64_t n, leaf;
    rdit_lvl *top;
    sh_plan *lp;               // leaf Stockham plan
    double *lbuf, *lbuf2;
} rdit_plan;

#define RD_COMB(R)                                                                                       \
static void rd_comb_##R(int64_t m, const double *restrict tw, double *restrict y) {                     \
    V a[R];                                                                                              \
    for (int64_t k = 0; k < m; k += 2) {                                                                 \
        const double *t = tw + 4 * (k / 2) * (R - 1);                                                    \
        a[0] = VLOAD(y + 2 * k);                                                                         \
        for (int r = 1; r < R; r++) a[r] = vcmul(VLOAD(y + 2 * (k + r * m)), VLOAD(t + 4 * (r - 1)));    \
        cl_opt_##R(a);                                                                                   \
        for (int q = 0; q < R; q++) VSTORE(y + 2 * (k + q * m), a[q]);                                   \
    }                                                                                                    \
}
RD_COMB(2) RD_COMB(4) RD_COMB(8) RD_COMB(16)

static rdit_lvl *rdit_build(int64_t n, int64_t leaf, int rmax) {
    if (n <= leaf) return NULL;
    rdit_lvl *L = (rdit_lvl *)calloc(1, sizeof(rdit_lvl));
    int R = rmax;
    while (R > 2 && (n % R || n / R < 2)) R /= 2;
    // keep the remaining size a multiple of the leaf grid: prefer that n/R >= leaf or is a power of 2
    L->n = n; L->R = R; L->m = n / R;
    int64_t m = L->m;
    L->tw = (double *)xmalloc(sizeof(double) * 4 * (R - 1) * ((m + 1) / 2) + 64);
    for (int64_t k = 0; k < m; k += 2)
        for (int r = 1; r < R; r++) {
            double *d = L->tw + 4 * ((k / 2) * (R - 1) + (r - 1));
            twiddle(r * k, n, d, d + 1);
            twiddle(r * (k + 1), n, d + 2, d + 3);
        }
    L->child = rdit_build(m, leaf, rmax);
    return L;
}

static rdit_plan *rdit_create(int64_t n, int64_t leaf, int rmax, int leafrmax) {
    if (n & (n - 1)) return NULL;           // powers of two only (mid-size path)
    if (leaf > n) leaf = n;
    rdit_plan *P = (rdit_plan *)calloc(1, sizeof(rdit_plan));
    P->n = n; P->leaf = leaf;
    P->top = rdit_build(n, leaf, rmax);
    // leaf size actually reached
    int64_t ls = n; for (rdit_lvl *l = P->top; l; l = l->child) ls = l->m;
    P->leaf = ls;
    P->lp = sh_plan_create(ls, 1, leafrmax, 0);
    P->lbuf = (double *)xmalloc(16 * ls); P->lbuf2 = (double *)xmalloc(16 * ls);
    return P;
}

static void rdit_rec(const rdit_plan *P, const rdit_lvl *L, const double *in, int64_t is, double *out) {
    if (!L) {
        const int64_t ls = P->leaf;
        double *b = P->lbuf;
        for (int64_t j = 0; j < ls; j++) _mm_store_pd(b + 2 * j, _mm_loadu_pd(in + 2 * j * is));
        sh_exec_oop(P->lp, b, out, P->lbuf2);
        return;
    }
    const int R = L->R; const int64_t m = L->m;
    for (int r = 0; r < R; r++) rdit_rec(P, L->child, in + 2 * r * is, is * R, out + 2 * r * m);
    switch (R) {
    case 2: rd_comb_2(m, L->tw, out); break;
    case 4: rd_comb_4(m, L->tw, out); break;
    case 8: rd_comb_8(m, L->tw, out); break;
    default: rd_comb_16(m, L->tw, out); break;
    }
}

static void rdit_exec(const rdit_plan *P, const double *in, double *out) { rdit_rec(P, P->top, in, 1, out); }

static void rdit_free_lvl(rdit_lvl *L) { if (!L) return; rdit_free_lvl(L->child); free(L->tw); free(L); }
static void rdit_free(rdit_plan *P) { rdit_free_lvl(P->top); sh_plan_free(P->lp); free(P->lbuf); free(P->lbuf2); free(P); }
