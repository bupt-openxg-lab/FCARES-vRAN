# Concordia baseline 交叉评估结果


### within/random  |  module = decode[observable]

```
    dataset    state          model cons_mode    r2    mae   rmse  coverage  overprov_us  underprov_us
        toy      ALL      concordia       max 0.914 48.575 63.241     1.000      307.333        49.735
        toy      ALL      concordia       p70 0.914 48.575 63.241     0.701       23.531        53.375
        toy      ALL grouped_linear       p70 0.914 48.536 63.241     0.701       23.398        53.566
        toy NO_CACHE      concordia       max 0.918 56.319 61.738     1.000      370.859         0.000
        toy NO_CACHE      concordia       p70 0.918 56.319 61.738     0.976       80.484        21.265
        toy NO_CACHE grouped_linear       p70 0.985 16.719 25.998     0.698        7.579        18.252
        toy      LOW      concordia       max 0.970 27.353 35.829     1.000      332.031        46.220
        toy      LOW      concordia       p70 0.970 27.353 35.829     0.919       44.725        26.179
        toy      LOW grouped_linear       p70 0.979 20.189 29.880     0.706       10.680        19.903
        toy   XXHIGH      concordia       max 0.822 72.618 91.226     0.999      253.298        16.834
        toy   XXHIGH      concordia       p70 0.822 72.618 91.226     0.141      -53.749        66.787
        toy   XXHIGH grouped_linear       p70 0.934 39.648 55.702     0.700       19.591        42.079
integration      ALL      concordia       max 0.975 37.003 55.327     0.999      303.575        48.784
integration      ALL      concordia       p70 0.975 37.003 55.327     0.692       12.328        45.795
integration      ALL grouped_linear       p70 0.975 37.093 55.262     0.696       12.862        45.650
integration NO_CACHE      concordia       max 0.987 30.891 38.169     1.000      380.649         0.000
integration NO_CACHE      concordia       p70 0.987 30.891 38.169     0.847       31.486        24.007
integration NO_CACHE grouped_linear       p70 0.990 23.109 33.119     0.711       14.965        20.934
integration      LOW      concordia       max 0.985 27.418 41.131     1.000      342.584        78.290
integration      LOW      concordia       p70 0.985 27.418 41.131     0.656        6.248        32.038
integration      LOW grouped_linear       p70 0.986 26.896 40.363     0.707       15.061        26.139
integration   XXHIGH      concordia       max 0.945 56.336 86.104     0.999      303.611        42.890
integration   XXHIGH      concordia       p70 0.945 56.336 86.104     0.390      -28.922        67.014
integration   XXHIGH grouped_linear       p70 0.963 50.338 70.256     0.694       27.262        48.634
```


### within/random  |  module = frontend

