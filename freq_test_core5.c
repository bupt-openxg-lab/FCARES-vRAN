#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#if !defined(__x86_64__) && !defined(__i386__)
#error "This program currently supports x86/x86_64 only."
#endif

#if defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>
static inline uint64_t read_tsc(void) {
  unsigned aux;
  return __rdtscp(&aux);
}
#endif

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif

#define MSR_APERF  0x000000E8
#define MSR_MPERF  0x000000E7

static void bind_to_cpu_or_die(int cpu) {
  cpu_set_t set;
  CPU_ZERO(&set);
  CPU_SET(cpu, &set);
  if (sched_setaffinity(0, sizeof(set), &set) != 0) {
    fprintf(stderr, "sched_setaffinity(cpu=%d) failed: %s\n", cpu, strerror(errno));
    exit(1);
  }
}

static double ts_diff_sec(const struct timespec *a, const struct timespec *b) {
  return (double)(b->tv_sec - a->tv_sec) +
         (double)(b->tv_nsec - a->tv_nsec) / 1e9;
}

static int read_msr_u64(int cpu, uint32_t msr, uint64_t *val) {
  char path[128];
  snprintf(path, sizeof(path), "/dev/cpu/%d/msr", cpu);
  int fd = open(path, O_RDONLY | O_CLOEXEC);
  if (fd < 0) return -1;

  ssize_t n = pread(fd, val, sizeof(*val), (off_t)msr);
  close(fd);
  return (n == (ssize_t)sizeof(*val)) ? 0 : -1;
}

int main(int argc, char **argv) {
  int cpu = 5;
  int rounds = 20;
  int sleep_sec = 1;

  if (argc >= 2) cpu = atoi(argv[1]);
  if (argc >= 3) rounds = atoi(argv[2]);
  if (argc >= 4) sleep_sec = atoi(argv[3]);

  bind_to_cpu_or_die(cpu);

  printf("Bound to CPU %d, rounds=%d, sleep=%d sec\n", cpu, rounds, sleep_sec);
  printf("Columns:\n");
  printf("  iter elapsed(s) tsc_delta tsc_GHz aperf_delta mperf_delta aperf/mperf aperf_GHz cpu_start cpu_end\n\n");

  for (int i = 0; i < rounds; ++i) {
    struct timespec t0, t1;
    uint64_t tsc0, tsc1;
    uint64_t aperf0 = 0, aperf1 = 0, mperf0 = 0, mperf1 = 0;
    int have_msr = 1;

    int cpu_start = sched_getcpu();

    if (clock_gettime(CLOCK_MONOTONIC_RAW, &t0) != 0) {
      perror("clock_gettime(t0)");
      return 1;
    }

    tsc0 = read_tsc();

    if (read_msr_u64(cpu, MSR_APERF, &aperf0) != 0 ||
        read_msr_u64(cpu, MSR_MPERF, &mperf0) != 0) {
      have_msr = 0;
    }

    sleep(sleep_sec);

    tsc1 = read_tsc();

    if (clock_gettime(CLOCK_MONOTONIC_RAW, &t1) != 0) {
      perror("clock_gettime(t1)");
      return 1;
    }

    if (have_msr) {
      if (read_msr_u64(cpu, MSR_APERF, &aperf1) != 0 ||
          read_msr_u64(cpu, MSR_MPERF, &mperf1) != 0) {
        have_msr = 0;
      }
    }

    int cpu_end = sched_getcpu();

    double elapsed = ts_diff_sec(&t0, &t1);
    uint64_t tsc_delta = tsc1 - tsc0;
    double tsc_ghz = (elapsed > 0.0) ? ((double)tsc_delta / elapsed / 1e9) : 0.0;

    if (have_msr) {
      uint64_t aperf_delta = aperf1 - aperf0;
      uint64_t mperf_delta = mperf1 - mperf0;
      double ratio = (mperf_delta > 0) ? ((double)aperf_delta / (double)mperf_delta) : 0.0;
      double aperf_ghz = (elapsed > 0.0) ? ((double)aperf_delta / elapsed / 1e9) : 0.0;

      printf("%4d %.9f %" PRIu64 " %.6f %" PRIu64 " %" PRIu64 " %.6f %.6f %d %d\n",
             i, elapsed, tsc_delta, tsc_ghz,
             aperf_delta, mperf_delta, ratio, aperf_ghz,
             cpu_start, cpu_end);
    } else {
      printf("%4d %.9f %" PRIu64 " %.6f MSR_UNAVAILABLE MSR_UNAVAILABLE MSR_UNAVAILABLE MSR_UNAVAILABLE %d %d\n",
             i, elapsed, tsc_delta, tsc_ghz, cpu_start, cpu_end);
    }

    fflush(stdout);
  }

  return 0;
}