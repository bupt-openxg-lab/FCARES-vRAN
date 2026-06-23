/* hcs_backlog 单元测试: 验证 predicted-commitment drain/add / feasibility / select_prb.
 * 编译: gcc -I <oai_mac_dir> hcs_model.c hcs_backlog.c hcs_backlog_selftest.c -lm -o t && ./t
 */
#include "hcs_backlog.h"
#include <stdio.h>
#include <math.h>

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); failures++; } } while (0)
#define CLOSE(a, b) (fabs((a) - (b)) < 1e-9)

/* mock TBS/CodeBlocks: 随 nb_rb 单调增, CodeBlocks 落在模型已有的 1..~24 范围
 * (近似真实: 273RB ~ 23 CB, 123RB ~ 10 CB, 5RB ~ 1 CB) */
static void mock_tbs(int nb_rb, int nb_symbol, int mcs, int round,
                     void *ctx, double *out_TBS, int *out_CodeBlocks)
{
  (void)mcs; (void)round; (void)ctx;
  int cb = (int)(nb_rb * 0.085 + 0.5);
  if (cb < 1) cb = 1;
  if (cb > 24) cb = 24;
  *out_TBS = (double)cb * 8448.0 / 8.0;      /* bytes, 与 CodeBlocks 一致 */
  (void)nb_symbol;
  *out_CodeBlocks = cb;
}

int main(void)
{
  hcs_backlog_t b;
  hcs_backlog_init(&b, HCS_BUDGET_US, HCS_DEADLINE_US);  /* B=500, D=2500 */

  /* 1) predicted-commitment: final grant 后 add, 无 grant slot 只 drain */
  CHECK(CLOSE(hcs_backlog_get(&b), 0.0), "init backlog=0");
  hcs_backlog_add(&b, 1100.0);
  CHECK(CLOSE(hcs_backlog_get(&b), 1100.0), "commit grant L=1100");
  hcs_backlog_drain(&b);
  CHECK(CLOSE(hcs_backlog_get(&b), 600.0), "one no-grant slot drains B=500");
  hcs_backlog_add(&b, 900.0);
  CHECK(CLOSE(hcs_backlog_get(&b), 1500.0), "second grant adds after drain");
  hcs_backlog_drain_slots(&b, 2);
  CHECK(CLOSE(hcs_backlog_get(&b), 500.0), "two no-grant slots drain 1000");
  hcs_backlog_drain_slots(&b, 2);
  CHECK(CLOSE(hcs_backlog_get(&b), 0.0), "drain clamps at zero");

  /* 2) feasibility & grant_budget at c=2000 */
  hcs_backlog_reset(&b);
  hcs_backlog_add(&b, 2000.0);
  CHECK(CLOSE(hcs_backlog_get(&b), 2000.0), "backlog=2000");
  CHECK(CLOSE(hcs_backlog_grant_budget(&b), 500.0), "grant_budget = D-c = 500");
  CHECK(hcs_backlog_feasible(&b, 400.0) == 1, "L=400: 2000+400 < 2500 feasible");
  CHECK(hcs_backlog_feasible(&b, 600.0) == 0, "L=600: 2000+600 !< 2500 infeasible");
  CHECK(hcs_backlog_project(&b, 600.0) > hcs_backlog_project(&b, 100.0), "project monotonic in L");
  double before_select = hcs_backlog_get(&b);
  (void)hcs_select_prb(&b, HCS_STATE_XXHIGH, 20, 13, 0, 273, 1, 1, mock_tbs, NULL);
  CHECK(CLOSE(hcs_backlog_get(&b), before_select), "select_prb/cap does not mutate backlog");

  /* 3) select_prb: backlog 越高, 可行 RB 越小 (单调不增); 高 backlog 应触发降 RB */
  int prev = 9999, reduced = 0;
  printf("select_prb sweep (state=XXHIGH, mcs=20, sym=13, requested=273, q_idx=1[p70]):\n");
  for (int i = 0; i <= 6; i++) {
    hcs_backlog_reset(&b);
    double c = i * 400.0;                 /* 0,400,...,2400 */
    if (c > 0) hcs_backlog_add(&b, c);     /* 令 backlog=c */
    int rb = hcs_select_prb(&b, HCS_STATE_XXHIGH, 20, 13, 0, 273, 1, 1, mock_tbs, NULL);
    printf("  backlog=%6.0f grant_budget=%6.0f -> feasible_rb=%d\n",
           hcs_backlog_get(&b), hcs_backlog_grant_budget(&b), rb);
    CHECK(rb <= prev, "feasible_rb non-increasing as backlog grows");
    if (rb != HCS_NO_FEASIBLE_PRB && rb < 273) reduced = 1;
    if (rb != HCS_NO_FEASIBLE_PRB) prev = rb;
  }
  CHECK(reduced == 1, "high backlog triggers RB reduction (select_prb < requested)");

  hcs_backlog_reset(&b);
  int rb0 = hcs_select_prb(&b, HCS_STATE_XXHIGH, 20, 13, 0, 273, 1, 1, mock_tbs, NULL);
  CHECK(rb0 == 273, "at backlog=0 full requested PRB feasible");

  if (failures == 0) printf("ALL_OK\n");
  else printf("FAILURES=%d\n", failures);
  return failures == 0 ? 0 : 1;
}
