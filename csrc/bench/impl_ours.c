// SPDX-License-Identifier: GPL-2.0-or-later
// Our implementations, each exposing the dft_impl interface with tunable params.
#include "impl.h"
#include "../dft/stockham.h"
#include "../dft/rec4.h"


// ---- baseline_radix2: iterative bit-reversal + radix-2 DIT, scalar (the common reference point) ----
typedef struct { int64_t n; double *tw; int64_t *rev; } r2_h;
static void *r2_plan(int64_t n, const char *p) {
    (void)p;
    if (n & (n - 1)) return NULL;
    r2_h *h = calloc(1, sizeof(r2_h));
    h->n = n;
    h->tw = xmalloc(sizeof(double) * n);
    for (int64_t k = 0; k < n / 2; k++) twiddle(k, n, h->tw + 2 * k, h->tw + 2 * k + 1);
    h->rev = xmalloc(sizeof(int64_t) * n);
    int lg = 0; while ((1LL << lg) < n) lg++;
    for (int64_t i = 0; i < n; i++) { int64_t r = 0; for (int b = 0; b < lg; b++) if (i >> b & 1) r |= 1LL << (lg - 1 - b); h->rev[i] = r; }
    return h;
}
static void r2_exec(void *hv, const double *in, double *out) {
    r2_h *h = hv; int64_t n = h->n;
    for (int64_t i = 0; i < n; i++) { out[2 * h->rev[i]] = in[2 * i]; out[2 * h->rev[i] + 1] = in[2 * i + 1]; }
    for (int64_t len = 2; len <= n; len <<= 1) {
        int64_t half = len / 2, step = n / len;
        for (int64_t i = 0; i < n; i += len)
            for (int64_t j = 0; j < half; j++) {
                double wr = h->tw[2 * j * step], wi = h->tw[2 * j * step + 1];
                double *a = out + 2 * (i + j), *b = out + 2 * (i + j + half);
                double br = b[0] * wr - b[1] * wi, bi = b[0] * wi + b[1] * wr;
                b[0] = a[0] - br; b[1] = a[1] - bi; a[0] += br; a[1] += bi;
            }
    }
}
static void r2_destroy(void *hv) { r2_h *h = hv; free(h->tw); free(h->rev); free(h); }
static const dft_impl impl_r2 = {"radix2", r2_plan, r2_exec, r2_destroy};

// ---- stockham: flat Stockham, every pass a full sweep. params: rmax (2..32), mode (0 opt,1 plain,2 naive) ----
typedef struct { sh_plan *p; double *work; } shw_h;
static void *shw_plan(int64_t n, const char *params) {
    int rmax = (int)param_get(params, "rmax", 16), mode = (int)param_get(params, "mode", 0);
    sh_plan *p = sh_plan_create(n, 1, rmax, mode);
    if (!p) return NULL;
    shw_h *h = malloc(sizeof(shw_h)); h->p = p; h->work = xmalloc(16 * n);
    return h;
}
static void shw_exec(void *hv, const double *in, double *out) { shw_h *h = hv; sh_exec_oop(h->p, in, out, h->work); }
static void shw_destroy(void *hv) { shw_h *h = hv; sh_plan_free(h->p); free(h->work); free(h); }
static const dft_impl impl_stockham = {"stockham", shw_plan, shw_exec, shw_destroy};