```
    dataset    state          model cons_mode    r2    mae   rmse  coverage  overprov_us  underprov_us
        toy      ALL      concordia       max 0.568 45.121 60.665     1.000      242.577        16.287
        toy      ALL      concordia       p70 0.568 45.121 60.665     0.698       19.633        49.093
        toy      ALL grouped_linear       p70 0.564 45.626 60.884     0.697       21.633        48.593
        toy NO_CACHE      concordia       max 0.463 46.011 56.352     1.000      277.524         0.000
        toy NO_CACHE      concordia       p70 0.463 46.011 56.352     0.977       61.088        38.858
        toy NO_CACHE grouped_linear       p70 0.747 29.151 38.663     0.702       19.856        20.402
        toy      LOW      concordia       max 0.695 33.389 43.910     1.000      243.867        44.270
        toy      LOW      concordia       p70 0.695 33.389 43.910     0.785       25.870        26.275
        toy      LOW grouped_linear       p70 0.703 32.549 43.393     0.688       16.291        30.488
        toy   XXHIGH      concordia       max 0.337 61.352 82.517     0.999      185.480        22.448
        toy   XXHIGH      concordia       p70 0.337 61.352 82.517     0.285      -33.248        59.559
        toy   XXHIGH grouped_linear       p70 0.628 46.415 61.783     0.704       31.553        39.930
integration      ALL      concordia       max 0.726 39.274 58.051     0.999      257.615        19.269
integration      ALL      concordia       p70 0.726 39.274 58.051     0.696       17.636        41.226
integration      ALL grouped_linear       p70 0.718 41.973 58.945     0.699       21.193        40.759
integration NO_CACHE      concordia       max 0.779 34.683 48.320     1.000      256.613         0.000
integration NO_CACHE      concordia       p70 0.779 34.683 48.320     0.865       38.589        29.731
integration NO_CACHE grouped_linear       p70 0.795 35.117 46.619     0.708       23.924        26.074
integration      LOW      concordia       max 0.772 34.398 48.249     0.999      232.602         8.345
integration      LOW      concordia       p70 0.772 34.398 48.249     0.688       17.151        28.253
integration      LOW grouped_linear       p70 0.767 35.153 48.710     0.700       23.036        27.945
integration   XXHIGH      concordia       max 0.622 51.575 76.998     0.999      203.195        37.797
integration   XXHIGH      concordia       p70 0.622 51.575 76.998     0.495       -7.170        56.005
integration   XXHIGH grouped_linear       p70 0.672 51.315 71.691     0.695       13.167        65.083
```


### within/prb_holdout  |  module = decode[observable]

```
    dataset    state          model cons_mode    r2     mae    rmse  coverage  overprov_us  underprov_us
        toy      ALL      concordia       max 0.751  84.368 107.424     0.965      195.261        43.309
        toy      ALL      concordia       p70 0.751  84.368 107.424     0.232      -52.879        82.968
        toy      ALL grouped_linear       p70 0.833  63.392  88.004     0.709       38.471        53.714
        toy NO_CACHE      concordia       max 0.932  48.241  55.884     1.000      245.103        32.140
        toy NO_CACHE      concordia       p70 0.932  48.241  55.884     0.325       -4.685        34.411
        toy NO_CACHE grouped_linear       p70 0.946  39.563  50.012     0.664       20.960        29.060
        toy      LOW      concordia       max 0.853  68.763  78.883     0.998      208.753        47.113
        toy      LOW      concordia       p70 0.853  68.763  78.883     0.221      -40.341        63.317
        toy      LOW grouped_linear       p70 0.966  28.233  37.690     0.736       16.425        28.662
        toy   XXHIGH      concordia       max 0.430 139.839 162.107     0.892      127.405        43.246
        toy   XXHIGH      concordia       p70 0.430 139.839 162.107     0.145     -117.943       143.312
        toy   XXHIGH grouped_linear       p70 0.889  49.749  71.480     0.681       22.187        48.201
integration      ALL      concordia       max 0.804 130.212 153.752     0.970      171.303        72.422
integration      ALL      concordia       p70 0.804 130.212 153.752     0.455       -6.259       118.949
integration      ALL grouped_linear       p70 0.963  53.089  67.156     0.749       36.212        41.967
integration NO_CACHE      concordia       max 0.828 120.673 138.378     0.999      193.837        40.589
integration NO_CACHE      concordia       p70 0.828 120.673 138.378     0.430       11.067        89.026
integration NO_CACHE grouped_linear       p70 0.979  38.542  48.784     0.839       31.090        25.629
integration      LOW      concordia       max 0.813 128.701 147.566     0.992      172.908       103.260
integration      LOW      concordia       p70 0.813 128.701 147.566     0.444       -5.738       114.373
integration      LOW grouped_linear       p70 0.979  34.293  49.067     0.700       17.041        31.012
integration   XXHIGH      concordia       max 0.767 144.777 178.219     0.905      139.756        69.830
integration   XXHIGH      concordia       p70 0.767 144.777 178.219     0.494      -30.138       168.397
integration   XXHIGH grouped_linear       p70 0.943  63.779  88.500     0.481       -5.357        66.327
```


