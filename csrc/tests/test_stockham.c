// SPDX-License-Identifier: GPL-2.0-or-later
#include "../dft/stockham.h"
#include "../ref/ref.h"
int main(void) {
    int64_t sizes[] = {2,4,8,16,32,64,128,1024,4096,65536,3,5,6,12,15,24,60,105,240,1000,3*1024,49*16};
    int rmaxs[] = {2,4,8,16,32};
    uint64_t seed = 1;
    int fails = 0;
    for (size_t si = 0; si < sizeof(sizes)/sizeof(sizes[0]); si++) {
        int64_t n = sizes[si];
        double *in = xmalloc(16*n), *out = xmalloc(16*n), *w = xmalloc(16*n);
        for (int64_t i = 0; i < 2*n; i++) in[i] = rng_unif(&seed);
        qc *ref = malloc(sizeof(qc)*n); ref_dft(in, n, ref);
        for (int mode = 0; mode < 3; mode++) for (int ri = 0; ri < 5; ri++) {
            sh_plan *P = sh_plan_create(n, 1, rmaxs[ri], mode);
            if (!P) { printf("no plan n=%ld\n", n); continue; }
            sh_exec_oop(P, in, out, w);
            double rms, mx; ref_errors(out, ref, n, &rms, &mx);
            if (rms > 1e-14) { printf("FAIL n=%ld mode=%d rmax=%d rms=%.3g\n", n, mode, rmaxs[ri], rms); fails++; }
            sh_plan_free(P);
        }
        // batched
        int64_t B = 6;
        double *bi = xmalloc(16*n*B), *bo = xmalloc(16*n*B), *bw = xmalloc(16*n*B);
        for (int64_t b = 0; b < B; b++) for (int64_t i = 0; i < n; i++) { bi[2*(b+B*i)] = in[2*i]*(b+1); bi[2*(b+B*i)+1] = in[2*i+1]*(b+1); }
        sh_plan *P = sh_plan_create(n, B, 16, 0);
        sh_exec_oop(P, bi, bo, bw);
        double worst = 0;
        for (int64_t b = 0; b < B; b++) { double *t = xmalloc(16*n); for (int64_t i=0;i<n;i++){t[2*i]=bo[2*(b+B*i)]/(b+1);t[2*i+1]=bo[2*(b+B*i)+1]/(b+1);} double r,m; ref_errors(t,ref,n,&r,&m); if(r>worst)worst=r; free(t);}
        if (worst > 1e-14) { printf("FAIL batched n=%ld rms=%.3g\n", n, worst); fails++; }
        sh_plan_free(P); free(bi); free(bo); free(bw);
        free(in); free(out); free(w); free(ref);
    }
    printf("%s (%d failures)\n", fails ? "FAILED" : "ALL OK", fails);
    return fails != 0;
}