// ---- rec4: recursive batched four-step. params: budget (complex), Bc, G, split, rmax, mode, nt ----
typedef struct { rec4_plan *p; int nt; } rec4_h;
static void *rec4_plan_(int64_t n, const char *params) {
    rec4_params rp = {
        .budget = (int64_t)param_get(params, "budget", 32768), .Bc = (int64_t)param_get(params, "Bc", 0),
        .G = (int64_t)param_get(params, "G", 0), .split = (int)param_get(params, "split", 0),
        .rmax = (int)param_get(params, "rmax", 16), .mode = (int)param_get(params, "mode", 0),
        .nt = (int)param_get(params, "nt", 0), .pf = (int)param_get(params, "pf", 0),
        .N1top = (int64_t)param_get(params, "N1", 0), .pad = (int64_t)param_get(params, "pad", 0),
        .stage = (int64_t)param_get(params, "stage", 0), .only = (int)param_get(params, "only", 0),
        .threads = (int)param_get(params, "threads", bench_threads()), .stage2 = (int)param_get(params, "stage2", 0),
        .sep = (int)param_get(params, "sep", 0), .ceil = (int)param_get(params, "ceil", 0)};
    rec4_plan *p = rec4_plan_create(n, &rp);
    if (!p) return NULL;
    rec4_h *h = malloc(sizeof(rec4_h)); h->p = p; h->nt = rp.nt;
    return h;
}
static void rec4_exec_(void *hv, const double *in, double *out) { rec4_h *h = hv; rec4_plan_exec(h->p, in, out, h->nt); }
static void rec4_destroy_(void *hv) { rec4_h *h = hv; rec4_plan_free(h->p); free(h); }
static const dft_impl impl_rec4 = {"rec4", rec4_plan_, rec4_exec_, rec4_destroy_};


// ---- sixstep: Bailey six-step with three explicit transpose passes (I1 baseline for rec4) ----
// params: nt (NT stores in transposes)
typedef struct { int64_t n, N1, N2; sh_plan *p1, *p2; double *t1, *t2, *work, *tw; int nt; } six_h;
static void six_transpose(const double *in, double *out, int64_t R, int64_t Cc, int nt) {
    const int64_t T = 16;
    for (int64_t i0 = 0; i0 < R; i0 += T)
        for (int64_t j0 = 0; j0 < Cc; j0 += T)
            for (int64_t j = j0; j < j0 + T && j < Cc; j++) {
                int64_t i = i0;
                if (nt && i0 + T <= R)
                    for (; i < i0 + T; i += 2)
                        _mm256_stream_pd(out + 2 * (j * R + i), _mm256_permute2f128_pd(
                            _mm256_castpd128_pd256(_mm_loadu_pd(in + 2 * (i * Cc + j))),
                            _mm256_castpd128_pd256(_mm_loadu_pd(in + 2 * ((i + 1) * Cc + j))), 0x20));
                for (; i < i0 + T && i < R; i++) { out[2 * (j * R + i)] = in[2 * (i * Cc + j)]; out[2 * (j * R + i) + 1] = in[2 * (i * Cc + j) + 1]; }
            }
    if (nt) _mm_sfence();
}
static void *six_plan(int64_t n, const char *params) {
    int lg = 0; while ((1LL << lg) < n) lg++;
    if ((1LL << lg) != n || n < 64) return NULL;
    six_h *h = calloc(1, sizeof(six_h));
    h->n = n; h->N1 = 1LL << (lg / 2); h->N2 = n / h->N1; h->nt = (int)param_get(params, "nt", 0);
    h->p1 = sh_plan_create(h->N1, 1, 16, 0); h->p2 = sh_plan_create(h->N2, 1, 16, 0);
    h->t1 = xmalloc(16 * n); h->t2 = xmalloc(16 * n); h->work = xmalloc(16 * (h->N1 > h->N2 ? h->N1 : h->N2));
    h->tw = xmalloc(16 * n);  // full twiddle table w_n^{i2 k1}, layout [i2][k1]
    for (int64_t i2 = 0; i2 < h->N2; i2++) for (int64_t k1 = 0; k1 < h->N1; k1++) twiddle(i2 * k1, n, h->tw + 2 * (i2 * h->N1 + k1), h->tw + 2 * (i2 * h->N1 + k1) + 1);
    return h;
}
static void six_exec(void *hv, const double *in, double *out) {
    six_h *h = hv; int64_t N1 = h->N1, N2 = h->N2;
    six_transpose(in, h->t1, N1, N2, h->nt);                       // 1. (i1,i2) -> (i2,i1)
    for (int64_t i2 = 0; i2 < N2; i2++) {                           // 2. rows: FFT over i1, twiddle
        double *row = h->t1 + 2 * i2 * N1;
        sh_exec_oop(h->p1, row, h->t2 + 2 * i2 * N1, h->work);
        double *r = h->t2 + 2 * i2 * N1; const double *w = h->tw + 2 * i2 * N1;
        for (int64_t k = 0; k < N1; k += 2) VSTORE(r + 2 * k, vcmul(VLOAD(r + 2 * k), VLOAD(w + 2 * k)));
    }
    six_transpose(h->t2, h->t1, N2, N1, h->nt);                     // 3. (i2,k1) -> (k1,i2)
    for (int64_t k1 = 0; k1 < N1; k1++)                             // 4. rows: FFT over i2
        sh_exec_oop(h->p2, h->t1 + 2 * k1 * N2, h->t2 + 2 * k1 * N2, h->work);
    six_transpose(h->t2, out, N1, N2, h->nt);                       // 5. (k1,k2) -> (k2,k1)
}
static void six_destroy(void *hv) { six_h *h = hv; sh_plan_free(h->p1); sh_plan_free(h->p2); free(h->t1); free(h->t2); free(h->work); free(h->tw); free(h); }
static const dft_impl impl_sixstep = {"sixstep", six_plan, six_exec, six_destroy};

