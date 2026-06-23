#include "hcs_state_classifier.h"
#include <stdio.h>
#include <math.h>
int main(void) {
  FILE *fp = fopen("fft_parity_data2.txt", "r");
  if (!fp) { printf("NO_DATA\n"); return 2; }
  hcs_fft_classifier_t c; hcs_classifier_init(&c, HCS_CLF_MEAN_THRESHOLD);
  int prev_file = -1, file_id, a_py, b_py; double fft, mean_py;
  long n = 0, mmA = 0, mmB = 0; double maxfeat = 0.0;
  while (fscanf(fp, "%d %lf %lf %d %d", &file_id, &fft, &mean_py, &a_py, &b_py) == 5) {
    if (file_id != prev_file) { hcs_classifier_init(&c, HCS_CLF_MEAN_THRESHOLD); prev_file = file_id; }
    hcs_classifier_push(&c, fft);
    hcs_fft_feats_t f = hcs_classifier_feats(&c);
    double d = fabs(f.mean - mean_py); if (d > maxfeat) maxfeat = d;
    if (hcs_classifier_interf_mode(&c, HCS_CLF_MEAN_THRESHOLD) != a_py) mmA++;
    if (hcs_classifier_interf_mode(&c, HCS_CLF_TREE) != b_py) mmB++;
    n++;
  }
  fclose(fp);
  printf("n=%ld mismatch_modeA=%ld mismatch_modeB=%ld max_mean_diff=%.3e\n", n, mmA, mmB, maxfeat);
  if (mmA == 0 && mmB == 0 && maxfeat < 1e-6) { printf("PARITY_OK\n"); return 0; }
  printf("PARITY_FAIL\n"); return 1;
}
