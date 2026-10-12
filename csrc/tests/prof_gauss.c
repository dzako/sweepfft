// SPDX-License-Identifier: GPL-2.0-or-later
#define GAU_PROF
#include "../dft/arbitrary.h"
int main(int argc, char **argv) {
    int64_t s = argc > 1 ? atoll(argv[1]) : 1000003;
    gau_plan *P = gau_create(s, 7, 0.25, argc > 2 ? atoi(argv[2]) : 4, 0);
    printf("s=%ld t=%ld T=%ld w=%ld\n", s, P->t, P->T, P->w);
    double *x = xmalloc(16 * s), *y = xmalloc(16 * s);
    uint64_t seed = 1; for (int64_t i = 0; i < 2 * s; i++) x[i] = rng_unif(&seed);
    gau_exec(P, x, y);
    double t0 = now_sec(); for (int i = 0; i < 5; i++) gau_exec(P, x, y); double tall = (now_sec() - t0) / 5;
    t0 = now_sec(); for (int i = 0; i < 5; i++) fe_exec(P->f, P->v, P->V); double tfft = (now_sec() - t0) / 5;
    // smooth fft vs pow2 fft of similar size
    int64_t m2 = 1; while (m2 < P->t) m2 <<= 1;
    fe_plan *f2 = fe_create(m2); double *a = xmalloc(16 * m2), *b = xmalloc(16 * m2); memset(a, 0, 16 * m2);
    fe_exec(f2, a, b); t0 = now_sec(); for (int i = 0; i < 5; i++) fe_exec(f2, a, b); double tp2 = (now_sec() - t0) / 5;
    printf("total %.2f ms, fft(t=%ld) %.2f ms [%.1f GF], fft(pow2 %ld) %.2f ms, rest %.2f ms\n", tall * 1e3, P->t, tfft * 1e3,
           5.0 * P->t * log2(P->t) / tfft / 1e9, m2, tp2 * 1e3, (tall - tfft) * 1e3);
    memset(gp_t, 0, sizeof gp_t); gau_exec(P, x, y);
    printf("halo+spread %.2f ms | fft %.2f ms | deconv %.2f ms | neumann %.2f ms\n", gp_t[0]*1e3, gp_t[1]*1e3, gp_t[2]*1e3, gp_t[3]*1e3);
    return 0;
}