const dft_impl *ours_impls[] = {&impl_r2, &impl_stockham, &impl_rec4, &impl_sixstep, NULL};

// ---- arbitrary-n: bluestein / rader / gauss (I7, Toeplitz T4) ----
#include "../dft/arbitrary.h"
static void *blu_plan_(int64_t n, const char *p) { return blu_create(n, (int)param_get(p, "pow2", 0)); }
static void blu_exec_(void *h, const double *in, double *out) { blu_exec(h, in, out); }
static void blu_destroy_(void *h) { blu_free(h); }
static const dft_impl impl_bluestein = {"bluestein", blu_plan_, blu_exec_, blu_destroy_};

static void *rad_plan_(int64_t n, const char *p) { return rad_create(n, (int)param_get(p, "pow2", 0)); }
static void rad_exec_(void *h, const double *in, double *out) { rad_exec(h, in, out); }
static void rad_destroy_(void *h) { rad_free(h); }
static const dft_impl impl_rader = {"rader", rad_plan_, rad_exec_, rad_destroy_};

static void *gau_plan_(int64_t n, const char *p) {
    return gau_create(n, param_get(p, "L", 7), param_get(p, "delta", 0.25), (int)param_get(p, "iters", 4), (int)param_get(p, "pow2", 0));
}
static void gau_exec_(void *h, const double *in, double *out) { gau_exec(h, in, out); }
static void gau_destroy_(void *h) { gau_free(h); }
static const dft_impl impl_gauss = {"gauss", gau_plan_, gau_exec_, gau_destroy_};

const dft_impl *ours_impls2[] = {&impl_bluestein, &impl_rader, &impl_gauss, NULL};

