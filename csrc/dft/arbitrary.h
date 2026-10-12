// SPDX-License-Identifier: GPL-2.0-or-later
// Arbitrary-length DFTs built on the smooth-length engine (rec4 / Stockham):
//   Bluestein  : DFT = D T D  (D = diag chirp, T Toeplitz) -> cyclic convolution of length M >= 2n-1
//   Rader      : prime n, DFT restricted to nonzero indices is a circulant of length n-1
//   Gauss      : Harvey-van der Hoeven style Gaussian resampling to a smooth length t ~ (1+delta) n,
//                one FFT of length t, deconvolution, Neumann-series alias correction   (idea I7)
#pragma once
#include "rec4.h"

// ---------------- smooth-length engine ----------------
typedef struct { rec4_plan *p; int64_t n; } fe_plan;
static int is_smooth(int64_t m) {
    for (int f = 2; f <= 7; f++) while (m % f == 0) m /= f;
    return m == 1;
}
static int64_t next_smooth(int64_t m, int pow2only) {
    if (pow2only) { int64_t t = 1; while (t < m) t <<= 1; return t; }
    for (int64_t t = m + (m & 1);; t += 2) if (is_smooth(t)) return t;
}
static fe_plan *fe_create(int64_t n) {
    rec4_params rp = {.budget = 131072, .Bc = 8, .G = 8, .split = 0, .rmax = 16, .mode = 0, .nt = 1, .pad = 4};
    fe_plan *f = (fe_plan *)calloc(1, sizeof(fe_plan));
    f->n = n; f->p = rec4_plan_create(n, &rp);
    if (!f->p) { fprintf(stderr, "fe_create: unsupported n=%ld\n", n); exit(1); }
    return f;
}
static void fe_exec(const fe_plan *f, const double *in, double *out) { rec4_plan_exec(f->p, in, out, 1); }
static void fe_free(fe_plan *f) { rec4_plan_free(f->p); free(f); }

// exp(-i pi k^2 / n) exactly reduced
static void chirp(int64_t k, int64_t n, double *re, double *im) {
    __int128 kk = (__int128)k * k % (2 * n);
    twiddle((int64_t)kk, 2 * n, re, im);
}

// ---------------- Bluestein ----------------
typedef struct { int64_t n, M; fe_plan *f; double *ch, *Bh, *a, *A; } blu_plan;
static blu_plan *blu_create(int64_t n, int pow2only) {
    blu_plan *P = (blu_plan *)calloc(1, sizeof(blu_plan));
    P->n = n; P->M = next_smooth(2 * n - 1, pow2only);
    int64_t M = P->M;
    P->f = fe_create(M);
    P->ch = (double *)xmalloc(16 * n);
    for (int64_t k = 0; k < n; k++) chirp(k, n, P->ch + 2 * k, P->ch + 2 * k + 1);
    double *b = (double *)xmalloc(16 * M);
    memset(b, 0, 16 * M);
    for (int64_t k = 0; k < n; k++) {
        b[2 * k] = P->ch[2 * k] / M; b[2 * k + 1] = -P->ch[2 * k + 1] / M;  // conj(chirp)/M
        if (k) { b[2 * (M - k)] = b[2 * k]; b[2 * (M - k) + 1] = b[2 * k + 1]; }
    }
    P->Bh = (double *)xmalloc(16 * M);
    fe_exec(P->f, b, P->Bh);
    free(b);
    P->a = (double *)xmalloc(16 * M); P->A = (double *)xmalloc(16 * M);
    return P;
}
static void blu_exec(const blu_plan *P, const double *x, double *y) {
    int64_t n = P->n, M = P->M;
    double *a = P->a, *A = P->A;
    int64_t k = 0;
    for (; k + 1 < n; k += 2) VSTORE(a + 2 * k, vcmul(VLOADU(x + 2 * k), VLOAD(P->ch + 2 * k)));
    for (; k < n; k++) { cd v = cmul((cd){x[2 * k], x[2 * k + 1]}, (cd){P->ch[2 * k], P->ch[2 * k + 1]}); a[2 * k] = v.re; a[2 * k + 1] = v.im; }
    memset(a + 2 * n, 0, 16 * (M - n));
    fe_exec(P->f, a, A);
    // conj(A * Bh) -> a  (IFFT via conj trick)
    const V cm = _mm256_set_pd(-0.0, 0.0, -0.0, 0.0);
    for (int64_t i = 0; i < M; i += 2) VSTORE(a + 2 * i, _mm256_xor_pd(vcmul(VLOAD(A + 2 * i), VLOAD(P->Bh + 2 * i)), cm));
    fe_exec(P->f, a, A);
    // y_k = conj(A_k) * ch_k
    for (k = 0; k + 1 < n; k += 2) VSTOREU(y + 2 * k, vcmulc(VLOAD(P->ch + 2 * k), VLOAD(A + 2 * k)));
    for (; k < n; k++) { cd v = cmul((cd){A[2 * k], -A[2 * k + 1]}, (cd){P->ch[2 * k], P->ch[2 * k + 1]}); y[2 * k] = v.re; y[2 * k + 1] = v.im; }
}
static void blu_free(blu_plan *P) { fe_free(P->f); free(P->ch); free(P->Bh); free(P->a); free(P->A); free(P); }

