/* leaf_model_wrapper.c */
#include "leaf_model_wrapper.h"
#include "leaf_model_exported.h"

int threshhold = 700;

static int clamp_min(int value, int min_value) {
    return (value < min_value) ? min_value : value;
}

int predict_cost_p70(int mcs, int nb_symbol, int nb_rb, int round) {
    return LeafModelExported_predict_runtime_cost_p70(mcs, nb_symbol, nb_rb, round);
}

int is_prb_feasible(int mcs, int nb_symbol, int nb_rb, int round, int threshold) {
    if (nb_rb < 1) {
        return 0;
    }
    return predict_cost_p70(mcs, nb_symbol, nb_rb, round) <= threshold;
}

int select_prb_with_bounds(int mcs,
                           int nb_symbol,
                           int requested_prb,
                           int round,
                           int threshold,
                           int min_prb,
                           int local_fixup_window) {
    int left;
    int right;
    int ans = SELECT_PRB_NO_FEASIBLE;
    int best;
    int prb;

    min_prb = clamp_min(min_prb, 1);
    local_fixup_window = clamp_min(local_fixup_window, 0);

    if (requested_prb < min_prb) {
        return SELECT_PRB_NO_FEASIBLE;
    }

    /* 1) 先检查当前 PRB */
    if (is_prb_feasible(mcs, nb_symbol, requested_prb, round, threshold)) {
        return requested_prb;
    }

    /* 2) 不满足则在 [min_prb, requested_prb - 1] 中二分，找最大的可行 PRB */
    left = min_prb;
    right = requested_prb - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;
        int feasible = is_prb_feasible(mcs, nb_symbol, mid, round, threshold);

        if (feasible) {
            ans = mid;
            left = mid + 1;   /* 继续向右找更接近阈值的 */
        } else {
            right = mid - 1;
        }
    }

    if (ans == SELECT_PRB_NO_FEASIBLE) {
        return SELECT_PRB_NO_FEASIBLE;
    }

    /* 3) 局部修正：防止树模型局部不单调 */
    best = ans;
    for (prb = ans + 1;
         prb <= requested_prb - 1 && prb <= ans + local_fixup_window;
         ++prb) {
        if (is_prb_feasible(mcs, nb_symbol, prb, round, threshold)) {
            best = prb;
        }
    }

    return best;
}

int select_prb(int mcs, int nb_symbol, int requested_prb, int round) {
    return select_prb_with_bounds(mcs,
                                  nb_symbol,
                                  requested_prb,
                                  round,
                                  threshhold,
                                  SELECT_PRB_DEFAULT_MIN,
                                  SELECT_PRB_LOCAL_FIXUP_WINDOW);
}