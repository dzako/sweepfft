# SPDX-License-Identifier: GPL-2.0-or-later
"""Toeplitz-representation tests T1-T3 (plan section "Toeplitz representation tests").

T1  representation correctness (mpmath, 40 digits):
    a) Bluestein   F = D T D,  D = diag(exp(-i pi k^2/n)),  T_{jk} = exp(+i pi (j-k)^2/n)  (Toeplitz)
    b) Rader       prime p: the DFT on nonzero indices, permuted by a primitive root, is a circulant
    c) HvdH Gaussian resampling identity used by csrc/dft/arbitrary.h:
           F_t G = A F_s,   G_{jk} = sum_m exp(-beta (j s/t - k - m s)^2)
           A_{pq} = (t/s) sqrt(pi/beta) sum_{l = p (t), l = q (s)} exp(-pi^2 l^2/(beta s^2))
    d) PR #5 completing-the-square: (sigma a - b)^2 = sigma theta a^2 + sigma (a-b)^2 - theta b^2,
       theta = sigma - 1  =>  G = D1 T D2 (diag x Toeplitz x diag) with exponentially graded D1, D2
T2  Toeplitz matvec back-ends for G in double precision: direct banded vs blocked chirp-Toeplitz-chirp
    (PR #5/#23 "bulk resampling") vs circulant embedding (FFT); error vs block size, flop counts.
T3  inverting the resampling: least-squares G u = v by Neumann series, CG on normal equations with a
    circulant (Strang) preconditioner, and dense Cholesky; iterations vs (L, delta), condition numbers.
Run:  uv run tests/test_toeplitz.py   (writes results/toeplitz_T*.csv)
"""
import math
import time
from pathlib import Path

import warnings

import mpmath as mp
import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve, toeplitz

mp.mp.dps = 40
warnings.filterwarnings("ignore", category=RuntimeWarning)
OUT = Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(exist_ok=True)


def maxabs(M):
    return max(abs(x) for x in M)


# ------------------------------------------------------------------ T1
def t1_bluestein(n):
    w = lambda k: mp.exp(-2j * mp.pi * k / n)
    worst = mp.mpf(0)
    for j in range(n):
        for k in range(n):
            F = w(j * k)
            Dj, Dk = mp.exp(-1j * mp.pi * j * j / n), mp.exp(-1j * mp.pi * k * k / n)
            T = mp.exp(1j * mp.pi * (j - k) ** 2 / n)
            worst = max(worst, abs(F - Dj * T * Dk))
    return float(worst)


