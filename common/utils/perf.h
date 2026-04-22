#ifndef LDPC_PMU_H
#define LDPC_PMU_H

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#define LDPC_PMU_IMPLEMENTATION

#include <errno.h>
#include <inttypes.h>
#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>


#if !defined(__x86_64__) && !defined(__i386__)
#error "ldpc_pmu.h currently supports x86/x86_64 only."
#endif

#include <x86intrin.h>

#include "common/utils/LOG/log.h"
#define LDPC_PMU_LOGE(fmt, ...) LOG_E(PHY, fmt, ##__VA_ARGS__)
#define LDPC_PMU_LOGW(fmt, ...) LOG_W(PHY, fmt, ##__VA_ARGS__)

#ifdef __cplusplus
extern "C" {
#endif

/* -------------------------------------------------------------------------- */
/* Config                                                                     */
/* -------------------------------------------------------------------------- */

/*
 * 如果大型仓库里已有日志系统，可在包含本头文件前自定义：
 *
 *   #define LDPC_PMU_LOGE(fmt, ...) LOG_E(PHY, fmt, ##__VA_ARGS__)
 *   #define LDPC_PMU_LOGW(fmt, ...) LOG_W(PHY, fmt, ##__VA_ARGS__)
 *
 * 否则默认走 stderr / stdout。
 */
#ifndef LDPC_PMU_LOGE
#define LDPC_PMU_LOGE(fmt, ...) \
  fprintf(stderr, "[LDPC_PMU][ERR] " fmt, ##__VA_ARGS__)
#endif

#ifndef LDPC_PMU_LOGW
#define LDPC_PMU_LOGW(fmt, ...) \
  fprintf(stdout, "[LDPC_PMU][WRN] " fmt, ##__VA_ARGS__)
#endif

/*
 * 头文件实现模式：
 *   - 只在一个 .c 文件里定义 LDPC_PMU_IMPLEMENTATION 后再 include 本头文件
 *   - 其他 .c 文件只普通 include
 *
 * 这样可以避免 header-only 多重定义问题，更适合大型仓库。
 */
#ifdef LDPC_PMU_IMPLEMENTATION
#define LDPC_PMU_API
#else
#define LDPC_PMU_API extern
#endif

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

typedef struct {
  int fd;
  struct perf_event_mmap_page *pc;
} ldpc_pmu_evt_t;

typedef struct {
  ldpc_pmu_evt_t cycles;
  ldpc_pmu_evt_t instr;
  ldpc_pmu_evt_t cache_ref;
  ldpc_pmu_evt_t cache_miss;
  int enabled;
  int rdpmc_ok;
  size_t mmap_len;
} ldpc_pmu_ctx_t;

typedef struct {
  uint64_t cycles;
  uint64_t instr;
  uint64_t cache_ref;
  uint64_t cache_miss;
} ldpc_pmu_result_t;

typedef ldpc_pmu_result_t ldpc_pmu_snapshot_t;

/* -------------------------------------------------------------------------- */
/* Public API                                                                 */
/* -------------------------------------------------------------------------- */

LDPC_PMU_API long ldpc_perf_event_open(struct perf_event_attr *hw_event,
                                       pid_t pid,
                                       int cpu,
                                       int group_fd,
                                       unsigned long flags);

LDPC_PMU_API void ldpc_pmu_ctx_zero(ldpc_pmu_ctx_t *ctx);
LDPC_PMU_API int  ldpc_pmu_init(ldpc_pmu_ctx_t *ctx);
LDPC_PMU_API void ldpc_pmu_destroy(ldpc_pmu_ctx_t *ctx);

LDPC_PMU_API int  ldpc_pmu_is_ready(const ldpc_pmu_ctx_t *ctx);
LDPC_PMU_API int  ldpc_pmu_rdpmc_available(const ldpc_pmu_ctx_t *ctx);

LDPC_PMU_API void ldpc_pmu_reset_start_legacy(ldpc_pmu_ctx_t *ctx);
LDPC_PMU_API void ldpc_pmu_stop_read_legacy(ldpc_pmu_ctx_t *ctx,
                                            ldpc_pmu_result_t *res);
LDPC_PMU_API void ldpc_pmu_reenable_after_legacy(ldpc_pmu_ctx_t *ctx);

LDPC_PMU_API void ldpc_pmu_snapshot(ldpc_pmu_ctx_t *ctx,
                                    ldpc_pmu_snapshot_t *snap);

LDPC_PMU_API void ldpc_pmu_diff(const ldpc_pmu_snapshot_t *begin,
                                const ldpc_pmu_snapshot_t *end,
                                ldpc_pmu_result_t *res);

LDPC_PMU_API void ldpc_pmu_result_zero(ldpc_pmu_result_t *res);

LDPC_PMU_API double ldpc_pmu_ipc(const ldpc_pmu_result_t *r);
LDPC_PMU_API double ldpc_pmu_cache_miss_rate(const ldpc_pmu_result_t *r);

LDPC_PMU_API void ldpc_log_pmu_stats(const char *tag,
                                     uint32_t iter,
                                     const ldpc_pmu_result_t *r);

LDPC_PMU_API void ldpc_flog_pmu_stats(FILE *fp,
                                      const char *tag,
                                      uint32_t iter,
                                      const ldpc_pmu_result_t *r);

/* -------------------------------------------------------------------------- */
/* Implementation                                                             */
/* -------------------------------------------------------------------------- */

#ifdef LDPC_PMU_IMPLEMENTATION


static int ldpc_open_event(uint32_t type, uint64_t config, int group_fd, int disabled)
{
  struct perf_event_attr pe;
  memset(&pe, 0, sizeof(pe));
  pe.type = type;
  pe.size = sizeof(pe);
  pe.config = config;
  pe.disabled = disabled;
  pe.exclude_kernel = 1;
  pe.exclude_hv = 1;
  pe.inherit = 0;
  pe.pinned = 0;
  pe.exclude_idle = 0;

  return (int)ldpc_perf_event_open(&pe, 0, -1, group_fd, 0);
}

static int ldpc_open_hw_event(uint64_t config, int group_fd, int disabled)
{
  return ldpc_open_event(PERF_TYPE_HARDWARE, config, group_fd, disabled);
}

static void ldpc_close_evt(ldpc_pmu_evt_t *evt, size_t mmap_len)
{
  if (!evt) return;

  if (evt->pc && evt->pc != MAP_FAILED) {
    munmap((void *)evt->pc, mmap_len);
  }
  evt->pc = NULL;

  if (evt->fd >= 0) {
    close(evt->fd);
  }
  evt->fd = -1;
}

static int ldpc_mmap_evt(ldpc_pmu_evt_t *evt, size_t mmap_len)
{
  evt->pc = (struct perf_event_mmap_page *)mmap(NULL,
                                                mmap_len,
                                                PROT_READ,
                                                MAP_SHARED,
                                                evt->fd,
                                                0);
  if (evt->pc == MAP_FAILED) {
    evt->pc = NULL;
    return -1;
  }

  volatile uint32_t touch = evt->pc->lock;
  (void)touch;
  return 0;
}

static inline uint64_t ldpc_sign_extend_pmc(uint64_t v, uint16_t pmc_width)
{
  if (pmc_width == 0 || pmc_width >= 64)
    return v;
  return (uint64_t)(((int64_t)(v << (64 - pmc_width))) >> (64 - pmc_width));
}

static inline uint64_t ldpc_read_rdpmc(const struct perf_event_mmap_page *pc, int *ok)
{
  uint32_t seq, idx, width;
  int64_t offset;
  uint64_t pmc;

  if (!pc) {
    *ok = 0;
    return 0;
  }

  for (;;) {
    seq = pc->lock;
    __sync_synchronize();

    idx = pc->index;
    offset = pc->offset;
    width = pc->pmc_width;

    if (idx == 0) {
      __sync_synchronize();
      if (pc->lock == seq) {
        *ok = 1;
        return (uint64_t)offset;
      }
      continue;
    }

    pmc = __rdpmc(idx - 1);
    pmc = ldpc_sign_extend_pmc(pmc, (uint16_t)width);

    __sync_synchronize();
    if (pc->lock == seq) {
      *ok = 1;
      return (uint64_t)(offset + (int64_t)pmc);
    }
  }
}

long ldpc_perf_event_open(struct perf_event_attr *hw_event,
                          pid_t pid,
                          int cpu,
                          int group_fd,
                          unsigned long flags)
{
  return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

void ldpc_pmu_ctx_zero(ldpc_pmu_ctx_t *ctx)
{
  if (!ctx) return;
  memset(ctx, 0, sizeof(*ctx));
  ctx->cycles.fd = -1;
  ctx->instr.fd = -1;
  ctx->cache_ref.fd = -1;
  ctx->cache_miss.fd = -1;
  ctx->cycles.pc = NULL;
  ctx->instr.pc = NULL;
  ctx->cache_ref.pc = NULL;
  ctx->cache_miss.pc = NULL;
  ctx->enabled = 0;
  ctx->rdpmc_ok = 0;
  ctx->mmap_len = 0;
}

int ldpc_pmu_init(ldpc_pmu_ctx_t *ctx)
{
  if (!ctx) {
    errno = EINVAL;
    return -1;
  }

  ldpc_pmu_ctx_zero(ctx);
  ctx->mmap_len = (size_t)sysconf(_SC_PAGESIZE);

  ctx->cycles.fd = ldpc_open_hw_event(PERF_COUNT_HW_CPU_CYCLES, -1, 1);
  if (ctx->cycles.fd < 0) goto fail;

  ctx->instr.fd = ldpc_open_hw_event(PERF_COUNT_HW_INSTRUCTIONS, ctx->cycles.fd, 0);
  if (ctx->instr.fd < 0) goto fail;

  ctx->cache_ref.fd = ldpc_open_hw_event(PERF_COUNT_HW_CACHE_REFERENCES, ctx->cycles.fd, 0);
  if (ctx->cache_ref.fd < 0) goto fail;

  ctx->cache_miss.fd = ldpc_open_hw_event(PERF_COUNT_HW_CACHE_MISSES, ctx->cycles.fd, 0);
  if (ctx->cache_miss.fd < 0) goto fail;

  if (ldpc_mmap_evt(&ctx->cycles, ctx->mmap_len) != 0) goto fail;
  if (ldpc_mmap_evt(&ctx->instr, ctx->mmap_len) != 0) goto fail;
  if (ldpc_mmap_evt(&ctx->cache_ref, ctx->mmap_len) != 0) goto fail;
  if (ldpc_mmap_evt(&ctx->cache_miss, ctx->mmap_len) != 0) goto fail;

  if (ioctl(ctx->cycles.fd, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP) != 0) goto fail;
  if (ioctl(ctx->cycles.fd, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP) != 0) goto fail;

  ctx->enabled =
      1;

  ctx->rdpmc_ok =
      ctx->cycles.pc->cap_user_rdpmc &&
      ctx->instr.pc->cap_user_rdpmc &&
      ctx->cache_ref.pc->cap_user_rdpmc &&
      ctx->cache_miss.pc->cap_user_rdpmc;

  return 0;

fail:
  ldpc_pmu_destroy(ctx);
  return -1;
}

void ldpc_pmu_destroy(ldpc_pmu_ctx_t *ctx)
{
  if (!ctx) return;
  ldpc_close_evt(&ctx->cache_miss, ctx->mmap_len);
  ldpc_close_evt(&ctx->cache_ref, ctx->mmap_len);
  ldpc_close_evt(&ctx->instr, ctx->mmap_len);
  ldpc_close_evt(&ctx->cycles, ctx->mmap_len);
  ctx->enabled = 0;
  ctx->rdpmc_ok = 0;
}

int ldpc_pmu_is_ready(const ldpc_pmu_ctx_t *ctx)
{
  return ctx && ctx->enabled;
}

int ldpc_pmu_rdpmc_available(const ldpc_pmu_ctx_t *ctx)
{
  return ctx && ctx->enabled && ctx->rdpmc_ok;
}

void ldpc_pmu_result_zero(ldpc_pmu_result_t *res)
{
  if (!res) return;
  memset(res, 0, sizeof(*res));
}

void ldpc_pmu_reset_start_legacy(ldpc_pmu_ctx_t *ctx)
{
  if (!ctx || !ctx->enabled) return;
  ioctl(ctx->cycles.fd, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP);
  ioctl(ctx->cycles.fd, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
}

void ldpc_pmu_stop_read_legacy(ldpc_pmu_ctx_t *ctx, ldpc_pmu_result_t *res)
{
  if (!res) return;
  ldpc_pmu_result_zero(res);

  if (!ctx || !ctx->enabled) return;

  ioctl(ctx->cycles.fd, PERF_EVENT_IOC_DISABLE, PERF_IOC_FLAG_GROUP);

  if (read(ctx->cycles.fd, &res->cycles, sizeof(res->cycles)) != (ssize_t)sizeof(res->cycles))
    res->cycles = 0;
  if (read(ctx->instr.fd, &res->instr, sizeof(res->instr)) != (ssize_t)sizeof(res->instr))
    res->instr = 0;
  if (read(ctx->cache_ref.fd, &res->cache_ref, sizeof(res->cache_ref)) != (ssize_t)sizeof(res->cache_ref))
    res->cache_ref = 0;
  if (read(ctx->cache_miss.fd, &res->cache_miss, sizeof(res->cache_miss)) != (ssize_t)sizeof(res->cache_miss))
    res->cache_miss = 0;
}

void ldpc_pmu_reenable_after_legacy(ldpc_pmu_ctx_t *ctx)
{
  if (!ctx || !ctx->enabled) return;
  ioctl(ctx->cycles.fd, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP);
}

void ldpc_pmu_snapshot(ldpc_pmu_ctx_t *ctx, ldpc_pmu_snapshot_t *snap)
{
  if (!snap) return;
  memset(snap, 0, sizeof(*snap));

  if (!ctx || !ctx->enabled || !ctx->rdpmc_ok) return;

  int ok = 1, tmp_ok = 1;

  snap->cycles = ldpc_read_rdpmc(ctx->cycles.pc, &tmp_ok);
  ok &= tmp_ok;

  snap->instr = ldpc_read_rdpmc(ctx->instr.pc, &tmp_ok);
  ok &= tmp_ok;

  snap->cache_ref = ldpc_read_rdpmc(ctx->cache_ref.pc, &tmp_ok);
  ok &= tmp_ok;

  snap->cache_miss = ldpc_read_rdpmc(ctx->cache_miss.pc, &tmp_ok);
  ok &= tmp_ok;

  if (!ok) {
    memset(snap, 0, sizeof(*snap));
  }
}

void ldpc_pmu_diff(const ldpc_pmu_snapshot_t *begin,
                   const ldpc_pmu_snapshot_t *end,
                   ldpc_pmu_result_t *res)
{
  if (!begin || !end || !res) return;
  res->cycles = end->cycles - begin->cycles;
  res->instr = end->instr - begin->instr;
  res->cache_ref = end->cache_ref - begin->cache_ref;
  res->cache_miss = end->cache_miss - begin->cache_miss;
}

double ldpc_pmu_ipc(const ldpc_pmu_result_t *r)
{
  if (!r || r->cycles == 0) return 0.0;
  return (double)r->instr / (double)r->cycles;
}

double ldpc_pmu_cache_miss_rate(const ldpc_pmu_result_t *r)
{
  if (!r || r->cache_ref == 0) return 0.0;
  return (double)r->cache_miss / (double)r->cache_ref;
}

void ldpc_log_pmu_stats(const char *tag,
                        uint32_t iter,
                        const ldpc_pmu_result_t *r)
{
  if (!r) return;

  LDPC_PMU_LOGW("%s iter=%u cycles=%" PRIu64 " instr=%" PRIu64
                " ipc=%.4f cache_ref=%" PRIu64 " cache_miss=%" PRIu64
                " miss_rate=%.4f\n",
                tag ? tag : "pmu",
                iter,
                r->cycles,
                r->instr,
                ldpc_pmu_ipc(r),
                r->cache_ref,
                r->cache_miss,
                ldpc_pmu_cache_miss_rate(r));
}

void ldpc_flog_pmu_stats(FILE *fp,
                         const char *tag,
                         uint32_t iter,
                         const ldpc_pmu_result_t *r)
{
  if (!fp || !r) return;

  fprintf(fp,
          "[LDPC_PMU] %s iter=%u cycles=%" PRIu64 " instr=%" PRIu64
          " ipc=%.6f cache_ref=%" PRIu64 " cache_miss=%" PRIu64
          " miss_rate=%.6f\n",
          tag ? tag : "pmu",
          iter,
          r->cycles,
          r->instr,
          ldpc_pmu_ipc(r),
          r->cache_ref,
          r->cache_miss,
          ldpc_pmu_cache_miss_rate(r));
}

#endif /* LDPC_PMU_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif

#endif /* LDPC_PMU_H */