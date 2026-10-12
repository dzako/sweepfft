// SPDX-License-Identifier: GPL-2.0-or-later
// Baseline: ducc0 (successor of pocketfft), single-threaded, plan + scratch cached.
// ducc0's 1-D API is in-place, so exec includes one copy in -> out (a single streaming pass).
#include <algorithm>
#include <memory>
#include "ducc0/fft/fft1d_impl.h"
#include "ducc0/infra/aligned_array.h"
#include "impl.h"

using namespace ducc0;

struct ducc_h {
    std::unique_ptr<pocketfft_c<double>> p;
    aligned_array<Cmplx<double>> buf;
    size_t n;
};

static void *ducc_plan(int64_t n, const char *) {
    auto *h = new ducc_h;
    h->n = (size_t)n;
    h->p = std::make_unique<pocketfft_c<double>>((size_t)n);
    h->buf = aligned_array<Cmplx<double>>(h->p->bufsize());
    return h;
}
static void ducc_exec(void *hv, const double *in, double *out) {
    auto *h = (ducc_h *)hv;
    auto *o = reinterpret_cast<Cmplx<double> *>(out);
    if (in != out) std::copy(in, in + 2 * h->n, out);   // in-place mode (BENCH_INPLACE=1): no copy
    auto *res = h->p->exec(o, h->buf.data(), 1.0, true, 1);
    if (res != o) std::copy(res, res + h->n, o);
}
static void ducc_destroy(void *hv) { delete (ducc_h *)hv; }

extern "C" const dft_impl impl_ducc = {"ducc", ducc_plan, ducc_exec, ducc_destroy};
