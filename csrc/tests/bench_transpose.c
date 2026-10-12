// SPDX-License-Identifier: GPL-2.0-or-later
// I1-toy and I14: address-interchange strategies on a RAM.
//
// I1-toy: transpose an N x N complex matrix.
//   naive      : out[j][i] = in[i][j], row-wise loop (strided writes)
//   blocked    : out-of-place, 16x16 tiles (+ NT stores option)
//   inplace    : in-place tile-pair swaps
//   shear3     : the paper's identity  D <- D - H,  H <- H + D,  D <- H - D  realised as three data
//                passes on (h, d) addresses: row rotation, column rotation, row reverse-rotation.
//                In place with O(N * strip) scratch -- the "catalytic"/restoring flavour of §3.
// I14: permute axes of an A x B x C tensor (a,b,c) -> (c,b,a):
//   chain3     : three adjacent swaps (a,b,c)->(b,a,c)->(b,c,a)->(c,b,a)       [d^2 routing]
//   grouped2   : (a,(b,c)) -> ((b,c),a) as one 2-D transpose, then (b,c,a)->(c,b,a) batched over a
//   direct1    : single blocked pass computing out[c][b][a] = in[a][b][c]       [non-adjacent swap]
#include "../common/common.h"

typedef struct { double re, im; } C;

static void tr_naive(const C *in, C *out, int64_t R, int64_t Cc) {
    for (int64_t i = 0; i < R; i++) for (int64_t j = 0; j < Cc; j++) out[j * R + i] = in[i * Cc + j];
}
static void tr_blocked(const C *in, C *out, int64_t R, int64_t Cc, int nt) {
    const int64_t T = 16;
    for (int64_t i0 = 0; i0 < R; i0 += T)
        for (int64_t j0 = 0; j0 < Cc; j0 += T) {
            int64_t im = i0 + T < R ? i0 + T : R, jm = j0 + T < Cc ? j0 + T : Cc;
            for (int64_t j = j0; j < jm; j++) {
                if (nt && im - i0 == T) {
                    for (int64_t i = i0; i < im; i += 2) {
                        __m256d v = _mm256_set_pd(in[(i + 1) * Cc + j].im, in[(i + 1) * Cc + j].re, in[i * Cc + j].im, in[i * Cc + j].re);
                        _mm256_stream_pd((double *)&out[j * R + i], v);
                    }
                } else
                    for (int64_t i = i0; i < im; i++) out[j * R + i] = in[i * Cc + j];
            }
        }
    if (nt) _mm_sfence();
}
static void tr_inplace(C *a, int64_t N) {
    const int64_t T = 16;
    for (int64_t i0 = 0; i0 < N; i0 += T)
        for (int64_t j0 = i0; j0 < N; j0 += T)
            for (int64_t i = i0; i < i0 + T; i++)
                for (int64_t j = (j0 == i0 ? i + 1 : j0); j < j0 + T; j++) { C t = a[i * N + j]; a[i * N + j] = a[j * N + i]; a[j * N + i] = t; }
}
// shear passes; N power of two so "mod N" is a mask
static void shear_rows(C *a, int64_t N, C *row, int rev) {
    // rev=0: new[h][(d - h)] = old[h][d]  ;  rev=1: new[h][(h - d)] = old[h][d]
    for (int64_t h = 0; h < N; h++) {
        C *r = a + h * N;
        if (!rev) { for (int64_t d = 0; d < N; d++) row[(d - h) & (N - 1)] = r[d]; }
        else { for (int64_t d = 0; d < N; d++) row[(h - d) & (N - 1)] = r[d]; }
        memcpy(r, row, sizeof(C) * N);
    }
}
static void shear_cols(C *a, int64_t N, C *strip, int64_t S) {
    // new[(h + d)][d] = old[h][d], via strips of S columns gathered into cache
    for (int64_t d0 = 0; d0 < N; d0 += S) {
        for (int64_t h = 0; h < N; h++) memcpy(strip + h * S, a + h * N + d0, sizeof(C) * S);
        for (int64_t h = 0; h < N; h++)
            for (int64_t s = 0; s < S; s++) a[((h + d0 + s) & (N - 1)) * N + d0 + s] = strip[h * S + s];
    }
}
static void tr_shear3(C *a, int64_t N, C *row, C *strip, int64_t S) {
    shear_rows(a, N, row, 0);
    shear_cols(a, N, strip, S);
    shear_rows(a, N, row, 1);
}

