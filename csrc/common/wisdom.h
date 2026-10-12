// SPDX-License-Identifier: GPL-2.0-or-later
// FFTW wisdom location.  Wisdom is machine-specific, so it is read from $FFTW_WISDOM_FILE when set
// (scripts/run_machine.sh points it into results/machines/<label>/); $FFTW_WISDOM_RO=1 disables writing
// (needed when several benchmark processes run concurrently).
#pragma once
#include <stdlib.h>
static inline const char *wisdom_path(void) {
    const char *p = getenv("FFTW_WISDOM_FILE");
    return p && *p ? p : "results/fftw_wisdom.dat";
}
static inline int wisdom_writable(void) { return !getenv("FFTW_WISDOM_RO"); }
