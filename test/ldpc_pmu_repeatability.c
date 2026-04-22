#define _GNU_SOURCE

/*
 * ldpc_pmu_repeatability.c
 *
 * Experiment driver for validating the repeatability of ldpc_pmu_snapshot()
 * over short measurement windows (target ~= 100 us).
 *
 * The workload layer is intentionally modular:
 *   - add a new workload by providing init/run/cleanup callbacks
 *   - calibration and PMU measurement logic stay unchanged
 *
 * This file is designed to compile as a standalone experiment binary with gcc.
 */

#include <errno.h>
#include <getopt.h>
#include <inttypes.h>
#include <math.h>
#include <sched.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/*
 * perf.h pulls in OAI logging headers. For this standalone experiment binary we
 * keep tracer features disabled and provide the minimal log symbol stubs needed
 * by log.h/perf.h. The experiment itself does not rely on OAI logging.
 */
#ifndef T_TRACER
#define T_TRACER 0
#endif

#ifndef ENABLE_LTTNG
#define ENABLE_LTTNG 0
#endif

#include "common/utils/perf.h"

log_t *g_log = NULL;

void logRecord_mt(const char *file,
                  const char *func,
                  int line,
                  int comp,
                  int level,
                  const char *format,
                  ...)
{
  (void)file;
  (void)func;
  (void)line;
  (void)comp;
  (void)level;
  (void)format;
}

#define DEFAULT_TARGET_US        100.0
#define DEFAULT_CALIB_LOW_US      80.0
#define DEFAULT_CALIB_HIGH_US    150.0
#define DEFAULT_ROUNDS            500
#define DEFAULT_WARMUP_ROUNDS      50
#define DEFAULT_CALIB_SAMPLES       5
#define DEFAULT_CALIB_WARMUPS       5
#define MAX_CALIB_STEPS            20

#define SMALL_ARRAY_BYTES      (32u * 1024u)
#define CHASE_ARRAY_BYTES      (64u * 1024u * 1024u)

static volatile uint64_t g_sink = 0;

typedef struct workload workload_t;

typedef struct {
  uint64_t seed;
} compute_state_t;

typedef struct {
  uint64_t *data;
  size_t len;
  size_t mask;
  size_t cursor;
  uint64_t checksum;
} small_mem_state_t;

typedef struct {
  uint32_t next;
  uint32_t pad;
  uint64_t payload[7];
} chase_node_t;

_Static_assert(sizeof(chase_node_t) == 64, "chase_node_t must stay one cache line");

typedef struct {
  chase_node_t *nodes;
  size_t len;
  size_t mask;
  size_t cursor;
  uint64_t checksum;
} chase_state_t;

typedef struct {
  int cpu;
  int rounds;
  int warmup_rounds;
  double target_us;
  double calib_low_us;
  double calib_high_us;
  const char *csv_path;
} program_options_t;

typedef struct {
  int round_id;
  int cpu_start;
  int cpu_end;
  int migrated;
  uint64_t wall_time_ns;
  ldpc_pmu_result_t pmu;
  double ipc;
  double cache_miss_rate;
  double estimated_freq_ghz;
} round_sample_t;

typedef struct {
  size_t count;
  double avg;
  double stddev;
  double p50;
  double p95;
  double p99;
  double min;
  double max;
  double cv;
} metric_stats_t;

struct workload {
  const char *name;
  const char *description;
  uint64_t initial_iters;
  int (*init)(workload_t *w);
  void (*run)(workload_t *w, uint64_t iterations);
  void (*cleanup)(workload_t *w);
  void *state;
  uint64_t calibrated_iters;
  uint64_t calibration_ns;
};

typedef enum {
  METRIC_INSTR,
  METRIC_CYCLES,
  METRIC_IPC,
  METRIC_CACHE_REF,
  METRIC_CACHE_MISS,
  METRIC_CACHE_MISS_RATE,
  METRIC_WALL_TIME_NS,
  METRIC_EST_FREQ_GHZ
} metric_kind_t;

static inline void compiler_barrier(void)
{
  __asm__ __volatile__("" ::: "memory");
}

static inline uint64_t now_ns(void)
{
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC_RAW, &ts) != 0) {
    perror("clock_gettime(CLOCK_MONOTONIC_RAW)");
    exit(EXIT_FAILURE);
  }
  return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static inline uint64_t rotl64(uint64_t x, unsigned int k)
{
  return (x << k) | (x >> (64u - k));
}

