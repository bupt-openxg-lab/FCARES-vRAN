# HCS Update: Predicted-Commitment Backlog

## Problem

`log5` showed two inconsistent HCS behaviors:

- Adjacent scheduled UL slots could have different final grants, for example `273RB/25CB` and `249RB/23CB`, but HCS printed the same `sel_pred`.
- `backlog` did not change after a grant, and it could be reset when the target scheduling frame changed.

The root cause was that the online scheduler mixed two models:

- The online backlog was still driven by measured `L_actual`, which arrives after the PHY work and is delayed from the current scheduling decision.
- The scheduler reset backlog on `sched_frame` changes, so backlog could not continuously represent committed compute work across frames.
- HCS prediction/logging happened before `nr_find_nb_rb()`. At that point `max_rbSize` was only a cap. The final grant could later be reduced by buffer/TBS fitting, so `sel_pred` did not match the actual `rbSize/TBS/num_cb`.

## Change

The online HCS backlog is now a predicted-commitment model:

```text
source slot advance: c = max(0, c - B)
final grant commit: c = c + L_pred(final rbSize, final TBS, final num_cb)
```

This means:

- There is no per-frame or target-frame reset.
- Slots without DCI still drain backlog by `B`, so the next scheduling opportunity has higher remaining tolerance.
- `hcs_select_prb()` and HCS cap calculation only inspect/project backlog. They do not update it.
- Backlog is updated only after the scheduler has made the actual RB/TBS decision.

## Implementation Notes

- `hcs_advance_slot()` runs at the start of `nr_schedule_ulsch()`, before early returns. It consumes new FFT samples for the classifier and drains backlog for elapsed source slots.
- The old `L_actual` update path is no longer used by online scheduling. It is kept only as a legacy/helper function for offline comparison.
- New data grants now log both request/cap and final grant fields:
  - `req_*`: prediction for the original requested `max_rbSize`
  - `cap_rb`: HCS-selected cap
  - `sel_*`: final grant after `nr_find_nb_rb()`
  - `backlog_before/backlog_after`: state before and after final-grant commit
- BSR=0 grants and retransmissions also commit only after allocation succeeds. Retransmissions are not RB-capped by HCS, because HARQ requires TB-size consistency.

## Expected Log Behavior

For the observed case:

- A final `273RB/26122B/25CB` grant and a final `249RB/24078B/23CB` grant should print different `sel_pred` values.
- The second scheduled slot should see backlog affected by the previous grant commit, minus any elapsed source-slot drain.
- No HCS log should show target-frame-change backlog reset.