// ---- pfa: Good-Thomas prime-factor mapping n = n1 * n2, gcd = 1, n1 = 2^a, n2 odd 3/5/7-smooth (I15) ----
// x is gathered with the Ruritanian map i = (i1 n2 + i2 n1) mod n into A[i2][i1] (i1 fastest), then
// FFT over i2 (batch n1, vectorised) and FFT over i1 (rows, contiguous): NO twiddle multiplications;
// the result is scattered with the CRT map k = (k1 n2 (n2^-1 mod n1) + k2 n1 (n1^-1 mod n2)) mod n.
typedef struct { int64_t n, n1, n2; int32_t *gin, *gout; sh_plan *pa, *pb; double *A, *B; } pfa_h;
static int64_t inv_mod(int64_t a, int64_t m) { for (int64_t x = 1; x < m; x++) if ((a * x) % m == 1) return x; return 1; }
static void *pfa_plan(int64_t n, const char *params) {
    (void)params;
    int64_t n1 = 1; while (n % (n1 * 2) == 0) n1 *= 2;
    int64_t n2 = n / n1;
    if (n1 < 2 || n2 < 3 || n > (1LL << 30)) return NULL;
    pfa_h *h = calloc(1, sizeof(pfa_h));
    h->n = n; h->n1 = n1; h->n2 = n2;
    h->pa = sh_plan_create(n2, n1, 16, 0);   // FFT over i2, batch n1 (layout A[i2][i1])
    h->pb = sh_plan_create(n1, 1, 16, 0);    // FFT over i1, one row at a time
    if (!h->pa || !h->pb) return NULL;
    h->gin = xmalloc(4 * n); h->gout = xmalloc(4 * n);
    int64_t e1 = n2 * inv_mod(n2 % n1, n1), e2 = n1 * inv_mod(n1 % n2, n2);
    for (int64_t i2 = 0; i2 < n2; i2++)
        for (int64_t i1 = 0; i1 < n1; i1++) h->gin[i2 * n1 + i1] = (int32_t)((i1 * n2 + i2 * n1) % n);
    // after both FFTs the element at [k1 row][k2 col] (layout B[k2][k1] -> we keep [k2][k1]) maps to CRT index
    for (int64_t k2 = 0; k2 < n2; k2++)
        for (int64_t k1 = 0; k1 < n1; k1++) h->gout[k2 * n1 + k1] = (int32_t)((k1 * e1 + k2 * e2) % n);
    h->A = xmalloc(16 * n); h->B = xmalloc(16 * n);
    return h;
}
static void pfa_exec(void *hv, const double *in, double *out) {
    pfa_h *h = hv; int64_t n = h->n, n1 = h->n1, n2 = h->n2;
    double *A = h->A, *B = h->B;
    for (int64_t i = 0; i < n; i++) _mm_store_pd(A + 2 * i, _mm_loadu_pd(in + 2 * h->gin[i]));
    double *r = sh_exec(h->pa, A, B);                     // FFT over i2: r[k2][i1]
    double *o = r == A ? B : A;
    for (int64_t k2 = 0; k2 < n2; k2++) sh_exec_oop(h->pb, r + 2 * k2 * n1, o + 2 * k2 * n1, out);  // rows: [k2][k1]
    for (int64_t i = 0; i < n; i++) _mm_storeu_pd(out + 2 * h->gout[i], _mm_load_pd(o + 2 * i));
}
static void pfa_destroy(void *hv) { pfa_h *h = hv; sh_plan_free(h->pa); sh_plan_free(h->pb); free(h->gin); free(h->gout); free(h->A); free(h->B); free(h); }
static const dft_impl impl_pfa = {"pfa", pfa_plan, pfa_exec, pfa_destroy};
const dft_impl *ours_impls3[] = {&impl_pfa, NULL};

#include "../dft/rdit.h"
// ---- pmfft: the combined practical algorithm (measuring planner over the winning ideas) ----
// smooth n : best of { Stockham(rmax in 4,8,16) } for small n, plus rec4 variants for larger n
// other n  : Bluestein on the smooth engine (exact, default)  |  Gaussian resampling when params "fast=1"
typedef struct { int kind, arg; void *h; double *ip; int64_t n; } pm_h;   // kind: 0 stockham, 1 rec4, 2 bluestein, 3 gauss, 4 rdit, 5 sixstep
// In-place calls (in == out, BENCH_INPLACE=1): the two-pass plans (rec4 with a split, sixstep) read all of `in` into
// their own scratch before writing `out`, so they run directly.  The in-cache plans (Stockham, recursive DIT) and
// Bluestein / Gauss read and write the same indices, so the input is first copied into a plan-owned array `ip`.
static int pm_inplace_safe(const pm_h *c) {
    return c->kind == 5 || (c->kind == 1 && !((rec4_h *)c->h)->p->root->leaf);
}
static pm_h *pm_finish(pm_h *c, int64_t n) {
    if (c) { c->n = n; c->ip = bench_inplace() && !pm_inplace_safe(c) ? xmalloc(16 * n) : NULL; }
    return c;
}
static void pm_exec(void *hv, const double *in, double *out);
static long pm_calls;   // transforms executed by the measuring planner for the current plan (reported to stderr)
static double pm_time(pm_h *c, int64_t n, double *a, double *b) {
    for (int64_t i = 0; i < 2 * n; i++) a[i] = 1e-3 * (double)(i % 97);
    pm_exec(c, a, b);
    pm_calls += 1;
    double best = 1e30;
    int reps = n <= 4096 ? 200 : n <= (1 << 16) ? 20 : n <= (1 << 20) ? 3 : 1;
    for (int r = 0; r < 3; r++) {
        double t = now_sec();
        for (int k = 0; k < reps; k++) pm_exec(c, a, b);
        pm_calls += reps;
        t = (now_sec() - t) / reps; if (t < best) best = t;
    }
    return best;
}
static void pm_free_cand(pm_h *c) {
    if (c->kind == 0) shw_destroy(c->h);
    else if (c->kind == 1) rec4_destroy_(c->h);
    else if (c->kind == 2) blu_free(c->h);
    else if (c->kind == 4) rdit_free(c->h);
    else if (c->kind == 5) six_destroy(c->h);
    else gau_free(c->h);
}
// smooth-n candidates: kind + argument (param string, or leaf size for rdit)
static const char *pm_sh_c[] = {"rmax=4", "rmax=8", "rmax=16"};
static const char *pm_r4_c[] = {"budget=16384,rmax=8,nt=1,pad=4", "budget=131072,rmax=8,nt=1,pad=4",
                                "budget=131072,rmax=16,nt=1,pad=4", "budget=16384,rmax=16,nt=1,pad=4",
                                "budget=131072,rmax=16,nt=1,pad=4,split=1", "budget=131072,rmax=8,nt=1,pad=4,split=1",
                                // traffic-minimal: N1 = 2048 rows staged 256 columns (4 KB) at a time through an 8 MB
                                // buffer; removes the hardware-prefetch overfetch of the strided gather (~4.0 S total)
                                "budget=131072,rmax=8,nt=1,pad=4,N1=2048,G=4,stage=256"};