static uint64_t mix64(uint64_t x)
{
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  x *= 0xc4ceb9fe1a85ec53ULL;
  x ^= x >> 33;
  return x;
}

static void *xmalloc(size_t size)
{
  void *ptr = malloc(size);
  if (!ptr) {
    fprintf(stderr, "malloc(%zu) failed\n", size);
    exit(EXIT_FAILURE);
  }
  return ptr;
}

static void *xaligned_alloc(size_t alignment, size_t size)
{
  void *ptr = NULL;
  int rc = posix_memalign(&ptr, alignment, size);
  if (rc != 0) {
    fprintf(stderr, "posix_memalign(%zu, %zu) failed: %s\n",
            alignment,
            size,
            strerror(rc));
    exit(EXIT_FAILURE);
  }
  memset(ptr, 0, size);
  return ptr;
}

static int cmp_double(const void *a, const void *b)
{
  const double va = *(const double *)a;
  const double vb = *(const double *)b;
  if (va < vb) return -1;
  if (va > vb) return 1;
  return 0;
}

static double percentile_sorted(const double *sorted, size_t n, double q)
{
  double pos;
  size_t lo;
  size_t hi;
  double frac;

  if (n == 0) return NAN;
  if (n == 1) return sorted[0];
  if (q <= 0.0) return sorted[0];
  if (q >= 1.0) return sorted[n - 1];

  pos = q * (double)(n - 1);
  lo = (size_t)floor(pos);
  hi = (size_t)ceil(pos);
  frac = pos - (double)lo;

  if (hi == lo) return sorted[lo];
  return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
}

static metric_stats_t compute_stats(const double *values, size_t n)
{
  metric_stats_t stats;
  double *sorted;
  long double sum = 0.0L;
  long double sq_sum = 0.0L;
  size_t i;

  memset(&stats, 0, sizeof(stats));
  stats.avg = NAN;
  stats.stddev = NAN;
  stats.p50 = NAN;
  stats.p95 = NAN;
  stats.p99 = NAN;
  stats.min = NAN;
  stats.max = NAN;
  stats.cv = NAN;

  if (n == 0) return stats;

  sorted = (double *)xmalloc(n * sizeof(*sorted));
  memcpy(sorted, values, n * sizeof(*sorted));
  qsort(sorted, n, sizeof(*sorted), cmp_double);

  for (i = 0; i < n; ++i) {
    sum += (long double)values[i];
  }

  stats.count = n;
  stats.avg = (double)(sum / (long double)n);
  stats.min = sorted[0];
  stats.max = sorted[n - 1];
  stats.p50 = percentile_sorted(sorted, n, 0.50);
  stats.p95 = percentile_sorted(sorted, n, 0.95);
  stats.p99 = percentile_sorted(sorted, n, 0.99);

  if (n > 1) {
    for (i = 0; i < n; ++i) {
      long double d = (long double)values[i] - (long double)stats.avg;
      sq_sum += d * d;
    }
    stats.stddev = sqrt((double)(sq_sum / (long double)(n - 1)));
  } else {
    stats.stddev = 0.0;
  }

  if (stats.avg != 0.0) {
    stats.cv = stats.stddev / fabs(stats.avg);
  } else {
    stats.cv = NAN;
  }

  free(sorted);
  return stats;
}

static const char *bool_to_yesno(int v)
{
  return v ? "yes" : "no";
}

static uint64_t read_first_u64_from_file(const char *path, int *ok)
{
  FILE *fp = fopen(path, "r");
  uint64_t value = 0;
  if (!fp) {
    if (ok) *ok = 0;
    return 0;
  }

  if (fscanf(fp, "%" SCNu64, &value) != 1) {
    fclose(fp);
    if (ok) *ok = 0;
    return 0;
  }

  fclose(fp);
  if (ok) *ok = 1;
  return value;
}

static void print_usage(const char *prog)
{
  printf("Usage: %s [options]\n", prog);
  printf("  -c, --cpu N          pin the experiment thread to CPU N\n");
  printf("  -r, --rounds N       measured rounds per workload (default: %d)\n",
         DEFAULT_ROUNDS);
  printf("  -w, --warmup N       warm-up rounds before measurement (default: %d)\n",
         DEFAULT_WARMUP_ROUNDS);
  printf("  -t, --target-us X    target calibration window in microseconds (default: %.1f)\n",
         DEFAULT_TARGET_US);
  printf("      --low-us X       lower acceptable calibration bound (default: %.1f)\n",
         DEFAULT_CALIB_LOW_US);
  printf("      --high-us X      upper acceptable calibration bound (default: %.1f)\n",
         DEFAULT_CALIB_HIGH_US);
  printf("  -o, --csv PATH       output CSV path (default: ldpc_pmu_repeatability.csv)\n");
  printf("  -h, --help           show this help\n");
}