### within/prb_holdout  |  module = frontend

```
    dataset    state          model cons_mode     r2    mae    rmse  coverage  overprov_us  underprov_us
        toy      ALL      concordia       max  0.500 49.981  64.961     0.998      231.338        31.124
        toy      ALL      concordia       p70  0.500 49.981  64.961     0.726       27.523        53.801
        toy      ALL grouped_linear       p70  0.563 45.882  60.765     0.704       24.504        47.695
        toy NO_CACHE      concordia       max  0.379 50.536  60.708     1.000      268.874         0.000
        toy NO_CACHE      concordia       p70  0.379 50.536  60.708     0.932       64.094        26.191
        toy NO_CACHE grouped_linear       p70  0.745 29.426  38.882     0.644       16.940        21.018
        toy      LOW      concordia       max  0.575 40.349  51.488     0.999      238.022        21.342
        toy      LOW      concordia       p70  0.575 40.349  51.488     0.803       33.682        41.711
        toy      LOW grouped_linear       p70  0.687 33.000  44.158     0.703       20.613        31.607
        toy   XXHIGH      concordia       max  0.362 60.209  81.162     0.995      181.676        32.346
        toy   XXHIGH      concordia       p70  0.362 60.209  81.162     0.408      -20.465        61.893
        toy   XXHIGH grouped_linear       p70  0.616 47.430  62.989     0.707       33.811        41.312
integration      ALL      concordia       max -0.053 89.985 113.387     0.989      194.448        35.194
integration      ALL      concordia       p70 -0.053 89.985 113.387     0.687       55.062        56.579
integration      ALL grouped_linear       p70  0.508 60.815  77.499     0.784       50.388        37.593
integration NO_CACHE      concordia       max -0.283 91.341 116.956     0.997      214.581         6.894
integration NO_CACHE      concordia       p70 -0.283 91.341 116.956     0.745       71.468        39.401
integration NO_CACHE grouped_linear       p70  0.018 85.145 102.305     0.717       75.292        18.024
integration      LOW      concordia       max -0.138 85.156 107.672     0.996      197.143        25.736
integration      LOW      concordia       p70 -0.138 85.156 107.672     0.665       57.240        42.365
integration      LOW grouped_linear       p70  0.554 52.826  67.425     0.752       46.177        24.877
integration   XXHIGH      concordia       max  0.158 95.088 116.148     0.970      164.560        39.853
integration   XXHIGH      concordia       p70  0.158 95.088 116.148     0.634       32.064        87.100
integration   XXHIGH grouped_linear       p70  0.659 52.520  73.877     0.722       14.716        78.403
```


### cross/toy->integration  |  module = decode[observable]

```
    dataset    state            model cons_mode    r2    mae    rmse  coverage  overprov_us  underprov_us
integration      ALL        concordia       max 0.960 45.996  69.226     0.999      327.121        25.712
integration      ALL        concordia       p70 0.960 45.996  69.226     0.536       -6.141        54.963
integration      ALL concordia_online       p70 0.971 40.378  58.511     0.708       16.843        47.637
integration      ALL   grouped_linear       p70 0.970 40.043  60.493     0.694       13.424        51.142
integration NO_CACHE        concordia       max 0.982 35.065  44.463     1.000      354.677         0.000
integration NO_CACHE        concordia       p70 0.982 35.065  44.463     0.685       16.006        35.862
integration NO_CACHE concordia_online       p70 0.985 32.556  41.476     0.781       26.450        30.114
integration NO_CACHE   grouped_linear       p70 0.983 31.427  43.823     0.374      -14.252        35.254
integration      LOW        concordia       max 0.973 38.429  56.058     1.000      328.812        50.543
integration      LOW        concordia       p70 0.973 38.429  56.058     0.530       -5.353        44.211
integration      LOW concordia_online       p70 0.980 33.087  48.026     0.723       16.473        34.638
integration      LOW   grouped_linear       p70 0.980 32.273  48.554     0.539       -4.872        39.179
integration   XXHIGH        concordia       max 0.924 69.032 101.814     0.997      289.929        23.143
integration   XXHIGH        concordia       p70 0.924 69.032 101.814     0.352      -35.345        76.193
integration   XXHIGH concordia_online       p70 0.948 59.844  84.227     0.579        8.841        63.424
integration   XXHIGH   grouped_linear       p70 0.949 63.006  83.588     0.685       27.203        63.738
```