#define PM_STAGED 6
static int pm_staged_ok(int64_t n) { return n >= (1 << 21) && n % 2048 == 0 && (n / 2048) % 256 == 0; }
static void *pm_make(int kind, int arg, int64_t n) {
    switch (kind) {
    case 0: return shw_plan(n, pm_sh_c[arg]);
    case 4: return rdit_create(n, arg, 8, 8);
    case 1: return rec4_plan_(n, pm_r4_c[arg]);
    default: return six_plan(n, "nt=1");   // explicit NT transposes (I1 ablation: wins at 2^18, 2^26)
    }
}
static void *pm_plan(int64_t n, const char *params) {
    int fast = (int)param_get(params, "fast", 0);
    pm_h *best = NULL;
    int rad[SH_MAXPASS];
    if (sh_factor(n, 16, rad) || n == 1) {
        int ck[16], ca[16], nc = 0;
        if (n <= (1 << 18))
            for (int i = 0; i < 3; i++) { ck[nc] = 0; ca[nc++] = i; }
        if (n >= (1 << 12) && n <= (1 << 20) && !(n & (n - 1)))
            for (int lf = 256; lf <= 1024; lf *= 4) { ck[nc] = 4; ca[nc++] = lf; }
        if (n > (1 << 13))
            for (int i = 0; i < (n >= (1 << 23) ? 6 : 4); i++) { ck[nc] = 1; ca[nc++] = i; }
        if (n >= (1 << 17) && !(n & (n - 1))) { ck[nc] = 5; ca[nc++] = 0; }
        if (pm_staged_ok(n)) { ck[nc] = 1; ca[nc++] = PM_STAGED; }
        // Keep the timed instance of the winner rather than rebuilding it: large transposing plans (sixstep at
        // 2^26) vary by up to 25% between instances depending on where their huge pages land physically, and
        // keeping the measured instance carries a lucky placement through.  One shared pair of test arrays.
        double *a = xmalloc(16 * n), *b = xmalloc(16 * n), bt = 1e30;
        int ncand = 0;
        pm_calls = 0;
        for (int i = 0; i < nc; i++) {
            pm_h *c = calloc(1, sizeof(pm_h)); c->kind = ck[i]; c->arg = ca[i]; c->h = pm_make(ck[i], ca[i], n);
            if (!c->h) { free(c); continue; }
            double t = pm_time(c, n, a, b);
            ncand++;
            if (getenv("PMFFT_VERBOSE")) fprintf(stderr, "pmfft plan n=%ld cand kind=%d arg=%d: %.3f ms\n", (long)n, ck[i], ca[i], t * 1e3);
            if (t < bt) { if (best) { pm_free_cand(best); free(best); } best = c; bt = t; } else { pm_free_cand(c); free(c); }
        }
        free(a); free(b);
        fprintf(stderr, "planner n=%ld candidates=%d timed_transforms=%ld\n", (long)n, ncand, pm_calls);
        return pm_finish(best, n);
    }
    best = calloc(1, sizeof(pm_h)); best->arg = 0;
    if (fast) { best->kind = 3; best->h = gau_create(n, param_get(params, "L", 4), param_get(params, "delta", 0.4), (int)param_get(params, "iters", 1), 0); }
    else { best->kind = 2; best->h = blu_create(n, n >= 500000); }  // pow2 padding wins for large n (I7 sweep)
    return pm_finish(best, n);
}
static void pm_exec(void *hv, const double *in, double *out) {
    pm_h *c = hv;
    if (in == out && c->ip) { memcpy(c->ip, in, 16 * c->n); in = c->ip; }
    switch (c->kind) {
    case 0: shw_exec(c->h, in, out); break;
    case 1: rec4_exec_(c->h, in, out); break;
    case 2: blu_exec(c->h, in, out); break;
    case 4: rdit_exec(c->h, in, out); break;
    case 5: six_exec(c->h, in, out); break;
    default: gau_exec(c->h, in, out);
    }
}
static void pm_destroy(void *hv) { pm_free_cand(hv); free(((pm_h *)hv)->ip); free(hv); }
// the planner's choice, e.g. "stockham:rmax=8", "rec4:budget=131072,rmax=8,nt=1,pad=4,split=1", "sixstep:nt=1"
static const char *pm_describe(void *hv) {
    static char buf[160];
    pm_h *c = hv;
    switch (c->kind) {
    case 0: snprintf(buf, sizeof buf, "stockham:%s", pm_sh_c[c->arg]); break;
    case 1: snprintf(buf, sizeof buf, "rec4:%s", pm_r4_c[c->arg]); break;
    case 2: snprintf(buf, sizeof buf, "bluestein"); break;
    case 4: snprintf(buf, sizeof buf, "rdit:leaf=%d", c->arg); break;
    case 5: snprintf(buf, sizeof buf, "sixstep:nt=1"); break;
    default: snprintf(buf, sizeof buf, "gauss");
    }
    return buf;
}
static const dft_impl impl_pmfft = {"pmfft", pm_plan, pm_exec, pm_destroy, pm_describe};