static program_options_t parse_args(int argc, char **argv)
{
  program_options_t opts;
  int c;

  static const struct option long_opts[] = {
      {"cpu", required_argument, NULL, 'c'},
      {"rounds", required_argument, NULL, 'r'},
      {"warmup", required_argument, NULL, 'w'},
      {"target-us", required_argument, NULL, 't'},
      {"low-us", required_argument, NULL, 1000},
      {"high-us", required_argument, NULL, 1001},
      {"csv", required_argument, NULL, 'o'},
      {"help", no_argument, NULL, 'h'},
      {NULL, 0, NULL, 0},
  };

  opts.cpu = -1;
  opts.rounds = DEFAULT_ROUNDS;
  opts.warmup_rounds = DEFAULT_WARMUP_ROUNDS;
  opts.target_us = DEFAULT_TARGET_US;
  opts.calib_low_us = DEFAULT_CALIB_LOW_US;
  opts.calib_high_us = DEFAULT_CALIB_HIGH_US;
  opts.csv_path = "ldpc_pmu_repeatability.csv";

  while ((c = getopt_long(argc, argv, "c:r:w:t:o:h", long_opts, NULL)) != -1) {
    switch (c) {
      case 'c':
        opts.cpu = atoi(optarg);
        break;
      case 'r':
        opts.rounds = atoi(optarg);
        break;
      case 'w':
        opts.warmup_rounds = atoi(optarg);
        break;
      case 't':
        opts.target_us = atof(optarg);
        break;
      case 'o':
        opts.csv_path = optarg;
        break;
      case 1000:
        opts.calib_low_us = atof(optarg);
        break;
      case 1001:
        opts.calib_high_us = atof(optarg);
        break;
      case 'h':
        print_usage(argv[0]);
        exit(EXIT_SUCCESS);
      default:
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }
  }

  if (opts.rounds <= 0 || opts.warmup_rounds < 0 ||
      opts.target_us <= 0.0 || opts.calib_low_us <= 0.0 ||
      opts.calib_high_us < opts.calib_low_us) {
    fprintf(stderr, "invalid arguments\n");
    exit(EXIT_FAILURE);
  }

  return opts;
}

static void maybe_pin_to_cpu(int cpu)
{
  cpu_set_t set;

  if (cpu < 0) return;

  CPU_ZERO(&set);
  CPU_SET((unsigned int)cpu, &set);

  if (sched_setaffinity(0, sizeof(set), &set) != 0) {
    fprintf(stderr, "sched_setaffinity(cpu=%d) failed: %s\n", cpu, strerror(errno));
    exit(EXIT_FAILURE);
  }
}

static int init_compute_workload(workload_t *w)
{
  compute_state_t *state = (compute_state_t *)xmalloc(sizeof(*state));
  state->seed = 0x123456789abcdef0ULL;
  w->state = state;
  return 0;
}

static int init_small_mem_workload(workload_t *w)
{
  size_t len = SMALL_ARRAY_BYTES / sizeof(uint64_t);
  size_t i;
  small_mem_state_t *state = (small_mem_state_t *)xmalloc(sizeof(*state));

  state->data = (uint64_t *)xaligned_alloc(64, len * sizeof(*state->data));
  state->len = len;
  state->mask = len - 1;
  state->cursor = 0;
  state->checksum = 0;

  for (i = 0; i < len; ++i) {
    state->data[i] = mix64((uint64_t)i + 0x1000ULL);
  }

  w->state = state;
  return 0;
}