### cross/toy->integration  |  module = frontend

```
    dataset    state            model cons_mode    r2    mae   rmse  coverage  overprov_us  underprov_us
integration      ALL        concordia       max 0.694 45.363 61.101     1.000      282.559        45.634
integration      ALL        concordia       p70 0.694 45.363 61.101     0.758       38.084        39.762
integration      ALL concordia_online       p70 0.731 41.136 57.326     0.713       24.153        36.938
integration      ALL   grouped_linear       p70 0.689 45.979 61.550     0.737       34.726        32.413
integration NO_CACHE        concordia       max 0.691 45.267 57.393     1.000      306.217         0.000
integration NO_CACHE        concordia       p70 0.691 45.267 57.393     0.896       57.455        35.587
integration NO_CACHE concordia_online       p70 0.781 37.454 48.370     0.831       39.989        28.972
integration NO_CACHE   grouped_linear       p70 0.777 36.395 48.800     0.658       13.766        31.205
integration      LOW        concordia       max 0.726 38.071 52.800     1.000      282.552        23.650
integration      LOW        concordia       p70 0.726 38.071 52.800     0.815       38.698        32.113
integration      LOW concordia_online       p70 0.758 35.828 49.602     0.780       29.668        29.721
integration      LOW   grouped_linear       p70 0.720 41.362 53.399     0.623       24.883        22.039
integration   XXHIGH        concordia       max 0.662 54.073 73.507     0.999      252.608        48.077
integration   XXHIGH        concordia       p70 0.662 54.073 73.507     0.516       12.829        44.340
integration   XXHIGH concordia_online       p70 0.661 54.777 73.554     0.577       30.420        35.530
integration   XXHIGH   grouped_linear       p70 0.563 62.640 83.482     0.846       71.524        37.212
```


### cross/integration->toy  |  module = decode[observable]

```
dataset    state            model cons_mode    r2     mae    rmse  coverage  overprov_us  underprov_us
    toy      ALL        concordia       max 0.848  68.383  83.856     0.941      177.156        32.303
    toy      ALL        concordia       p70 0.848  68.383  83.856     0.570       10.209        69.356
    toy      ALL concordia_online       p70 0.909  50.179  64.947     0.686       23.327        54.196
    toy      ALL   grouped_linear       p70 0.836  69.227  87.181     0.566        8.188        72.311
    toy NO_CACHE        concordia       max 0.875  65.599  75.907     0.997      231.871         7.804
    toy NO_CACHE        concordia       p70 0.875  65.599  75.907     0.812       59.789        41.646
    toy NO_CACHE concordia_online       p70 0.966  28.644  39.544     0.743       22.024        24.168
    toy NO_CACHE   grouped_linear       p70 0.947  39.115  49.563     0.753       24.447        36.775
    toy      LOW        concordia       max 0.897  53.093  66.076     0.966      192.050        26.788
    toy      LOW        concordia       p70 0.897  53.093  66.076     0.666       23.374        49.824
    toy      LOW concordia_online       p70 0.965  28.328  38.750     0.697       15.466        25.215
    toy      LOW   grouped_linear       p70 0.878  57.420  71.730     0.609       18.375        55.132
    toy   XXHIGH        concordia       max 0.756  87.865 106.149     0.855      102.584        34.305
    toy   XXHIGH        concordia       p70 0.756  87.865 106.149     0.209      -57.008        85.302
    toy   XXHIGH concordia_online       p70 0.907  48.391  65.362     0.573        5.365        49.933
    toy   XXHIGH   grouped_linear       p70 0.263 131.194 184.437     0.171     -104.611       135.115
```


