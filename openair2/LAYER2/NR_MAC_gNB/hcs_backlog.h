/* hcs_backlog.h —— HCS 计算 backlog 抽象 + 调度可行性判定
 *
 * 在线模型采用 predicted-commitment:
 *   - 每个源 slot 推进时先排空服务预算: c = max(0, c - B)
 *   - 只有成功形成最终 grant 后, 才把该 grant 的预测计算量加入: c += L_pred(final grant)
 *   c_t : 累积预测计算 backlog (µs)
 *   B   : 每 slot 计算服务预算 (µs); μ=1 时 slot=500µs
 * 调度可行性: 若候选 grant 的预测耗时 L_pred 会让投影 backlog 越过 deadline D 则不可行,
 *   即 feasible <=> c + L_pred < D, 否则二分降 RB. 候选/cap 计算本身不改变 c.
 * B/D 标定见 python_scripts/threshold_test/threshold_test.md (D≈2500µs, state/dataset-indep).
 */
#ifndef HCS_BACKLOG_H
#define HCS_BACKLOG_H

#include "hcs_model.h"   /* hcs_state_t, hcs_predict_total */

#ifdef __cplusplus
extern "C" {
#endif

#ifndef HCS_BUDGET_US
#define HCS_BUDGET_US   500.0    /* B: 每 slot 计算服务预算 (µs) */
#endif
#ifndef HCS_DEADLINE_US
#define HCS_DEADLINE_US 2500.0   /* D: 最大可容忍累积 backlog (µs) */
#endif

#define HCS_NO_FEASIBLE_PRB (-1)

typedef struct {
  double backlog_us;    /* c_t, 当前累积 backlog */
  double budget_us;     /* B */
  double deadline_us;   /* D */
} hcs_backlog_t;

/* 生命周期 */
void   hcs_backlog_init(hcs_backlog_t *b, double budget_us, double deadline_us);
void   hcs_backlog_reset(hcs_backlog_t *b);
double hcs_backlog_get(const hcs_backlog_t *b);

/* legacy: 用实测计算耗时 L_actual 更新 backlog, 在线调度不再调用 */
double hcs_backlog_update(hcs_backlog_t *b, double l_actual_us);

/* predicted-commitment: 源 slot 时间推进时排空服务预算 */
void   hcs_backlog_drain(hcs_backlog_t *b);
void   hcs_backlog_drain_slots(hcs_backlog_t *b, int slots);

/* predicted-commitment: final grant 成功后加入其预测计算量 */
void   hcs_backlog_add(hcs_backlog_t *b, double l_pred_us);

/* 投影 (不改状态): 若本 slot 耗时 L, backlog 会变成多少 */
double hcs_backlog_project(const hcs_backlog_t *b, double l_us);

/* 当前还能容纳的最大新增预测计算量 L_max = D - c (clamp >=0) */
double hcs_backlog_grant_budget(const hcs_backlog_t *b);

/* 可行性: 预测耗时 L_pred 是否能让投影 backlog 保持 < D */
int    hcs_backlog_feasible(const hcs_backlog_t *b, double l_pred_us);

/* 调度集成: backlog + 预测器, 判某 grant 是否可行 (q_idx: -1 mean, 0..HCS_NQUANT-1 分位) */
int    hcs_grant_feasible(const hcs_backlog_t *b, hcs_state_t state,
                          double TBS, double mcs, double nb_rb, double nb_symbol,
                          double round, int CodeBlocks, int q_idx);

/* 候选 nb_rb -> (TBS, CodeBlocks) 回调; OAI 侧包 nr_compute_tbs + CB 计算 */
typedef void (*hcs_tbs_fn)(int nb_rb, int nb_symbol, int mcs, int round,
                           void *ctx, double *out_TBS, int *out_CodeBlocks);

/* backlog-aware 二分降 RB: 在 [min_prb, requested_prb] 找最大可行 nb_rb;
 * 全不可行返回 HCS_NO_FEASIBLE_PRB */
int    hcs_select_prb(const hcs_backlog_t *b, hcs_state_t state, int mcs, int nb_symbol,
                      int round, int requested_prb, int min_prb, int q_idx,
                      hcs_tbs_fn tbs_fn, void *tbs_ctx);

#ifdef __cplusplus
}
#endif

#endif /* HCS_BACKLOG_H */