def primitive_root(p):
    L = p - 1
    fac = [q for q in range(2, L + 1) if L % q == 0 and all(q % r for r in range(2, int(q ** 0.5) + 1))]
    for g in range(2, p):
        if all(pow(g, L // q, p) != 1 for q in fac):
            return g


def t1_rader(p):
    g = primitive_root(p)
    gi = pow(g, p - 2, p)
    L = p - 1
    # M_{a,b} = F[g^{-a}, g^{b}]  must depend only on (a + b) mod L ... use b' = -b: circulant in (a - b)
    worst = mp.mpf(0)
    first = [mp.exp(-2j * mp.pi * (pow(gi, a, p) * 1) / p) for a in range(L)]
    for a in range(L):
        for b in range(L):
            Fab = mp.exp(-2j * mp.pi * (pow(gi, a, p) * pow(g, b, p) % p) / p)
            worst = max(worst, abs(Fab - first[(a - b) % L]))
    return float(worst)


def gauss_G(s, t, beta, mpm=False):
    ex = mp.exp if mpm else math.exp
    G = [[0] * s for _ in range(t)]
    for j in range(t):
        for k in range(s):
            acc = 0
            for m in range(-3, 4):
                z = mp.mpf(j) * s / t - k - m * s if mpm else j * s / t - k - m * s
                acc += ex(-beta * z * z)
            G[j][k] = acc
    return G


def t1_resampling(s, t, Lnats):
    beta = mp.pi ** 2 / (4 * Lnats)
    G = gauss_G(s, t, beta, mpm=True)
    gam = mp.pi ** 2 / (beta * s * s)
    worst = mp.mpf(0)
    for p in range(t):
        for q in range(s):
            lhs = mp.mpf(0)
            # (F_t G F_s^{-1})_{pq}
            for j in range(t):
                for k in range(s):
                    lhs += mp.exp(-2j * mp.pi * j * p / t) * G[j][k] * mp.exp(2j * mp.pi * k * q / s) / s
            rhs = mp.mpf(0)
            for l in range(-6 * t, 6 * t + 1):
                if (l - p) % t == 0 and (l - q) % s == 0:
                    rhs += mp.exp(-gam * l * l)
            rhs *= mp.mpf(t) / s * mp.sqrt(mp.pi / beta)
            worst = max(worst, abs(lhs - rhs))
    return float(worst)


def t1_complete_square(trials=200):
    rng = np.random.default_rng(0)
    worst = 0.0
    for _ in range(trials):
        sig, a, b = (mp.mpf(float(x)) for x in rng.uniform(-3, 3, 3))
        th = sig - 1
        worst = max(worst, float(abs((sig * a - b) ** 2 - (sig * th * a * a + sig * (a - b) ** 2 - th * b * b))))
    return worst


# ------------------------------------------------------------------ T2
def G_banded(u, s, t, beta, w):
    """direct banded resampling (what the C kernel does): v_j = sum_{|c_j - k| < w} exp(-beta (c_j-k)^2) u_k"""
    j = np.arange(t)
    c = j * s / t
    k0 = np.floor(c).astype(np.int64) - (w - 1)
    v = np.zeros(t, complex)
    for i in range(2 * w):
        k = k0 + i
        v += np.exp(-beta * (c - k) ** 2) * u[k % s]
    return v


def G_blocked_toeplitz(u, s, t, beta, w, B):
    """PR #5 form, blockwise: for a block of B outputs starting at j0 and the input window feeding it,
    exp(-beta (sigma a - b)^2) = D1(a) T(a-b) D2(b) with a = j - j0, b = k - k0 local coordinates.
    The Toeplitz product is done as a correlation via FFT (circulant embedding)."""
    sig = s / t
    th = sig - 1.0
    v = np.zeros(t, complex)
    for j0 in range(0, t, B):
        jb = np.arange(j0, min(j0 + B, t))
        c0 = j0 * s / t
        k0 = int(math.floor(c0)) - (w - 1)
        nk = int(math.ceil(len(jb) * sig)) + 2 * w + 1
        kk = np.arange(k0, k0 + nk)
        # local: sigma a - b = c_j - k - delta,  with a = j - j0, b = k - k0, delta = k0 - c0
        delta = k0 - c0
        a = jb - j0
        b = kk - k0
        # (sigma a - (b + delta))^2 -> complete the square with b' = b + delta
        bp = b + delta
        D1 = np.exp(-beta * sig * th * a * a)
        D2 = np.exp(beta * th * bp * bp)
        # Toeplitz part exp(-beta sigma (a - b')^2): depends on a - b' = (a - b) - delta
        offs = np.arange(-(nk - 1), len(jb))
        tcol = np.exp(-beta * sig * (offs - delta) ** 2)
        x = D2 * u[kk % s]
        # y_a = sum_b T(a - b) x_b  via circulant embedding
        Lc = 1 << int(math.ceil(math.log2(len(jb) + nk)))
        kern = np.zeros(Lc, complex)
        for idx, o in enumerate(offs):
            kern[o % Lc] = tcol[idx]
        xx = np.zeros(Lc, complex)
        xx[:nk] = x
        y = np.fft.ifft(np.fft.fft(kern) * np.fft.fft(xx))[: len(jb)]
        v[jb] = D1 * y
    return v


def G_dense(s, t, beta):
    j = np.arange(t)[:, None]
    k = np.arange(s)[None, :]
    G = np.zeros((t, s))
    for m in range(-2, 3):
        z = j * s / t - k - m * s
        G += np.exp(-beta * z * z)
    return G


def t2(rows):
    rng = np.random.default_rng(1)
    for s in [997, 4093]:
        for Lnats in [4.0, 7.0]:
            beta = math.pi ** 2 / (4 * Lnats)
            w = int(math.ceil(math.sqrt(39.2 / beta)))
            for delta in [0.25, 0.5]:
                t = int(math.ceil((1 + delta) * s))
                u = rng.standard_normal(s) + 1j * rng.standard_normal(s)
                ref = G_dense(s, t, beta) @ u
                for meth, fn in [("banded_direct", lambda: G_banded(u, s, t, beta, w))] + \
                                [(f"chirp_toeplitz_B{B}", (lambda B=B: G_blocked_toeplitz(u, s, t, beta, w, B))) for B in [4, 8, 16, 32, 64, 128]]:
                    t0 = time.perf_counter()
                    v = fn()
                    dt = time.perf_counter() - t0
                    err = np.linalg.norm(v - ref) / np.linalg.norm(ref)
                    sig = s / t
                    B = int(meth.split("B")[-1]) if "B" in meth else 0
                    dyn = beta * sig * (1 - sig) * B * B / math.log(10) if B else 0.0  # log10 of D1 growth in a block
                    rows.append(dict(test="T2", s=s, t=t, L=Lnats, delta=delta, method=meth, rel_err=err,
                                     log10_dyn_range=dyn, py_time_ms=dt * 1e3))


# ------------------------------------------------------------------ T3
def t3(rows):
    rng = np.random.default_rng(2)
    for s in [512, 2048]:
        for Lnats in [2.0, 4.0, 7.0]:
            beta = math.pi ** 2 / (4 * Lnats)
            for delta in [0.25, 0.5, 1.0]:
                t = int(math.ceil((1 + delta) * s))
                G = G_dense(s, t, beta)
                N = G.T @ G
                cond = np.linalg.cond(N)
                u = rng.standard_normal(s)
                v = G @ u
                rhs = G.T @ v
                # dense Cholesky reference
                t0 = time.perf_counter()
                uc = cho_solve(cho_factor(N), rhs)
                tc = time.perf_counter() - t0
                rows.append(dict(test="T3", s=s, t=t, L=Lnats, delta=delta, method="cholesky", iters=0,
                                 rel_err=np.linalg.norm(uc - u) / np.linalg.norm(u), cond=cond, py_time_ms=tc * 1e3))
                # Neumann (Richardson) u_{k+1} = u_k + c (rhs - N u_k), c = 2/(lmin+lmax)
                ev = np.linalg.eigvalsh(N)
                c = 2.0 / (ev[0] + ev[-1])
                uk = np.zeros(s)
                it = 0
                t0 = time.perf_counter()
                while it < 5000:
                    r = rhs - N @ uk
                    if np.linalg.norm(r) <= 1e-12 * np.linalg.norm(rhs):
                        break
                    uk += c * r
                    it += 1
                rows.append(dict(test="T3", s=s, t=t, L=Lnats, delta=delta, method="neumann", iters=it,
                                 rel_err=np.linalg.norm(uk - u) / np.linalg.norm(u), cond=cond,
                                 py_time_ms=(time.perf_counter() - t0) * 1e3))
                # PCG with Strang circulant preconditioner built from the central column of N
                col = N[:, s // 2]
                circ = np.zeros(s)
                for d in range(-(s // 2), s - s // 2):
                    circ[d % s] = col[(s // 2 + d) % s] if 0 <= s // 2 + d < s else 0
                lam = np.fft.fft(circ).real
                lam = np.maximum(lam, lam.max() * 1e-14)
                prec = lambda r: np.fft.ifft(np.fft.fft(r) / lam).real
                for pname, M in [("cg", lambda r: r), ("pcg_strang", prec)]:
                    x = np.zeros(s)
                    r = rhs.copy()
                    z = M(r)
                    p = z.copy()
                    rz = r @ z
                    it = 0
                    t0 = time.perf_counter()
                    while it < 5000 and np.linalg.norm(r) > 1e-12 * np.linalg.norm(rhs):
                        Ap = N @ p
                        al = rz / (p @ Ap)
                        x += al * p
                        r -= al * Ap
                        z = M(r)
                        rz2 = r @ z
                        p = z + (rz2 / rz) * p
                        rz = rz2
                        it += 1
                    rows.append(dict(test="T3", s=s, t=t, L=Lnats, delta=delta, method=pname, iters=it,
                                     rel_err=np.linalg.norm(x - u) / np.linalg.norm(u), cond=cond,
                                     py_time_ms=(time.perf_counter() - t0) * 1e3))
                # how Toeplitz is N?  ||N - toeplitz(first col)|| / ||N||
                rows.append(dict(test="T3", s=s, t=t, L=Lnats, delta=delta, method="toeplitz_defect",
                                 iters=0, rel_err=np.linalg.norm(N - toeplitz(N[:, 0])) / np.linalg.norm(N), cond=cond))


def main():
    rows = []
    for n in [7, 16, 31]:
        rows.append(dict(test="T1a_bluestein", n=n, max_abs_err=t1_bluestein(n)))
    for p in [7, 13, 31]:
        rows.append(dict(test="T1b_rader", n=p, max_abs_err=t1_rader(p)))
    for s, t, Ln in [(7, 9, 4.0), (13, 16, 7.0), (11, 15, 5.0)]:
        rows.append(dict(test="T1c_resampling", n=s, t=t, L=Ln, max_abs_err=t1_resampling(s, t, Ln)))
    rows.append(dict(test="T1d_complete_square", n=0, max_abs_err=t1_complete_square()))
    t1 = pd.DataFrame(rows)
    print(t1.to_string())
    assert (t1.max_abs_err < 1e-25).all(), "T1 representation identity failed"
    t1.to_csv(OUT / "toeplitz_T1.csv", index=False)

    r2 = []
    t2(r2)
    d2 = pd.DataFrame(r2)
    print(d2.to_string())
    d2.to_csv(OUT / "toeplitz_T2.csv", index=False)

    r3 = []
    t3(r3)
    d3 = pd.DataFrame(r3)
    print(d3.to_string())
    d3.to_csv(OUT / "toeplitz_T3.csv", index=False)


if __name__ == "__main__":
    main()
