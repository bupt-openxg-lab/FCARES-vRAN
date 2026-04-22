#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <x86intrin.h>

#include "perf.h"

#ifndef BENCH_ITERS
#define BENCH_ITERS 10000
#endif
#ifndef WARMUP_ITERS
#define WARMUP_ITERS 1000
#endif
#ifndef WORKLOAD_REPS
#define WORKLOAD_REPS 200
#endif

typedef struct {
  int iter;
  int cpu_start;
  int cpu_end;
  uint64_t wall_ns;
  uint64_t tsc_delta;
  uint64_t pmu_cycles;
  uint64_t pmu_instr;
  uint64_t pmu_cache_ref;
  uint64_t pmu_cache_miss;
} sample_t;

static volatile uint64_t g_sink = 0;

static inline uint64_t now_ns(void)
{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int cmp_u64(const void *a, const void *b)
{
  const uint64_t ua = *(const uint64_t *)a;
  const uint64_t ub = *(const uint64_t *)b;
  return (ua > ub) - (ua < ub);
}

static uint64_t percentile_u64(uint64_t *arr, size_t n, double p)
{
  if (n == 0) return 0;
  qsort(arr, n, sizeof(arr[0]), cmp_u64);
  size_t idx = (size_t)(p * (double)(n - 1) + 0.5);
  if (idx >= n) idx = n - 1;
  return arr[idx];
}

static double mean_u64(const uint64_t *arr, size_t n)
{
  long double sum = 0.0;
  if (n == 0) return 0.0;
  for (size_t i = 0; i < n; ++i) sum += (long double)arr[i];
  return (double)(sum / (long double)n);
}

static void print_stats_u64(FILE *fp, const char *name, const char *unit, uint64_t *arr, size_t n)
{
  if (n == 0) return;
  double avg = mean_u64(arr, n);
  uint64_t p50 = percentile_u64(arr, n, 0.50);
  uint64_t p90 = percentile_u64(arr, n, 0.90);
  uint64_t p99 = percentile_u64(arr, n, 0.99);
  uint64_t min = arr[0];
  uint64_t max = arr[n - 1];
  fprintf(fp,
          "%-28s avg=%12.2f %s  p50=%10" PRIu64 "  p90=%10" PRIu64
          "  p99=%10" PRIu64 "  min=%10" PRIu64 "  max=%10" PRIu64 "\n",
          name, avg, unit, p50, p90, p99, min, max);
}

static void pin_to_cpu(int cpu)
{
  cpu_set_t set;
  CPU_ZERO(&set);
  CPU_SET(cpu, &set);
  if (sched_setaffinity(0, sizeof(set), &set) != 0) {
    fprintf(stderr, "sched_setaffinity(cpu=%d) failed: %s\n", cpu, strerror(errno));
  }
}

static void dummy_workload(size_t reps)
{
  enum { N = 4096 };
  static uint64_t buf[N];
  static int inited = 0;
  if (!inited) {
    for (size_t i = 0; i < N; ++i)
      buf[i] = (uint64_t)(i * 1315423911u + 0x9e3779b97f4a7c15ull);
    inited = 1;
  }

  uint64_t acc = 0x123456789abcdef0ull;
  for (size_t r = 0; r < reps; ++r) {
    for (size_t i = 0; i < N; i += 8) {
      acc ^= buf[(i + (acc & 63)) & (N - 1)];
      acc = (acc << 7) | (acc >> 57);
      acc += (uint64_t)i * 0x9e3779b185ebca87ull;
      buf[i] ^= acc;
    }
  }
  g_sink ^= acc;
}

static int write_csv(const char *path, const sample_t *samples, int n)
{
  FILE *fp = fopen(path, "w");
  if (!fp) {
    fprintf(stderr, "open %s failed: %s\n", path, strerror(errno));
    return -1;
  }

  fprintf(fp, "iter,cpu_start,cpu_end,wall_ns,tsc_delta,pmu_cycles,pmu_instr,pmu_cache_ref,pmu_cache_miss\n");
  for (int i = 0; i < n; ++i) {
    fprintf(fp, "%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 "\n",
            samples[i].iter,
            samples[i].cpu_start,
            samples[i].cpu_end,
            samples[i].wall_ns,
            samples[i].tsc_delta,
            samples[i].pmu_cycles,
            samples[i].pmu_instr,
            samples[i].pmu_cache_ref,
            samples[i].pmu_cache_miss);
  }
  fclose(fp);
  return 0;
}

static void write_summary(FILE *fp, const char *title, const sample_t *samples, int n)
{
  uint64_t *wall = calloc((size_t)n, sizeof(uint64_t));
  uint64_t *tsc = calloc((size_t)n, sizeof(uint64_t));
  uint64_t *cyc = calloc((size_t)n, sizeof(uint64_t));
  uint64_t *ins = calloc((size_t)n, sizeof(uint64_t));
  uint64_t *cref = calloc((size_t)n, sizeof(uint64_t));
  uint64_t *cmiss = calloc((size_t)n, sizeof(uint64_t));
  int migrated = 0;
  long double ipc_sum = 0.0;
  long double mr_sum = 0.0;
  int ipc_cnt = 0;
  int mr_cnt = 0;

  if (!wall || !tsc || !cyc || !ins || !cref || !cmiss) goto out;

  for (int i = 0; i < n; ++i) {
    wall[i] = samples[i].wall_ns;
    tsc[i] = samples[i].tsc_delta;
    cyc[i] = samples[i].pmu_cycles;
    ins[i] = samples[i].pmu_instr;
    cref[i] = samples[i].pmu_cache_ref;
    cmiss[i] = samples[i].pmu_cache_miss;
    if (samples[i].cpu_start != samples[i].cpu_end) migrated++;
    if (samples[i].pmu_cycles) {
      ipc_sum += (long double)samples[i].pmu_instr / (long double)samples[i].pmu_cycles;
      ipc_cnt++;
    }
    if (samples[i].pmu_cache_ref) {
      mr_sum += (long double)samples[i].pmu_cache_miss / (long double)samples[i].pmu_cache_ref;
      mr_cnt++;
    }
  }

  fprintf(fp, "[%s]\n", title);
  print_stats_u64(fp, "wall time", "ns", wall, (size_t)n);
  print_stats_u64(fp, "tsc delta", "cycles", tsc, (size_t)n);
  print_stats_u64(fp, "pmu cycles", "cycles", cyc, (size_t)n);
  print_stats_u64(fp, "pmu instructions", "instr", ins, (size_t)n);
  print_stats_u64(fp, "pmu cache_ref", "events", cref, (size_t)n);
  print_stats_u64(fp, "pmu cache_miss", "events", cmiss, (size_t)n);
  fprintf(fp, "avg ipc                     = %.6Lf\n", ipc_cnt ? ipc_sum / ipc_cnt : 0.0L);
  fprintf(fp, "avg miss rate               = %.6Lf\n", mr_cnt ? mr_sum / mr_cnt : 0.0L);
  fprintf(fp, "cpu migrations              = %d / %d\n\n", migrated, n);

out:
  free(wall); free(tsc); free(cyc); free(ins); free(cref); free(cmiss);
}

static void bench_snapshot_api_only(ldpc_pmu_ctx_t *ctx, sample_t *out, int n)
{
  ldpc_pmu_snapshot_t s0, s1;
  ldpc_pmu_result_t diff;
  for (int i = 0; i < WARMUP_ITERS; ++i) {
    ldpc_pmu_snapshot(ctx, &s0);
    ldpc_pmu_snapshot(ctx, &s1);
    ldpc_pmu_diff(&s0, &s1, &diff);
  }

  for (int i = 0; i < n; ++i) {
    uint64_t wall0 = now_ns();
    int cpu0 = sched_getcpu();
    uint64_t tsc0 = __rdtsc();
    ldpc_pmu_snapshot(ctx, &s0);
    ldpc_pmu_snapshot(ctx, &s1);
    uint64_t tsc1 = __rdtsc();
    int cpu1 = sched_getcpu();
    uint64_t wall1 = now_ns();

    ldpc_pmu_diff(&s0, &s1, &diff);
    out[i] = (sample_t){
      .iter = i,
      .cpu_start = cpu0,
      .cpu_end = cpu1,
      .wall_ns = wall1 - wall0,
      .tsc_delta = tsc1 - tsc0,
      .pmu_cycles = diff.cycles,
      .pmu_instr = diff.instr,
      .pmu_cache_ref = diff.cache_ref,
      .pmu_cache_miss = diff.cache_miss,
    };
  }
}

static void bench_legacy_api_only(ldpc_pmu_ctx_t *ctx, sample_t *out, int n)
{
  ldpc_pmu_result_t r;
  for (int i = 0; i < WARMUP_ITERS; ++i) {
    ldpc_pmu_reset_start_legacy(ctx);
    ldpc_pmu_stop_read_legacy(ctx, &r);
    ldpc_pmu_reenable_after_legacy(ctx);
  }

  for (int i = 0; i < n; ++i) {
    uint64_t wall0 = now_ns();
    int cpu0 = sched_getcpu();
    uint64_t tsc0 = __rdtsc();
    ldpc_pmu_reset_start_legacy(ctx);
    ldpc_pmu_stop_read_legacy(ctx, &r);
    ldpc_pmu_reenable_after_legacy(ctx);
    uint64_t tsc1 = __rdtsc();
    int cpu1 = sched_getcpu();
    uint64_t wall1 = now_ns();

    out[i] = (sample_t){
      .iter = i,
      .cpu_start = cpu0,
      .cpu_end = cpu1,
      .wall_ns = wall1 - wall0,
      .tsc_delta = tsc1 - tsc0,
      .pmu_cycles = r.cycles,
      .pmu_instr = r.instr,
      .pmu_cache_ref = r.cache_ref,
      .pmu_cache_miss = r.cache_miss,
    };
  }
}

static void bench_snapshot_with_workload(ldpc_pmu_ctx_t *ctx, sample_t *out, int n)
{
  ldpc_pmu_snapshot_t s0, s1;
  ldpc_pmu_result_t diff;
  for (int i = 0; i < WARMUP_ITERS; ++i) dummy_workload(WORKLOAD_REPS);

  for (int i = 0; i < n; ++i) {
    uint64_t wall0 = now_ns();
    int cpu0 = sched_getcpu();
    uint64_t tsc0 = __rdtsc();
    ldpc_pmu_snapshot(ctx, &s0);
    dummy_workload(WORKLOAD_REPS);
    ldpc_pmu_snapshot(ctx, &s1);
    uint64_t tsc1 = __rdtsc();
    int cpu1 = sched_getcpu();
    uint64_t wall1 = now_ns();

    ldpc_pmu_diff(&s0, &s1, &diff);
    out[i] = (sample_t){
      .iter = i,
      .cpu_start = cpu0,
      .cpu_end = cpu1,
      .wall_ns = wall1 - wall0,
      .tsc_delta = tsc1 - tsc0,
      .pmu_cycles = diff.cycles,
      .pmu_instr = diff.instr,
      .pmu_cache_ref = diff.cache_ref,
      .pmu_cache_miss = diff.cache_miss,
    };
  }
}

static void bench_legacy_with_workload(ldpc_pmu_ctx_t *ctx, sample_t *out, int n)
{
  ldpc_pmu_result_t r;
  for (int i = 0; i < WARMUP_ITERS; ++i) dummy_workload(WORKLOAD_REPS);

  for (int i = 0; i < n; ++i) {
    uint64_t wall0 = now_ns();
    int cpu0 = sched_getcpu();
    uint64_t tsc0 = __rdtsc();
    ldpc_pmu_reset_start_legacy(ctx);
    dummy_workload(WORKLOAD_REPS);
    ldpc_pmu_stop_read_legacy(ctx, &r);
    ldpc_pmu_reenable_after_legacy(ctx);
    uint64_t tsc1 = __rdtsc();
    int cpu1 = sched_getcpu();
    uint64_t wall1 = now_ns();

    out[i] = (sample_t){
      .iter = i,
      .cpu_start = cpu0,
      .cpu_end = cpu1,
      .wall_ns = wall1 - wall0,
      .tsc_delta = tsc1 - tsc0,
      .pmu_cycles = r.cycles,
      .pmu_instr = r.instr,
      .pmu_cache_ref = r.cache_ref,
      .pmu_cache_miss = r.cache_miss,
    };
  }
}

int main(int argc, char **argv)
{
  int pin_cpu = -1;
  if (argc >= 2) pin_cpu = atoi(argv[1]);
  if (pin_cpu >= 0) pin_to_cpu(pin_cpu);

  ldpc_pmu_ctx_t ctx;
  if (ldpc_pmu_init(&ctx) != 0) {
    fprintf(stderr, "ldpc_pmu_init failed: %s\n", strerror(errno));
    return 1;
  }

  if (!ldpc_pmu_rdpmc_available(&ctx)) {
    fprintf(stderr, "rdpmc unavailable; snapshot benchmarks skipped\n");
    ldpc_pmu_destroy(&ctx);
    return 2;
  }

  sample_t *snapshot_api = calloc(BENCH_ITERS, sizeof(sample_t));
  sample_t *legacy_api = calloc(BENCH_ITERS, sizeof(sample_t));
  sample_t *snapshot_work = calloc(BENCH_ITERS, sizeof(sample_t));
  sample_t *legacy_work = calloc(BENCH_ITERS, sizeof(sample_t));
  if (!snapshot_api || !legacy_api || !snapshot_work || !legacy_work) {
    fprintf(stderr, "alloc failed\n");
    ldpc_pmu_destroy(&ctx);
    free(snapshot_api); free(legacy_api); free(snapshot_work); free(legacy_work);
    return 3;
  }

  bench_snapshot_api_only(&ctx, snapshot_api, BENCH_ITERS);
  bench_legacy_api_only(&ctx, legacy_api, BENCH_ITERS);
  bench_snapshot_with_workload(&ctx, snapshot_work, BENCH_ITERS);
  bench_legacy_with_workload(&ctx, legacy_work, BENCH_ITERS);

  write_csv("snapshot_api_overhead.csv", snapshot_api, BENCH_ITERS);
  write_csv("legacy_api_overhead.csv", legacy_api, BENCH_ITERS);
  write_csv("snapshot_with_workload.csv", snapshot_work, BENCH_ITERS);
  write_csv("legacy_with_workload.csv", legacy_work, BENCH_ITERS);

  FILE *fs = fopen("snapshot_summary.txt", "w");
  FILE *fl = fopen("legacy_summary.txt", "w");
  if (!fs || !fl) {
    fprintf(stderr, "open summary file failed: %s\n", strerror(errno));
  } else {
    fprintf(fs, "pinned_cpu=%d current_cpu=%d BENCH_ITERS=%d WORKLOAD_REPS=%d\n\n",
            pin_cpu, sched_getcpu(), BENCH_ITERS, WORKLOAD_REPS);
    fprintf(fl, "pinned_cpu=%d current_cpu=%d BENCH_ITERS=%d WORKLOAD_REPS=%d\n\n",
            pin_cpu, sched_getcpu(), BENCH_ITERS, WORKLOAD_REPS);

    write_summary(fs, "snapshot api-only (tsc encloses snapshot+snapshot)", snapshot_api, BENCH_ITERS);
    write_summary(fl, "legacy api-only (tsc encloses reset+read)", legacy_api, BENCH_ITERS);
    write_summary(fs, "snapshot with workload (tsc encloses snapshot+workload+snapshot)", snapshot_work, BENCH_ITERS);
    write_summary(fl, "legacy with workload (tsc encloses reset+workload+read)", legacy_work, BENCH_ITERS);
    fclose(fs);
    fclose(fl);
  }

  printf("Generated files:\n");
  printf("  snapshot_api_overhead.csv\n");
  printf("  legacy_api_overhead.csv\n");
  printf("  snapshot_with_workload.csv\n");
  printf("  legacy_with_workload.csv\n");
  printf("  snapshot_summary.txt\n");
  printf("  legacy_summary.txt\n");
  printf("g_sink=%" PRIu64 "\n", g_sink);

  ldpc_pmu_destroy(&ctx);
  free(snapshot_api); free(legacy_api); free(snapshot_work); free(legacy_work);
  return 0;
}
