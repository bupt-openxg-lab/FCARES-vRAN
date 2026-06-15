#ifndef CW_STALL_PROBE_H
#define CW_STALL_PROBE_H
/* ----------------------------------------------------------------------------
 * co_workload stall diagnostics (shared probe)
 *
 * Wrap any real-time-critical section with cw_probe_begin()/cw_probe_end().
 * When wall-clock time exceeds the threshold, it tells apart the two causes:
 *   - OFF-CPU : the thread was descheduled (RT throttling / preemption / lock
 *               held by a throttled holder)  -> wall >> thread-CPU time
 *   - ON-CPU  : the thread kept running but slowly (L3 cache contention)
 *               -> wall ~= thread-CPU time
 * nonvoluntary_ctxt_switches (via getrusage(RUSAGE_THREAD), one syscall, no
 * allocation) confirms the kernel forced us off the CPU during the window.
 *
 * The same probe is dropped at every hot point that can stall the air
 * interface (L1_rx notify, RU-thread TX write, TX OFDM, ...), because the
 * bottleneck migrates across runs to whichever RT thread is holding the CPU
 * or a lock when contention/throttling hits.
 * -------------------------------------------------------------------------- */
#include <time.h>
#include <sys/resource.h>
#include <stdint.h>
#include "common/utils/LOG/log.h"

/* RUSAGE_THREAD / CLOCK_MONOTONIC_RAW are Linux/GNU extensions normally gated by
 * _GNU_SOURCE. Some translation units that include this header do not define it
 * (e.g. radio/OXGRF/oxgrf_lib.c). These are fixed kernel ABI values that the
 * glibc getrusage()/clock_gettime() wrappers pass straight through, so providing
 * fallback constants keeps the probe self-contained without _GNU_SOURCE. */
#ifndef RUSAGE_THREAD
#define RUSAGE_THREAD 1
#endif
#ifndef CLOCK_MONOTONIC_RAW
#define CLOCK_MONOTONIC_RAW 4
#endif

#ifndef CW_STALL_THRESHOLD_US
#define CW_STALL_THRESHOLD_US 2000.0 /* only flag catastrophic stalls (>2ms) */
#endif

typedef struct {
  uint64_t w0; /* wall clock        (CLOCK_MONOTONIC_RAW)        */
  uint64_t c0; /* this thread's CPU (CLOCK_THREAD_CPUTIME_ID)    */
  long nv0;    /* voluntary    ctxt switches (blocked itself)    */
  long niv0;   /* nonvoluntary ctxt switches (preempted/throttled) */
} cw_probe_t;

static inline uint64_t cw_ts_ns(clockid_t clk)
{
  struct timespec t;
  clock_gettime(clk, &t);
  return (uint64_t)t.tv_sec * 1000000000ULL + t.tv_nsec;
}

/* voluntary + nonvoluntary ctxt switches of the *calling* thread (one syscall) */
static inline void cw_read_csw(long *nv, long *niv)
{
  struct rusage ru;
  if (getrusage(RUSAGE_THREAD, &ru) == 0) {
    *nv = ru.ru_nvcsw;
    *niv = ru.ru_nivcsw;
  } else {
    *nv = -1;
    *niv = -1;
  }
}

static inline cw_probe_t cw_probe_begin(void)
{
  cw_probe_t p;
  p.w0 = cw_ts_ns(CLOCK_MONOTONIC_RAW);
  p.c0 = cw_ts_ns(CLOCK_THREAD_CPUTIME_ID);
  cw_read_csw(&p.nv0, &p.niv0);
  return p;
}

/* site = short label of the instrumented section, e.g. "l1_rx_out_notify".
 *
 * Verdict logic (the ctxt-switch counters disambiguate WHY we left the CPU):
 *   ratio >= 0.5                         -> ON-CPU, just slow  = L3 cache contention
 *   ratio <  0.5 & nonvoluntary switched -> forced off CPU     = preempt / RT throttle
 *   ratio <  0.5 & ONLY voluntary switch -> we slept on a futex/syscall
 *                                           = BLOCKED on a lock whose holder was
 *                                             descheduled (non-PI priority inversion)
 */
static inline void cw_probe_end(cw_probe_t p, const char *site, int frame, int slot)
{
  const uint64_t c1 = cw_ts_ns(CLOCK_THREAD_CPUTIME_ID);
  const uint64_t w1 = cw_ts_ns(CLOCK_MONOTONIC_RAW);
  const double wall = (w1 - p.w0) / 1000.0; /* us */
  const double cpu = (c1 - p.c0) / 1000.0;  /* us */
  if (wall > CW_STALL_THRESHOLD_US) {
    long nv1, niv1;
    cw_read_csw(&nv1, &niv1);
    const long dnv = (p.nv0 >= 0) ? (nv1 - p.nv0) : -1;    /* voluntary    */
    const long dniv = (p.niv0 >= 0) ? (niv1 - p.niv0) : -1; /* nonvoluntary */
    const double ratio = (wall > 0.0) ? (cpu / wall) : 1.0;
    const char *verdict;
    if (ratio >= 0.5)
      verdict = "ON-CPU(cache-bound)";
    else if (dniv > 0)
      verdict = "OFF-CPU: preempted/RT-throttled (runnable, forced off)";
    else if (dnv > 0)
      verdict = "OFF-CPU: BLOCKED on futex/syscall (lock holder descheduled?)";
    else
      verdict = "OFF-CPU: unclear (no ctxt-switch delta)";
    LOG_E(PHY,
          "[STALL] %d.%d %s wall=%.1fus cpu=%.1fus off_cpu=%.1fus ratio=%.3f vcsw+%ld ivcsw+%ld => %s\n",
          frame,
          slot,
          site,
          wall,
          cpu,
          wall - cpu,
          ratio,
          dnv,
          dniv,
          verdict);
  }
}

#endif /* CW_STALL_PROBE_H */