static int init_chase_workload(workload_t *w)
{
  size_t len = CHASE_ARRAY_BYTES / sizeof(chase_node_t);
  size_t i;
  const uint32_t stride = 8191u;
  chase_state_t *state = (chase_state_t *)xmalloc(sizeof(*state));

  state->nodes = (chase_node_t *)xaligned_alloc(64, len * sizeof(*state->nodes));
  state->len = len;
  state->mask = len - 1;
  state->cursor = 0;
  state->checksum = 0;

  for (i = 0; i < len; ++i) {
    size_t j;
    state->nodes[i].next = (uint32_t)((i + stride) & state->mask);
    state->nodes[i].pad = 0;
    for (j = 0; j < 7; ++j) {
      state->nodes[i].payload[j] = mix64((uint64_t)i * 131u + (uint64_t)j);
    }
  }

  w->state = state;
  return 0;
}

static void cleanup_compute_workload(workload_t *w)
{
  free(w->state);
  w->state = NULL;
}

static void cleanup_small_mem_workload(workload_t *w)
{
  small_mem_state_t *state = (small_mem_state_t *)w->state;
  if (!state) return;
  free(state->data);
  free(state);
  w->state = NULL;
}

static void cleanup_chase_workload(workload_t *w)
{
  chase_state_t *state = (chase_state_t *)w->state;
  if (!state) return;
  free(state->nodes);
  free(state);
  w->state = NULL;
}

__attribute__((noinline))
static void run_compute_workload(workload_t *w, uint64_t iterations)
{
  compute_state_t *state = (compute_state_t *)w->state;
  uint64_t a = state->seed ^ 0x9e3779b97f4a7c15ULL;
  uint64_t b = state->seed + 0xbf58476d1ce4e5b9ULL;
  uint64_t c = state->seed ^ 0x94d049bb133111ebULL;
  uint64_t d = state->seed + 0x2545f4914f6cdd1dULL;
  uint64_t e = state->seed ^ 0xda942042e4dd58b5ULL;
  uint64_t f = state->seed + 0x369dea0f31a53f85ULL;
  uint64_t g = state->seed ^ 0xdb4f0b9175ae2165ULL;
  uint64_t h = state->seed + 0x632be59bd9b4e019ULL;
  uint64_t i;

  for (i = 0; i < iterations; ++i) {
    a = rotl64(a + b + 0x9e3779b97f4a7c15ULL, 5) ^ h;
    b = (b ^ c) + 0xbf58476d1ce4e5b9ULL;
    c = rotl64(c + d, 11) ^ a;
    d = (d * 3u) + 0x94d049bb133111ebULL + (b >> 3);
    e = rotl64(e ^ f, 17) + c;
    f = (f + g) ^ rotl64(d, 9);
    g = rotl64(g + h, 23) ^ e;
    h = (h * 5u) + a + (uint64_t)i;
  }

  state->seed ^= a ^ b ^ c ^ d ^ e ^ f ^ g ^ h ^ iterations;
  g_sink ^= state->seed;
}

__attribute__((noinline))
static void run_small_mem_workload(workload_t *w, uint64_t iterations)
{
  small_mem_state_t *state = (small_mem_state_t *)w->state;
  size_t idx = state->cursor;
  uint64_t acc0 = state->checksum + 0x0123456789abcdefULL;
  uint64_t acc1 = state->checksum ^ 0xfedcba9876543210ULL;
  uint64_t i;

  for (i = 0; i < iterations; ++i) {
    uint64_t *d = state->data;
    size_t m = state->mask;
    uint64_t x0, x1, x2, x3, x4, x5, x6, x7;

    idx = (idx + 8u) & m;

    x0 = d[(idx + 0u) & m];
    x1 = d[(idx + 1u) & m];
    x2 = d[(idx + 2u) & m];
    x3 = d[(idx + 3u) & m];
    x4 = d[(idx + 4u) & m];
    x5 = d[(idx + 5u) & m];
    x6 = d[(idx + 6u) & m];
    x7 = d[(idx + 7u) & m];

    x0 += rotl64(x4 ^ acc0, 3);
    x1 ^= rotl64(x5 + acc1, 7);
    x2 += x6 ^ 0x9e3779b97f4a7c15ULL;
    x3 ^= x7 + 0xbf58476d1ce4e5b9ULL;

    d[(idx + 0u) & m] = x0;
    d[(idx + 1u) & m] = x1;
    d[(idx + 2u) & m] = x2;
    d[(idx + 3u) & m] = x3;

    acc0 += x0 + x2 + x4 + x6;
    acc1 ^= x1 + x3 + x5 + x7;
  }

  state->cursor = idx;
  state->checksum ^= acc0 + rotl64(acc1, 13);
  g_sink += state->checksum;
}