// pmfft_heur: same components, fixed size rule instead of measuring (planning ~ twiddle setup only).
// Rule from the reference-machine planner choices (PMFFT_VERBOSE=1): Stockham radix-8 up to 2^18, recursive
// DIT at 2^19, rec4 beyond (radix-16 small-budget at 2^20; radix-8 leaves; from 2^25 the staged traffic-minimal
// rec4, which is also faster there on one core).  Staging is not used below 2^25 because its 8 MB buffer per
// transform overflows the shared L3 when several transforms run at once (results/scale_mp_staged.csv).
static void *pmh_plan(int64_t n, const char *params) {
    int rad[SH_MAXPASS];
    if (!(sh_factor(n, 16, rad) || n == 1)) return pm_plan(n, params);    // non-smooth: Bluestein / Gauss as pmfft
    pm_h *c = calloc(1, sizeof(pm_h));
    int pow2 = !(n & (n - 1));
    if (n <= (1 << 18)) { c->kind = 0; c->arg = 1; }
    else if (n <= (1 << 19) && pow2) { c->kind = 4; c->arg = 1024; }
    else if (n <= (1 << 20)) { c->kind = 1; c->arg = 3; }                                     // small budget, radix 16
    else if (n >= (1 << 25) && pm_staged_ok(n)) { c->kind = 1; c->arg = PM_STAGED; }             // staged rec4
    else { c->kind = 1; c->arg = n >= (1 << 25) ? 5 : 1; }
    c->h = pm_make(c->kind, c->arg, n);
    if (!c->h) { free(c); return NULL; }
    return pm_finish(c, n);
}
static const dft_impl impl_pmfft_heur = {"pmfft_heur", pmh_plan, pm_exec, pm_destroy, pm_describe};
// pmfft_mt: multithreaded pmfft (OpenMP, $BENCH_THREADS threads).  For smooth n >= 2^20 the measuring planner
// times the multithreaded rec4 variants (balanced, small-inner split, staged with one shared staging buffer) at
// the actual thread count and keeps the fastest; smaller or non-smooth n run the single-threaded pmfft.
typedef struct { int mt; void *h; } pmt_h;
static void *pmt_plan(int64_t n, const char *params) {
    const int T = (int)param_get(params, "threads", bench_threads());
    int rad[SH_MAXPASS];
    pmt_h *P = calloc(1, sizeof(pmt_h));
    if (T > 1 && n >= (1 << 20) && sh_factor(n, 16, rad)) {
        static const char *cand[] = {"budget=131072,rmax=8,nt=1,pad=4", "budget=131072,rmax=8,nt=1,pad=4,split=1",
                                     "budget=131072,rmax=16,nt=1,pad=4", "budget=131072,rmax=8,nt=1,pad=4,N1=2048,G=4,stage=256"};
        double *a = xmalloc(16 * n), *b = xmalloc(16 * n), bt = 1e30;
        for (int64_t i = 0; i < 2 * n; i++) a[i] = 1e-3 * (double)(i % 97);
        void *best = NULL;
        for (int i = 0; i < 4; i++) {
            if (i == 3 && !pm_staged_ok(n)) continue;
            char pr[256]; snprintf(pr, sizeof pr, "%s,threads=%d", cand[i], T);
            void *h = rec4_plan_(n, pr);
            if (!h || ((rec4_h *)h)->p->T != T) { if (h) rec4_destroy_(h); continue; }
            rec4_exec_(h, a, b);
            double t = 1e30;
            for (int r = 0; r < 3; r++) { double t0 = now_sec(); rec4_exec_(h, a, b); t0 = now_sec() - t0; if (t0 < t) t = t0; }
            if (getenv("PMFFT_VERBOSE")) fprintf(stderr, "pmfft_mt plan n=%ld T=%d cand %d: %.3f ms\n", (long)n, T, i, t * 1e3);
            if (t < bt) { if (best) rec4_destroy_(best); best = h; bt = t; } else rec4_destroy_(h);
        }
        free(a); free(b);
        if (best) { P->mt = 1; P->h = best; return P; }
    }
    P->h = pm_plan(n, params);
    if (!P->h) { free(P); return NULL; }
    return P;
}
static void pmt_exec(void *hv, const double *in, double *out) {
    pmt_h *P = hv;
    if (P->mt) rec4_exec_(P->h, in, out); else pm_exec(P->h, in, out);
}
static void pmt_destroy(void *hv) { pmt_h *P = hv; if (P->mt) rec4_destroy_(P->h); else pm_destroy(P->h); free(P); }
static const char *pmt_describe(void *hv) { pmt_h *P = hv; return P->mt ? "rec4_mt" : pm_describe(P->h); }
static const dft_impl impl_pmfft_mt = {"pmfft_mt", pmt_plan, pmt_exec, pmt_destroy, pmt_describe};

const dft_impl *ours_impls4[] = {&impl_pmfft, &impl_pmfft_heur, &impl_pmfft_mt, NULL};

// ---- rdit: depth-first recursive DIT for mid sizes. params: leaf, rmax (combine radix), lrmax (leaf radix) ----
static void *rdit_plan_(int64_t n, const char *p) {
    return rdit_create(n, (int64_t)param_get(p, "leaf", 1024), (int)param_get(p, "rmax", 8), (int)param_get(p, "lrmax", 8));
}
static void rdit_exec_(void *h, const double *in, double *out) { rdit_exec(h, in, out); }
static void rdit_destroy_(void *h) { rdit_free(h); }
static const dft_impl impl_rdit = {"rdit", rdit_plan_, rdit_exec_, rdit_destroy_};
const dft_impl *ours_impls5[] = {&impl_rdit, NULL};
