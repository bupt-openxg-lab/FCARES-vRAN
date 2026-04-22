/* leaf_model_wrapper.h */
#ifndef LEAF_MODEL_WRAPPER_H
#define LEAF_MODEL_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

enum {
    SELECT_PRB_NO_FEASIBLE = -1,
    SELECT_PRB_DEFAULT_MIN = 1,
    SELECT_PRB_LOCAL_FIXUP_WINDOW = 4,
};

int predict_cost_p70(int mcs, int nb_symbol, int nb_rb, int round);
int is_prb_feasible(int mcs, int nb_symbol, int nb_rb, int round, int threshold);
int select_prb(int mcs, int nb_symbol, int requested_prb, int round);
int select_prb_with_bounds(int mcs,
                           int nb_symbol,
                           int requested_prb,
                           int round,
                           int threshold,
                           int min_prb,
                           int local_fixup_window);

#ifdef __cplusplus
}
#endif

#endif