__attribute__((noinline))
static void run_chase_workload(workload_t *w, uint64_t iterations)
{
  chase_state_t *state = (chase_state_t *)w->state;
  size_t idx = state->cursor;
  uint64_t acc = state->checksum + 0x9e3779b97f4a7c15ULL;
  uint64_t i;

  for (i = 0; i < iterations; ++i) {
    chase_node_t *node;
    idx = state->nodes[idx].next;
    node = &state->nodes[idx];
    acc ^= node->payload[0];
    acc += node->payload[3];
    acc = rotl64(acc, 9);
  }

  state->cursor = idx;
  state->checksum ^= acc;
  g_sink ^= state->checksum;
}

static void workload_warmup(workload_t *w, uint64_t iterations, int rounds)
{
  int i;
  for (i = 0; i < rounds; ++i) {
    w->run(w, iterations);
  }
}

static uint64_t measure_workload_only_ns(workload_t *w, uint64_t iterations)
{
  double samples[DEFAULT_CALIB_SAMPLES];
  size_t i;

  workload_warmup(w, iterations, DEFAULT_CALIB_WARMUPS);
  for (i = 0; i < DEFAULT_CALIB_SAMPLES; ++i) {
    uint64_t start = now_ns();
    compiler_barrier();
    w->run(w, iterations);
    compiler_barrier();
    samples[i] = (double)(now_ns() - start);
  }

  return (uint64_t)llround(compute_stats(samples, DEFAULT_CALIB_SAMPLES).p50);
}

static void calibrate_workload(workload_t *w, double target_us, double low_us, double high_us)
{
  const uint64_t target_ns = (uint64_t)llround(target_us * 1000.0);
  const uint64_t low_ns = (uint64_t)llround(low_us * 1000.0);
  const uint64_t high_ns = (uint64_t)llround(high_us * 1000.0);
  uint64_t best_iters = w->initial_iters ? w->initial_iters : 1u;
  uint64_t best_ns = 0;
  uint64_t best_err = UINT64_MAX;
  uint64_t iters = best_iters;
  int step;

  /*
   * Calibration uses wall time only. The chosen iteration count stays fixed
   * during the formal measurement phase so PMU repeatability is evaluated at a
   * constant workload shape instead of a constantly retuned runtime target.
   */
  for (step = 0; step < MAX_CALIB_STEPS; ++step) {
    uint64_t ns = measure_workload_only_ns(w, iters);
    uint64_t err = (ns > target_ns) ? (ns - target_ns) : (target_ns - ns);

    if (err < best_err) {
      best_err = err;
      best_iters = iters;
      best_ns = ns;
    }

    if (ns >= low_ns && ns <= high_ns) {
      best_iters = iters;
      best_ns = ns;
      break;
    }

    if (ns == 0) {
      iters *= 4u;
      continue;
    }

    {
      double ratio = (double)target_ns / (double)ns;
      uint64_t next = (uint64_t)llround((double)iters * ratio);

      if (next == iters) {
        if (ns < low_ns) {
          next = iters + (iters / 2u) + 1u;
        } else if (iters > 1u) {
          next = iters - (iters / 4u ? iters / 4u : 1u);
        } else {
          next = 1u;
        }
      }

      if (next == 0) next = 1u;

      if (next > iters * 8u && iters < UINT64_MAX / 8u) {
        next = iters * 8u;
      }

      iters = next;
    }
  }

  w->calibrated_iters = best_iters;
  w->calibration_ns = best_ns;
}

static void fail_pmu_init(const ldpc_pmu_ctx_t *pmu_ctx)
{
  int ok_paranoid = 0;
  int ok_rdpmc = 0;
  uint64_t paranoid = read_first_u64_from_file("/proc/sys/kernel/perf_event_paranoid", &ok_paranoid);
  uint64_t rdpmc = read_first_u64_from_file("/sys/bus/event_source/devices/cpu/rdpmc", &ok_rdpmc);

  (void)pmu_ctx;
  fprintf(stderr, "ldpc_pmu_init() failed: %s\n", strerror(errno));
  if (ok_paranoid) {
    fprintf(stderr, "  /proc/sys/kernel/perf_event_paranoid = %" PRIu64 "\n", paranoid);
  }
  if (ok_rdpmc) {
    fprintf(stderr, "  /sys/bus/event_source/devices/cpu/rdpmc = %" PRIu64 "\n", rdpmc);
  }
  fprintf(stderr, "This experiment requires perf_event access and user RDPMC support.\n");
  exit(EXIT_FAILURE);
}

