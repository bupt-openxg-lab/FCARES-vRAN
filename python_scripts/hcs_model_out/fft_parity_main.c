#include "hcs_state_classifier.h"
#include <stdio.h>
#include <math.h>
int main(void) {
  FILE *fp = fopen("fft_parity_data.txt", "r");
  if (!fp) { printf("NO_DATA\n"); return 2; }
  hcs_fft_classifier_t c; hcs_classifier_init(&c);
  int prev_file = -1, file_id, py_interf; double fft, py_feat;
  long n = 0, mismatch = 0; double maxfeatdiff = 0.0;
  while (fscanf(fp, "%d %lf %lf %d", &file_id, &fft, &py_feat, &py_interf) == 4) {
    if (file_id != prev_file) { hcs_classifier_init(&c); prev_file = file_id; }
    hcs_classifier_push(&c, fft);
    double cf = hcs_classifier_feature(&c);
    int ci = hcs_classifier_interf(&c);
    double d = fabs(cf - py_feat); if (d > maxfeatdiff) maxfeatdiff = d;
    if (ci != py_interf) mismatch++;
    n++;
  }
  fclose(fp);
  printf("n=%ld mismatch=%ld max_feat_diff=%.3e\n", n, mismatch, maxfeatdiff);
  if (mismatch == 0 && maxfeatdiff < 1e-6) { printf("PARITY_OK\n"); return 0; }
  printf("PARITY_FAIL\n"); return 1;
}
