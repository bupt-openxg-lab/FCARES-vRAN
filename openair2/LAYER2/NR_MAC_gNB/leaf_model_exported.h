#ifndef LEAFMODELEXPORTED_H
#define LEAFMODELEXPORTED_H

#ifdef __cplusplus
extern "C" {
#endif

#define LEAFMODELEXPORTED_NUM_FEATURES 4

/* Feature order:
 * mcs, nb_symbol, nb_rb, round
 */

int LeafModelExported_num_features(void);
const char *LeafModelExported_feature_name(int idx);
int LeafModelExported_predict_leaf_id(int mcs, int nb_symbol, int nb_rb, int round);
int LeafModelExported_predict_runtime_cost_p70(int mcs, int nb_symbol, int nb_rb, int round);

#ifdef __cplusplus
}
#endif

#endif  /* LEAFMODELEXPORTED_H */