static void ensure_pmu_ready(ldpc_pmu_ctx_t *pmu_ctx)
{
  if (ldpc_pmu_init(pmu_ctx) != 0) {
    fail_pmu_init(pmu_ctx);
  }

  if (!ldpc_pmu_is_ready(pmu_ctx) || !ldpc_pmu_rdpmc_available(pmu_ctx)) {
    int ok_rdpmc = 0;
    uint64_t rdpmc = read_first_u64_from_file("/sys/bus/event_source/devices/cpu/rdpmc", &ok_rdpmc);
    fprintf(stderr, "PMU context initialized but user RDPMC is unavailable.\n");
    if (ok_rdpmc) {
      fprintf(stderr, "  /sys/bus/event_source/devices/cpu/rdpmc = %" PRIu64 "\n", rdpmc);
    }
    ldpc_pmu_destroy(pmu_ctx);
    exit(EXIT_FAILURE);
  }
}

static round_sample_t run_measured_round(workload_t *w, ldpc_pmu_ctx_t *pmu_ctx, int round_id)
{
  round_sample_t sample;
  ldpc_pmu_snapshot_t s0;
  ldpc_pmu_snapshot_t s1;

  memset(&sample, 0, sizeof(sample));
  sample.round_id = round_id;
  sample.cpu_start = sched_getcpu();

  /*
   * Keep the measured region narrow: wall clock and PMU snapshots bracket the
   * workload directly, and all formatting or file I/O happens after the round.
   */
  compiler_barrier();
  {
    uint64_t start_ns = now_ns();
    ldpc_pmu_snapshot(pmu_ctx, &s0);
    w->run(w, w->calibrated_iters);
    ldpc_pmu_snapshot(pmu_ctx, &s1);
    sample.wall_time_ns = now_ns() - start_ns;
  }
  compiler_barrier();

  sample.cpu_end = sched_getcpu();
  sample.migrated = (sample.cpu_start != sample.cpu_end);
  ldpc_pmu_diff(&s0, &s1, &sample.pmu);

  sample.ipc = ldpc_pmu_ipc(&sample.pmu);
  if (sample.pmu.cache_ref > 0) {
    sample.cache_miss_rate = ldpc_pmu_cache_miss_rate(&sample.pmu);
  } else {
    sample.cache_miss_rate = NAN;
  }

  if (sample.wall_time_ns > 0) {
    sample.estimated_freq_ghz = (double)sample.pmu.cycles / (double)sample.wall_time_ns;
  } else {
    sample.estimated_freq_ghz = NAN;
  }

  return sample;
}

static int sample_metric_value(const round_sample_t *sample, metric_kind_t kind, double *out)
{
  switch (kind) {
    case METRIC_INSTR:
      *out = (double)sample->pmu.instr;
      return 1;
    case METRIC_CYCLES:
      *out = (double)sample->pmu.cycles;
      return 1;
    case METRIC_IPC:
      if (sample->pmu.cycles == 0) return 0;
      *out = sample->ipc;
      return isfinite(*out);
    case METRIC_CACHE_REF:
      *out = (double)sample->pmu.cache_ref;
      return 1;
    case METRIC_CACHE_MISS:
      *out = (double)sample->pmu.cache_miss;
      return 1;
    case METRIC_CACHE_MISS_RATE:
      if (sample->pmu.cache_ref == 0) return 0;
      *out = sample->cache_miss_rate;
      return isfinite(*out);
    case METRIC_WALL_TIME_NS:
      *out = (double)sample->wall_time_ns;
      return 1;
    case METRIC_EST_FREQ_GHZ:
      if (sample->wall_time_ns == 0) return 0;
      *out = sample->estimated_freq_ghz;
      return isfinite(*out);
    default:
      return 0;
  }
}

static metric_stats_t collect_metric_stats(const round_sample_t *samples,
                                           size_t sample_count,
                                           metric_kind_t kind)
{
  double *values = (double *)xmalloc(sample_count * sizeof(*values));
  size_t n = 0;
  size_t i;
  metric_stats_t stats;

  for (i = 0; i < sample_count; ++i) {
    double value = 0.0;
    if (!sample_metric_value(&samples[i], kind, &value)) continue;
    values[n++] = value;
  }

  stats = compute_stats(values, n);
  free(values);
  return stats;
}