// ---------------- Rader ----------------
static int64_t powmod(int64_t b, int64_t e, int64_t m) {
    __int128 r = 1, x = b % m;
    while (e) { if (e & 1) r = r * x % m; x = x * x % m; e >>= 1; }
    return (int64_t)r;
}
static int is_prime(int64_t n) {
    if (n < 2) return 0;
    for (int64_t d = 2; d * d <= n; d++) if (n % d == 0) return 0;
    return 1;
}
static int64_t primitive_root(int64_t p) {
    int64_t L = p - 1, fac[64]; int nf = 0, m = L;
    for (int64_t d = 2; d * d <= m; d++) if (m % d == 0) { fac[nf++] = d; while (m % d == 0) m /= d; }
    if (m > 1) fac[nf++] = m;
    for (int64_t g = 2;; g++) {
        int ok = 1;
        for (int i = 0; i < nf && ok; i++) if (powmod(g, L / fac[i], p) == 1) ok = 0;
        if (ok) return g;
    }
}
typedef struct { int64_t n, L, M; fe_plan *f; int64_t *gp, *gi; double *Bh, *a, *A; } rad_plan;
static rad_plan *rad_create(int64_t n, int pow2only) {
    if (!is_prime(n) || n < 3) return NULL;
    rad_plan *P = (rad_plan *)calloc(1, sizeof(rad_plan));
    int64_t L = n - 1;
    P->n = n; P->L = L;
    P->M = (!pow2only && is_smooth(L)) ? L : next_smooth(2 * L - 1, pow2only);
    int64_t M = P->M;
    P->f = fe_create(M);
    int64_t g = primitive_root(n), gin = powmod(g, n - 2, n);
    P->gp = (int64_t *)xmalloc(8 * L); P->gi = (int64_t *)xmalloc(8 * L);
    int64_t v = 1, w = 1;
    for (int64_t q = 0; q < L; q++) { P->gp[q] = v; P->gi[q] = w; v = v * g % n; w = w * gin % n; }
    double *b = (double *)xmalloc(16 * M);
    memset(b, 0, 16 * M);
    for (int64_t q = 0; q < L; q++) {
        double re, im; twiddle(P->gi[q], n, &re, &im);  // omega^{g^{-q}}
        b[2 * q] = re / M; b[2 * q + 1] = im / M;
        if (M != L && q) { b[2 * (M - L + q)] = re / M; b[2 * (M - L + q) + 1] = im / M; }
    }
    P->Bh = (double *)xmalloc(16 * M);
    fe_exec(P->f, b, P->Bh);
    free(b);
    P->a = (double *)xmalloc(16 * M); P->A = (double *)xmalloc(16 * M);
    return P;
}
static void rad_exec(const rad_plan *P, const double *x, double *y) {
    int64_t n = P->n, L = P->L, M = P->M;
    double *a = P->a, *A = P->A;
    for (int64_t q = 0; q < L; q++) { a[2 * q] = x[2 * P->gp[q]]; a[2 * q + 1] = x[2 * P->gp[q] + 1]; }
    if (M > L) memset(a + 2 * L, 0, 16 * (M - L));
    fe_exec(P->f, a, A);
    const V cm = _mm256_set_pd(-0.0, 0.0, -0.0, 0.0);
    for (int64_t i = 0; i + 1 < M; i += 2) VSTORE(a + 2 * i, _mm256_xor_pd(vcmul(VLOAD(A + 2 * i), VLOAD(P->Bh + 2 * i)), cm));
    if (M & 1) { cd v = cmul((cd){A[2 * (M - 1)], A[2 * (M - 1) + 1]}, (cd){P->Bh[2 * (M - 1)], P->Bh[2 * (M - 1) + 1]}); a[2 * (M - 1)] = v.re; a[2 * (M - 1) + 1] = -v.im; }
    fe_exec(P->f, a, A);
    double s0r = 0, s0i = 0;
    for (int64_t k = 0; k < n; k++) { s0r += x[2 * k]; s0i += x[2 * k + 1]; }
    y[0] = s0r; y[1] = s0i;
    double x0r = x[0], x0i = x[1];
    for (int64_t p = 0; p < L; p++) { int64_t o = P->gi[p]; y[2 * o] = x0r + A[2 * p]; y[2 * o + 1] = x0i - A[2 * p + 1]; }
}
static void rad_free(rad_plan *P) { fe_free(P->f); free(P->gp); free(P->gi); free(P->Bh); free(P->a); free(P->A); free(P); }

