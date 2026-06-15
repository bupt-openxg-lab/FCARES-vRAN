/* hcs_shared.h —— PHY->MAC 轻量数据流 handoff (HCS 在线闭环).
 *
 * 为什么要这个: classifier/backlog 由 MAC 调度线程持有(单线程更新), 但喂它们的原始量
 * (FFT 时延、frontend+decode 实测耗时) 在 PHY 线程测得. 让 PHY 直接动 MAC 大结构会引入
 * 跨层 include 与跨线程竞争. 这里只放两个原子标量 + 序号: PHY 线程调 hcs_report_* 写最新值,
 * MAC 每 slot 按序号去重消费 (调度线程频率 >= PHY 产出, 故不漏不重).
 *   - FFT     : RU FEP 线程  -> hcs_report_fft     (nr_ru_procedures.c)
 *   - L_actual: L1 rx 线程    -> hcs_report_lactual (phy_procedures_nr_gNB.c, frontend+decode)
 * 单写者-单读者, 标量原子即可; 头文件无 MAC 依赖, PHY 可直接 include.
 */
#ifndef HCS_SHARED_H
#define HCS_SHARED_H

#include <stdatomic.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  _Atomic double        fft_us;       /* 最近 slot 的 ru_rx_fft_task_work_sum (µs) */
  _Atomic uint_fast64_t fft_seq;      /* 每次更新 +1, 供 MAC 去重消费 */
  _Atomic double        lactual_us;   /* 最近 slot 的 frontend+decode 实测 (µs) */
  _Atomic uint_fast64_t lactual_seq;
} hcs_shared_t;

extern hcs_shared_t hcs_shared;

static inline void hcs_report_fft(double us)
{
  atomic_store_explicit(&hcs_shared.fft_us, us, memory_order_relaxed);
  atomic_fetch_add_explicit(&hcs_shared.fft_seq, 1, memory_order_release);
}

static inline void hcs_report_lactual(double us)
{
  atomic_store_explicit(&hcs_shared.lactual_us, us, memory_order_relaxed);
  atomic_fetch_add_explicit(&hcs_shared.lactual_seq, 1, memory_order_release);
}

#ifdef __cplusplus
}
#endif

#endif /* HCS_SHARED_H */