static int cache_metrics_present(const round_sample_t *samples, size_t sample_count)
{
  size_t i;
  for (i = 0; i < sample_count; ++i) {
    if (samples[i].pmu.cache_ref != 0 || samples[i].pmu.cache_miss != 0) return 1;
  }
  return 0;
}

static void print_metric_stats(const char *label, metric_stats_t stats, const char *fmt)
{
  if (stats.count == 0) {
    printf("  %-20s n=0 (no valid samples)\n", label);
    return;
  }

  printf("  %-20s n=%zu avg=", label, stats.count);
  printf(fmt, stats.avg);
  printf(" std=");
  printf(fmt, stats.stddev);
  printf(" p50=");
  printf(fmt, stats.p50);
  printf(" p95=");
  printf(fmt, stats.p95);
  printf(" p99=");
  printf(fmt, stats.p99);
  printf(" min=");
  printf(fmt, stats.min);
  printf(" max=");
  printf(fmt, stats.max);
  printf(" cv=%.6f\n", stats.cv);
}

static void summarize_workload(const workload_t *w,
                               const round_sample_t *samples,
                               size_t sample_count,
                               int warmup_rounds)
{
  size_t i;
  size_t migrated = 0;
  size_t zero_cycles = 0;
  int cache_present = cache_metrics_present(samples, sample_count);

  for (i = 0; i < sample_count; ++i) {
    migrated += (size_t)samples[i].migrated;
    zero_cycles += (samples[i].pmu.cycles == 0);
  }

  printf("\n=== %s ===\n", w->name);
  printf("description           : %s\n", w->description);
  printf("calibrated_iters      : %" PRIu64 "\n", w->calibrated_iters);
  printf("calibration_window_us : %.3f\n", (double)w->calibration_ns / 1000.0);
  printf("measured_rounds       : %zu\n", sample_count);
  printf("warmup_rounds         : %d\n", warmup_rounds);
  printf("migrated_rounds       : %zu\n", migrated);
  printf("zero_cycle_rounds     : %zu\n", zero_cycles);

  print_metric_stats("instructions", collect_metric_stats(samples, sample_count, METRIC_INSTR), "%.3f");
  print_metric_stats("cycles", collect_metric_stats(samples, sample_count, METRIC_CYCLES), "%.3f");
  print_metric_stats("ipc", collect_metric_stats(samples, sample_count, METRIC_IPC), "%.6f");

  if (cache_present) {
    print_metric_stats("cache_ref", collect_metric_stats(samples, sample_count, METRIC_CACHE_REF), "%.3f");
    print_metric_stats("cache_miss", collect_metric_stats(samples, sample_count, METRIC_CACHE_MISS), "%.3f");
    print_metric_stats("cache_miss_rate", collect_metric_stats(samples, sample_count, METRIC_CACHE_MISS_RATE), "%.6f");
  } else {
    printf("  %-20s all zero in this run; cache counters may be unavailable or workload did not exercise them.\n",
           "cache metrics");
  }

  print_metric_stats("wall_time_ns", collect_metric_stats(samples, sample_count, METRIC_WALL_TIME_NS), "%.3f");
  print_metric_stats("estimated_freq_GHz",
                     collect_metric_stats(samples, sample_count, METRIC_EST_FREQ_GHZ),
                     "%.6f");
}

static void csv_print_double(FILE *fp, double v)
{
  if (!isfinite(v)) return;
  fprintf(fp, "%.12f", v);
}

static void write_csv_header(FILE *fp)
{
  fprintf(fp,
          "workload_name,round_id,iterations,cpu_id,cpu_end,migrated,wall_time_ns,"
          "instructions,cycles,ipc,cache_ref,cache_miss,cache_miss_rate,estimated_freq_ghz\n");
}

static void append_csv_rows(FILE *fp,
                            const workload_t *w,
                            const round_sample_t *samples,
                            size_t sample_count)
{
  size_t i;

  for (i = 0; i < sample_count; ++i) {
    const round_sample_t *s = &samples[i];
    fprintf(fp,
            "%s,%d,%" PRIu64 ",%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",",
            w->name,
            s->round_id,
            w->calibrated_iters,
            s->cpu_start,
            s->cpu_end,
            s->migrated,
            s->wall_time_ns,
            s->pmu.instr,
            s->pmu.cycles);
    csv_print_double(fp, s->ipc);
    fprintf(fp, ",%" PRIu64 ",%" PRIu64 ",", s->pmu.cache_ref, s->pmu.cache_miss);
    csv_print_double(fp, s->cache_miss_rate);
    fputc(',', fp);
    csv_print_double(fp, s->estimated_freq_ghz);
    fputc('\n', fp);
  }
}