// ---------------- Gaussian resampling (HvdH) ----------------
// Vector exp for |x| < ~700, rel. error ~1e-16 (Cody-Waite + degree-13 Taylor/Horner).
static inline __m256d exp4(__m256d x) {
    const __m256d l2e = _mm256_set1_pd(1.4426950408889634), c1 = _mm256_set1_pd(6.93145751953125e-1),
                  c2 = _mm256_set1_pd(1.42860682030941723212e-6);
    __m256d k = _mm256_round_pd(_mm256_mul_pd(x, l2e), _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
    __m256d r = _mm256_fnmadd_pd(k, c1, x);
    r = _mm256_fnmadd_pd(k, c2, r);
    static const double co[14] = {1.0 / 6227020800.0, 1.0 / 479001600.0, 1.0 / 39916800.0, 1.0 / 3628800.0, 1.0 / 362880.0,
                                  1.0 / 40320.0, 1.0 / 5040.0, 1.0 / 720.0, 1.0 / 120.0, 1.0 / 24.0, 1.0 / 6.0, 0.5, 1.0, 1.0};
    __m256d p = _mm256_set1_pd(co[0]);
    for (int i = 1; i < 14; i++) p = _mm256_fmadd_pd(p, r, _mm256_set1_pd(co[i]));
    __m128i ki = _mm256_cvtpd_epi32(k);
    __m256i e = _mm256_slli_epi64(_mm256_add_epi64(_mm256_cvtepi32_epi64(ki), _mm256_set1_epi64x(1023)), 52);
    return _mm256_mul_pd(p, _mm256_castsi256_pd(e));
}

typedef struct {
    int64_t s, t, T, w;     // input length, resampled length, taps (=2w)
    int iters;
    double beta;
    fe_plan *f;
    double *E;              // exp(-beta i^2) for taps, i = 0..T-1 relative to k0 (stored with offset)
    double *D;              // per output q: 1/(t * ghat(q))  (indexed by q mod s)
    double *Rp, *Rm;        // alias ratios ghat(q +- t)/ghat(q)
    int64_t *Ip, *Im;       // alias partner indices (q +- t) mod s
    double *uext, *v, *V, *U2;
    int nrng; int64_t rlo[2], rhi[2], rsh[2]; double *rr[2];   // significant alias ranges
} gau_plan;

static gau_plan *gau_create(int64_t s, double Lnats, double delta, int iters, int pow2only) {
    gau_plan *P = (gau_plan *)calloc(1, sizeof(gau_plan));
    P->s = s; P->iters = iters;
    P->t = next_smooth((int64_t)ceil((1.0 + delta) * s), pow2only);
    int64_t t = P->t;
    P->beta = M_PI * M_PI / (4.0 * Lnats);
    P->w = (int64_t)ceil(sqrt(39.2 / P->beta));  // exp(-beta w^2) < 1e-17
    P->T = 2 * P->w; if (P->T % 4) P->T += 4 - P->T % 4;
    P->f = fe_create(t);
    // tap i corresponds to z = f - i with f in [w-1, w); store exp(-beta*(i - (w-1))^2)?  We use the
    // separable form exp(-beta (f-i)^2) = exp(-beta f^2) exp(2 beta f i) exp(-beta i^2).
    P->E = (double *)xmalloc(sizeof(double) * P->T);
    for (int64_t i = 0; i < P->T; i++) P->E[i] = exp(-P->beta * (double)(i * i));
    // spectrum of the periodised spreading function: ghat(l) ∝ exp(-pi^2 l^2 / (beta s^2)); constant cancels
    // except for the overall scale: v_j = sum_k u_k phi(c_j - k), phi(z)=exp(-beta z^2)
    // V_p = t * sum_{l = p mod t} (1/s) sqrt(pi/beta) exp(-pi^2 l^2/(beta s^2)) U_{l mod s}
    double scale = (double)t / (double)s * sqrt(M_PI / P->beta);
    P->D = (double *)xmalloc(sizeof(double) * s);
    P->Rp = (double *)xmalloc(sizeof(double) * s); P->Rm = (double *)xmalloc(sizeof(double) * s);
    P->Ip = (int64_t *)xmalloc(8 * s); P->Im = (int64_t *)xmalloc(8 * s);
    double gam = M_PI * M_PI / (P->beta * (double)s * (double)s);
    for (int64_t qi = 0; qi < s; qi++) {
        int64_t q = qi <= s / 2 ? qi : qi - s;            // centred representative, q in (-s/2, s/2]
        if (2 * q == s) q = -q;                            // keep symmetric range
        double g0 = exp(-gam * (double)q * q);
        P->D[qi] = 1.0 / (scale * g0);
        P->Rp[qi] = exp(-gam * ((double)(q + t) * (q + t) - (double)q * q));
        P->Rm[qi] = exp(-gam * ((double)(q - t) * (q - t) - (double)q * q));
        P->Ip[qi] = (((q + t) % s) + s) % s;
        P->Im[qi] = (((q - t) % s) + s) % s;
    }
    // significant alias ranges: index qi where ratio > 1e-18; partner shift (q +- t) mod s as qi offset
    P->nrng = 0;
    for (int side = 0; side < 2; side++) {
        double *R = side ? P->Rm : P->Rp;
        int64_t lo = s, hi = 0;
        for (int64_t qi = 0; qi < s; qi++) if (R[qi] > 1e-18) { if (qi < lo) lo = qi; hi = qi + 1; }
        if (lo < hi) {
            int r = P->nrng++;
            P->rlo[r] = lo; P->rhi[r] = hi; P->rr[r] = R;
            P->rsh[r] = ((side ? P->Im[lo] : P->Ip[lo]) - lo) % s;
            for (int64_t qi = lo; qi < hi; qi++) {  // verify constant shift
                int64_t pq = qi + P->rsh[r]; pq = ((pq % s) + s) % s;
                if (pq != (side ? P->Im[qi] : P->Ip[qi])) { fprintf(stderr, "gauss: non-constant alias shift\n"); exit(1); }
            }
        }
    }
    P->uext = (double *)xmalloc(16 * (s + 2 * P->T + 8));  // split re/im halves
    P->v = (double *)xmalloc(16 * t); P->V = (double *)xmalloc(16 * t);
    P->U2 = (double *)xmalloc(16 * s);
    return P;
}

#ifdef GAU_PROF
static double gp_t[4];
#define GP_MARK(i) do { double _t = now_sec(); gp_t[i] += _t - gp_last; gp_last = _t; } while (0)
#else
#define GP_MARK(i) do {} while (0)
#endif
static void gau_exec(const gau_plan *P, const double *x, double *y) {
#ifdef GAU_PROF
    double gp_last = now_sec();
#endif
    const int64_t s = P->s, t = P->t, T = P->T, w = P->w;
    const double beta = P->beta;
    // periodic halo in split (re[], im[]) format: ur[T + k] = Re x[k mod s] for k in [-T, s+T)
    double *ur = P->uext + T, *ui = P->uext + (s + 2 * T + 8) + T;
    {
        int64_t k = 0;
        for (; k + 4 <= s; k += 4) {
            __m256d a = VLOADU(x + 2 * k), b = VLOADU(x + 2 * k + 4);   // r0 i0 r1 i1 | r2 i2 r3 i3
            __m256d re = _mm256_permute4x64_pd(_mm256_unpacklo_pd(a, b), 0xD8);
            __m256d im = _mm256_permute4x64_pd(_mm256_unpackhi_pd(a, b), 0xD8);
            _mm256_storeu_pd(ur + k, re); _mm256_storeu_pd(ui + k, im);
        }
        for (; k < s; k++) { ur[k] = x[2 * k]; ui[k] = x[2 * k + 1]; }
        for (k = 1; k <= T; k++) {
            int64_t km = ((-k) % s + s) % s, kp = (s - 1 + k) % s;
            ur[-k] = x[2 * km]; ui[-k] = x[2 * km + 1];
            ur[s - 1 + k] = x[2 * kp]; ui[s - 1 + k] = x[2 * kp + 1];
        }
    }
    // resample: v_j = sum_i exp(-beta (f_j - i)^2) u[k0_j + i],  c_j = j s / t, k0_j = floor(c_j) - (w - 1)
    double *v = P->v;
    int64_t kc = 0, rem = 0;          // j*s = kc*t + rem, maintained incrementally (s < t)
    const double inv_t = 1.0 / (double)t;
    enum { NB = 64 };
    double fv[NB], Av[NB], Bv[NB];
    int64_t k0v[NB];
    for (int64_t jb = 0; jb < t; jb += NB) {
        const int64_t nb = t - jb < NB ? t - jb : NB;
        // pass 1: offsets and the two exponentials per output (independent -> pipelined exp4)
        for (int64_t l = 0; l < nb; l++) {
            k0v[l] = kc - (w - 1);
            fv[l] = (double)(w - 1) + (double)rem * inv_t;
            rem += s; if (rem >= t) { rem -= t; kc++; }
        }
        for (int64_t l = nb; l < NB; l++) { fv[l] = fv[0]; k0v[l] = k0v[0]; }
        const __m256d mb = _mm256_set1_pd(-beta), tb = _mm256_set1_pd(2.0 * beta);
        for (int64_t l = 0; l < NB; l += 4) {
            __m256d f = _mm256_loadu_pd(fv + l);
            _mm256_storeu_pd(Av + l, exp4(_mm256_mul_pd(_mm256_mul_pd(f, f), mb)));
            _mm256_storeu_pd(Bv + l, exp4(_mm256_mul_pd(f, tb)));
        }
        // pass 2: spread, 4 outputs interleaved (independent weight / accumulator chains)
        for (int64_t l0 = 0; l0 < nb; l0 += 4) {
            __m256d P0[4], B4[4], ar[4], ai[4];
            const double *pr[4], *pi[4];
            for (int l = 0; l < 4; l++) {
                const double b = Bv[l0 + l], b2 = b * b;
                P0[l] = _mm256_mul_pd(_mm256_set1_pd(Av[l0 + l]), _mm256_setr_pd(1.0, b, b2, b2 * b));
                B4[l] = _mm256_set1_pd(b2 * b2);
                ar[l] = ai[l] = _mm256_setzero_pd();
                pr[l] = ur + k0v[l0 + l]; pi[l] = ui + k0v[l0 + l];
            }
            for (int64_t i = 0; i < T; i += 4) {
                const __m256d E = _mm256_loadu_pd(P->E + i);
                for (int l = 0; l < 4; l++) {
                    __m256d wt = _mm256_mul_pd(P0[l], E);
                    ar[l] = _mm256_fmadd_pd(wt, _mm256_loadu_pd(pr[l] + i), ar[l]);
                    ai[l] = _mm256_fmadd_pd(wt, _mm256_loadu_pd(pi[l] + i), ai[l]);
                    P0[l] = _mm256_mul_pd(P0[l], B4[l]);
                }
            }
            // horizontal sums: lanes -> (re, im) per output
            __m256d h0 = _mm256_hadd_pd(ar[0], ai[0]), h1 = _mm256_hadd_pd(ar[1], ai[1]);   // (r01, i01, r23, i23)
            __m256d h2 = _mm256_hadd_pd(ar[2], ai[2]), h3 = _mm256_hadd_pd(ar[3], ai[3]);
            __m256d s01 = _mm256_add_pd(_mm256_permute2f128_pd(h0, h1, 0x20), _mm256_permute2f128_pd(h0, h1, 0x31));
            __m256d s23 = _mm256_add_pd(_mm256_permute2f128_pd(h2, h3, 0x20), _mm256_permute2f128_pd(h2, h3, 0x31));
            if (l0 + 4 <= nb) { VSTOREU(v + 2 * (jb + l0), s01); VSTOREU(v + 2 * (jb + l0 + 2), s23); }
            else {
                double tmp[8]; _mm256_storeu_pd(tmp, s01); _mm256_storeu_pd(tmp + 4, s23);
                for (int l = 0; l < nb - l0; l++) { v[2 * (jb + l0 + l)] = tmp[2 * l]; v[2 * (jb + l0 + l) + 1] = tmp[2 * l + 1]; }
            }
        }
    }
    GP_MARK(0);
    fe_exec(P->f, v, P->V);
    GP_MARK(1);
    // deconvolve: U_q = V_{q mod t} * D_q
    const double *Vv = P->V;
    // q in [0, s/2) -> V_q ; q in [s/2, s) (negative frequencies q - s) -> V_{t - (s - q)}
    const int64_t hs = (s % 2 == 0) ? s / 2 : s / 2 + 1;
    for (int64_t qi = 0; qi < hs; qi++) {
        __m128d d = _mm_set1_pd(P->D[qi]);
        _mm_storeu_pd(y + 2 * qi, _mm_mul_pd(_mm_loadu_pd(Vv + 2 * qi), d));
    }
    for (int64_t qi = hs; qi < s; qi++) {
        __m128d d = _mm_set1_pd(P->D[qi]);
        _mm_storeu_pd(y + 2 * qi, _mm_mul_pd(_mm_loadu_pd(Vv + 2 * (t - s + qi)), d));
    }
    GP_MARK(2);
    // Neumann iterations: U = b - E U,  (E U)_q = Rp_q U_{q+t} + Rm_q U_{q-t}  (indices mod s).
    // Only entries with a non-negligible ratio are visited ([lo,hi) ranges precomputed); the partner
    // index is a constant shift, so the sweep is streaming.  b is kept in U2, ping-pong via v.
    if (P->iters > 0) {
        double *b = P->U2, *nxt = P->v;
        memcpy(b, y, 16 * s);
        double *cur = y;
        for (int it = 0; it < P->iters; it++) {
            memcpy(nxt, b, 16 * s);
            for (int r = 0; r < P->nrng; r++) {
                const int64_t lo = P->rlo[r], hi = P->rhi[r], sh = P->rsh[r];
                const double *R = P->rr[r];
                for (int64_t q = lo; q < hi; q++) {
                    int64_t pq = q + sh; if (pq >= s) pq -= s; else if (pq < 0) pq += s;
                    nxt[2 * q] -= R[q] * cur[2 * pq]; nxt[2 * q + 1] -= R[q] * cur[2 * pq + 1];
                }
            }
            double *tq = cur; cur = nxt; nxt = tq;
        }
        if (cur != y) memcpy(y, cur, 16 * s);
    }
    GP_MARK(3);
}
static void gau_free(gau_plan *P) {
    fe_free(P->f); free(P->E); free(P->D); free(P->Rp); free(P->Rm); free(P->Ip); free(P->Im);
    free(P->uext); free(P->v); free(P->V); free(P->U2); free(P);
}