// ---- I14 tensor permutations ----
static void perm_direct(const C *in, C *out, int64_t A, int64_t B, int64_t Cc) {
    // out[c][b][a] = in[a][b][c]; tile over (a, c), b outer
    const int64_t T = 16;
    for (int64_t b = 0; b < B; b++)
        for (int64_t a0 = 0; a0 < A; a0 += T)
            for (int64_t c0 = 0; c0 < Cc; c0 += T)
                for (int64_t c = c0; c < c0 + T && c < Cc; c++)
                    for (int64_t a = a0; a < a0 + T && a < A; a++) out[(c * B + b) * A + a] = in[(a * B + b) * Cc + c];
}
static void batch_tr(const C *in, C *out, int64_t batch, int64_t R, int64_t Cc) {
    for (int64_t k = 0; k < batch; k++) tr_blocked(in + k * R * Cc, out + k * R * Cc, R, Cc, 0);
}
// transpose of (X, Y) where each element is a contiguous block of E complex
static void tr_blockelem(const C *in, C *out, int64_t X, int64_t Y, int64_t E) {
    for (int64_t x = 0; x < X; x++) for (int64_t y = 0; y < Y; y++) memcpy(out + (y * X + x) * E, in + (x * Y + y) * E, sizeof(C) * E);
}
static void perm_chain3(const C *in, C *out, C *tmp, int64_t A, int64_t B, int64_t Cc) {
    tr_blockelem(in, tmp, A, B, Cc);   // (a,b,c) -> (b,a,c)
    batch_tr(tmp, out, B, A, Cc);      // (b,a,c) -> (b,c,a)
    tr_blockelem(out, tmp, B, Cc, A);  // (b,c,a) -> (c,b,a)
    memcpy(out, tmp, sizeof(C) * A * B * Cc);  // result back in out (copy charged: chains need ping-pong)
}
static void perm_grouped2(const C *in, C *out, C *tmp, int64_t A, int64_t B, int64_t Cc) {
    tr_blocked(in, tmp, A, B * Cc, 0);  // (a,(b,c)) -> ((b,c),a)
    tr_blockelem(tmp, out, B, Cc, A);   // (b,c,a) -> (c,b,a)
}

static double timeit(void (*f)(void *), void *ctx) {
    double best = 1e9;
    for (int r = 0; r < 5; r++) { double t = now_sec(); f(ctx); t = now_sec() - t; if (t < best) best = t; }
    return best;
}

typedef struct { C *a, *b, *t, *row, *strip; int64_t N, A, B, Cc, S; int which; } ctx_t;
static void run_tr(void *v) {
    ctx_t *c = v;
    switch (c->which) {
    case 0: tr_naive(c->a, c->b, c->N, c->N); break;
    case 1: tr_blocked(c->a, c->b, c->N, c->N, 0); break;
    case 2: tr_blocked(c->a, c->b, c->N, c->N, 1); break;
    case 3: tr_inplace(c->a, c->N); break;
    case 4: tr_shear3(c->a, c->N, c->row, c->strip, c->S); break;
    case 5: perm_chain3(c->a, c->b, c->t, c->A, c->B, c->Cc); break;
    case 6: perm_grouped2(c->a, c->b, c->t, c->A, c->B, c->Cc); break;
    case 7: perm_direct(c->a, c->b, c->A, c->B, c->Cc); break;
    }
}

int main(void) {
    printf("test,variant,shape,bytes,time_ms,GBps_rw\n");
    const char *tn[] = {"naive", "blocked", "blocked_nt", "inplace_tiles", "shear3_inplace"};
    for (int64_t N = 256; N <= 8192; N *= 2) {
        int64_t n = N * N;
        ctx_t c = {.a = xmalloc(sizeof(C) * n), .b = xmalloc(sizeof(C) * n), .row = xmalloc(sizeof(C) * N),
                   .strip = xmalloc(sizeof(C) * N * 16), .N = N, .S = 16};
        for (int64_t i = 0; i < n; i++) c.a[i] = (C){(double)i, -(double)i};
        // correctness of shear3 against blocked
        tr_blocked(c.a, c.b, N, N, 0);
        tr_shear3(c.a, N, c.row, c.strip, 16);
        if (memcmp(c.a, c.b, sizeof(C) * n)) { printf("shear3 WRONG at N=%ld\n", N); return 1; }
        tr_shear3(c.a, N, c.row, c.strip, 16);  // transpose back (involution)
        for (int w = 0; w < 5; w++) {
            c.which = w;
            double t = timeit(run_tr, &c);
            printf("I1,%s,%ldx%ld,%ld,%.3f,%.2f\n", tn[w], N, N, (long)(sizeof(C) * n), t * 1e3, 2.0 * sizeof(C) * n / t / 1e9);
        }
        free(c.a); free(c.b); free(c.row); free(c.strip);
    }
    const char *pn[] = {"chain3_adjacent", "grouped2", "direct1"};
    int64_t shapes[][3] = {{64, 64, 64}, {256, 64, 256}, {512, 32, 512}, {1024, 16, 1024}, {128, 128, 128}, {256, 256, 256}};
    for (size_t s = 0; s < sizeof shapes / sizeof shapes[0]; s++) {
        int64_t A = shapes[s][0], B = shapes[s][1], Cc = shapes[s][2], n = A * B * Cc;
        ctx_t c = {.a = xmalloc(sizeof(C) * n), .b = xmalloc(sizeof(C) * n), .t = xmalloc(sizeof(C) * n), .A = A, .B = B, .Cc = Cc};
        for (int64_t i = 0; i < n; i++) c.a[i] = (C){(double)i, 0};
        C *ref = xmalloc(sizeof(C) * n);
        perm_direct(c.a, ref, A, B, Cc);
        for (int w = 0; w < 3; w++) {
            c.which = 5 + w;
            run_tr(&c);
            if (memcmp(c.b, ref, sizeof(C) * n)) { printf("perm %s WRONG\n", pn[w]); return 1; }
            double t = timeit(run_tr, &c);
            printf("I14,%s,%ldx%ldx%ld,%ld,%.3f,%.2f\n", pn[w], A, B, Cc, (long)(sizeof(C) * n), t * 1e3, 2.0 * sizeof(C) * n / t / 1e9);
        }
        free(c.a); free(c.b); free(c.t); free(ref);
    }
    return 0;
}