static void run_workload_experiment(workload_t *w,
                                    const program_options_t *opts,
                                    ldpc_pmu_ctx_t *pmu_ctx,
                                    FILE *csv_fp)
{
  round_sample_t *samples;
  int i;

  if (w->init(w) != 0) {
    fprintf(stderr, "failed to initialize workload %s\n", w->name);
    exit(EXIT_FAILURE);
  }

  calibrate_workload(w, opts->target_us, opts->calib_low_us, opts->calib_high_us);
  workload_warmup(w, w->calibrated_iters, opts->warmup_rounds);

  samples = (round_sample_t *)xmalloc((size_t)opts->rounds * sizeof(*samples));
  for (i = 0; i < opts->rounds; ++i) {
    samples[i] = run_measured_round(w, pmu_ctx, i);
  }

  summarize_workload(w, samples, (size_t)opts->rounds, opts->warmup_rounds);
  append_csv_rows(csv_fp, w, samples, (size_t)opts->rounds);
  fflush(csv_fp);

  free(samples);
  w->cleanup(w);
}

int main(int argc, char **argv)
{
  program_options_t opts = parse_args(argc, argv);
  workload_t workloads[] = {
      {
          .name = "compute-heavy",
          .description = "ALU-heavy recurrence with minimal memory footprint.",
          .initial_iters = 4096,
          .init = init_compute_workload,
          .run = run_compute_workload,
          .cleanup = cleanup_compute_workload,
          .state = NULL,
          .calibrated_iters = 0,
          .calibration_ns = 0,
      },
      {
          .name = "memory-friendly",
          .description = "Small hot array with regular read/write accesses and high cache hit rate.",
          .initial_iters = 1024,
          .init = init_small_mem_workload,
          .run = run_small_mem_workload,
          .cleanup = cleanup_small_mem_workload,
          .state = NULL,
          .calibrated_iters = 0,
          .calibration_ns = 0,
      },
      {
          .name = "memory-stressing",
          .description = "Dependent pointer chase over a large array to provoke cache misses.",
          .initial_iters = 256,
          .init = init_chase_workload,
          .run = run_chase_workload,
          .cleanup = cleanup_chase_workload,
          .state = NULL,
          .calibrated_iters = 0,
          .calibration_ns = 0,
      },
  };
  const size_t workload_count = sizeof(workloads) / sizeof(workloads[0]);
  ldpc_pmu_ctx_t pmu_ctx;
  FILE *csv_fp;
  size_t i;

  maybe_pin_to_cpu(opts.cpu);
  printf("current_cpu           : %d\n", sched_getcpu());
  printf("cpu_pinned            : %s\n", bool_to_yesno(opts.cpu >= 0));
  if (opts.cpu >= 0) {
    printf("requested_cpu         : %d\n", opts.cpu);
  }
  printf("target_window_us      : %.3f\n", opts.target_us);
  printf("accepted_window_us    : [%.3f, %.3f]\n", opts.calib_low_us, opts.calib_high_us);
  printf("rounds_per_workload   : %d\n", opts.rounds);
  printf("warmup_rounds         : %d\n", opts.warmup_rounds);
  printf("csv_output            : %s\n", opts.csv_path);

  ensure_pmu_ready(&pmu_ctx);
  printf("pmu_ready             : yes\n");
  printf("rdpmc_available       : yes\n");

  csv_fp = fopen(opts.csv_path, "w");
  if (!csv_fp) {
    fprintf(stderr, "failed to open CSV '%s': %s\n", opts.csv_path, strerror(errno));
    ldpc_pmu_destroy(&pmu_ctx);
    return EXIT_FAILURE;
  }

  write_csv_header(csv_fp);

  for (i = 0; i < workload_count; ++i) {
    run_workload_experiment(&workloads[i], &opts, &pmu_ctx, csv_fp);
  }

  fclose(csv_fp);
  ldpc_pmu_destroy(&pmu_ctx);

  printf("\nfinal_sink            : %" PRIu64 "\n", g_sink);
  printf("CSV written to        : %s\n", opts.csv_path);
  return EXIT_SUCCESS;
}