### cross/integration->toy  |  module = frontend

```
dataset    state            model cons_mode    r2    mae    rmse  coverage  overprov_us  underprov_us
    toy      ALL        concordia       max 0.358 55.817  73.613     0.874       98.307        55.792
    toy      ALL        concordia       p70 0.358 55.817  73.613     0.419      -11.252        52.934
    toy      ALL concordia_online       p70 0.559 45.543  61.038     0.658       16.272        47.279
    toy      ALL   grouped_linear       p70 0.551 45.885  61.556     0.626       13.695        49.304
    toy NO_CACHE        concordia       max 0.422 44.997  58.597     0.998      138.839        51.098
    toy NO_CACHE        concordia       p70 0.422 44.997  58.597     0.748       25.990        34.219
    toy NO_CACHE concordia_online       p70 0.703 32.656  41.976     0.712       23.220        21.207
    toy NO_CACHE   grouped_linear       p70 0.715 30.448  41.125     0.840       34.759        27.448
    toy      LOW        concordia       max 0.493 45.192  56.184     0.938      105.341        18.147
    toy      LOW        concordia       p70 0.493 45.192  56.184     0.335       -4.718        32.246
    toy      LOW concordia_online       p70 0.687 34.017  44.189     0.589       14.686        24.286
    toy      LOW   grouped_linear       p70 0.667 34.857  45.549     0.662       23.809        26.757
    toy   XXHIGH        concordia       max 0.013 79.930 100.974     0.663       44.898        63.580
    toy   XXHIGH        concordia       p70 0.013 79.930 100.974     0.143      -60.407        77.185
    toy   XXHIGH concordia_online       p70 0.559 52.019  67.527     0.526        9.454        45.472
    toy   XXHIGH   grouped_linear       p70 0.496 54.312  72.156     0.426      -22.840        62.873
```

## 头条: 保守预测覆盖率 (目标 0.70) —— 越接近且不塌陷越好

```
model                   concordia  concordia_online  grouped_linear
scenario                                                           
cross/integration->toy      0.570             0.686           0.566
cross/toy->integration      0.536             0.708           0.694
within/prb_holdout          0.344               NaN           0.729
within/random               0.697               NaN           0.698
```

## dcor 特征排序 (Algorithm 1)

```
    dataset             module  rank         feature  dcor
        toy decode[observable]     1             TBS 0.936
        toy decode[observable]     2           nb_rb 0.735
        toy decode[observable]     3       nb_symbol 0.586
        toy decode[observable]     4             mcs 0.369
        toy decode[observable]     5           round 0.000
        toy     decode[oracle]     1             TBS 0.936
        toy     decode[oracle]     2 total_iteration 0.934
        toy     decode[oracle]     3           nb_rb 0.735
        toy     decode[oracle]     4       nb_symbol 0.586
        toy     decode[oracle]     5             mcs 0.369
        toy     decode[oracle]     6          snr_db 0.236
        toy     decode[oracle]     7           round 0.000
        toy           frontend     1       nb_symbol 0.523
        toy           frontend     2           nb_rb 0.509
integration decode[observable]     1             TBS 0.994
integration decode[observable]     2           nb_rb 0.757
integration decode[observable]     3             mcs 0.658
integration decode[observable]     4       nb_symbol 0.475
integration decode[observable]     5           round 0.000
integration     decode[oracle]     1             TBS 0.994
integration     decode[oracle]     2 total_iteration 0.984
integration     decode[oracle]     3           nb_rb 0.757
integration     decode[oracle]     4             mcs 0.658
integration     decode[oracle]     5          snr_db 0.512
integration     decode[oracle]     6       nb_symbol 0.475
integration     decode[oracle]     7           round 0.000
integration           frontend     1           nb_rb 0.583
integration           frontend     2       nb_symbol 0.528
```
