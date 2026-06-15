/* hcs_backlog.c —— 见 hcs_backlog.h */
#include "hcs_backlog.h"

void hcs_backlog_init(hcs_backlog_t *b, double budget_us, double deadline_us)
{
  b->backlog_us = 0.0;
  b->budget_us = budget_us;
  b->deadline_us = deadline_us;
}

void hcs_backlog_reset(hcs_backlog_t *b)
{
  b->backlog_us = 0.0;
}

double hcs_backlog_get(const hcs_backlog_t *b)
{
  return b->backlog_us;
}

/* legacy: measured 模型 (c=max(0,c+L-B), 一步排空+加). 现决策不再用, 保留备查/标定. */
double hcs_backlog_update(hcs_backlog_t *b, double l_actual_us)
{
  double c = b->backlog_us + l_actual_us - b->budget_us;
  if (c < 0.0) c = 0.0;
  b->backlog_us = c;
  return c;
}

/* predicted-commitment 模型: 每 slot 排空 B (服务速率) */
void hcs_backlog_drain(hcs_backlog_t *b)
{
  double c = b->backlog_us - b->budget_us;
  b->backlog_us = c < 0.0 ? 0.0 : c;
}

void hcs_backlog_drain_slots(hcs_backlog_t *b, int slots)
{
  if (slots <= 0)
    return;
  double c = b->backlog_us - b->budget_us * (double)slots;
  b->backlog_us = c < 0.0 ? 0.0 : c;
}

/* 每个已调度 grant 把其预测计算量加入 backlog (前向承诺) */
void hcs_backlog_add(hcs_backlog_t *b, double l_pred_us)
{
  if (l_pred_us > 0.0)
    b->backlog_us += l_pred_us;
}

double hcs_backlog_project(const hcs_backlog_t *b, double l_us)
{
  return b->backlog_us + l_us;   /* 排空已单独做; 投影 = 当前 backlog + 新 grant 预测 */
}

double hcs_backlog_grant_budget(const hcs_backlog_t *b)
{
  double m = b->deadline_us - b->backlog_us;   /* 本 slot 还能容纳的最大预测计算量 */
  return m < 0.0 ? 0.0 : m;
}

int hcs_backlog_feasible(const hcs_backlog_t *b, double l_pred_us)
{
  return (b->backlog_us + l_pred_us) < b->deadline_us;   /* 排空已单独做, 不再减 B */
}

int hcs_grant_feasible(const hcs_backlog_t *b, hcs_state_t state,
                       double TBS, double mcs, double nb_rb, double nb_symbol,
                       double round, int CodeBlocks, int q_idx)
{
  double l_pred = hcs_predict_total(state, TBS, mcs, nb_rb, nb_symbol, round, CodeBlocks, q_idx);
  return hcs_backlog_feasible(b, l_pred);
}

static int rb_is_feasible(const hcs_backlog_t *b, hcs_state_t state, int mcs, int nb_symbol,
                          int round, int nb_rb, int q_idx, hcs_tbs_fn tbs_fn, void *tbs_ctx)
{
  double TBS = 0.0;
  int CodeBlocks = 1;
  if (nb_rb < 1) return 0;
  tbs_fn(nb_rb, nb_symbol, mcs, round, tbs_ctx, &TBS, &CodeBlocks);
  return hcs_grant_feasible(b, state, TBS, (double)mcs, (double)nb_rb,
                            (double)nb_symbol, (double)round, CodeBlocks, q_idx);
}

int hcs_select_prb(const hcs_backlog_t *b, hcs_state_t state, int mcs, int nb_symbol,
                   int round, int requested_prb, int min_prb, int q_idx,
                   hcs_tbs_fn tbs_fn, void *tbs_ctx)
{
  int left, right, ans = HCS_NO_FEASIBLE_PRB;

  if (min_prb < 1) min_prb = 1;
  if (requested_prb < min_prb) return HCS_NO_FEASIBLE_PRB;

  /* 1) 先看 requested 是否已可行 */
  if (rb_is_feasible(b, state, mcs, nb_symbol, round, requested_prb, q_idx, tbs_fn, tbs_ctx))
    return requested_prb;

  /* 2) 二分在 [min_prb, requested_prb-1] 找最大可行 PRB */
  left = min_prb;
  right = requested_prb - 1;
  while (left <= right) {
    int mid = left + (right - left) / 2;
    if (rb_is_feasible(b, state, mcs, nb_symbol, round, mid, q_idx, tbs_fn, tbs_ctx)) {
      ans = mid;
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  return ans;
}
