#include "leaf_model_exported.h"

#include <math.h>

static const char *kFeatureNames[] = {
    "mcs",
    "nb_symbol",
    "nb_rb",
    "round"
};

int LeafModelExported_num_features(void) {
    return LEAFMODELEXPORTED_NUM_FEATURES;
}

const char *LeafModelExported_feature_name(int idx) {
    if (idx < 0 || idx >= LEAFMODELEXPORTED_NUM_FEATURES) {
        return "";
    }
    return kFeatureNames[idx];
}

int LeafModelExported_predict_leaf_id(int mcs, int nb_symbol, int nb_rb, int round) {
    /* node 0: if (nb_rb <= 152.5) -> 1 else 614 */
    if (nb_rb <= 152.5) {
        /* node 1: if (mcs <= 9.5) -> 2 else 225 */
        if (mcs <= 9.5) {
            /* node 2: if (nb_rb <= 58.35) -> 3 else 48 */
            if (nb_rb <= 58.5) {
                /* node 3: if (nb_rb <= 15.5) -> 4 else 7 */
                if (nb_rb <= 15.5) {
                    /* node 4: if (nb_symbol <= 12.5) -> 5 else 6 */
                    if (nb_symbol <= 12.5) {
                        return 5;
                    } else {
                        return 6;
                    }
                } else {
                    /* node 7: if (mcs <= 7.5) -> 8 else 35 */
                    if (mcs <= 7.5) {
                        /* node 8: if (nb_symbol <= 7.5) -> 9 else 14 */
                        if (nb_symbol <= 7.5) {
                            /* node 9: if (mcs <= 6.5) -> 10 else 11 */
                            if (mcs <= 6.5) {
                                return 10;
                            } else {
                                /* node 11: if (nb_rb <= 54.5) -> 12 else 13 */
                                if (nb_rb <= 54.5) {
                                    return 12;
                                } else {
                                    return 13;
                                }
                            }
                        } else {
                            /* node 14: if (mcs <= 6.5) -> 15 else 24 */
                            if (mcs <= 6.5) {
                                /* node 15: if (nb_rb <= 54.5) -> 16 else 19 */
                                if (nb_rb <= 54.5) {
                                    /* node 16: if (nb_rb <= 52.5) -> 17 else 18 */
                                    if (nb_rb <= 52.5) {
                                        return 17;
                                    } else {
                                        return 18;
                                    }
                                } else {
                                    /* node 19: if (nb_rb <= 56.5) -> 20 else 23 */
                                    if (nb_rb <= 56.5) {
                                        /* node 20: if (nb_rb <= 55.5) -> 21 else 22 */
                                        if (nb_rb <= 55.5) {
                                            return 21;
                                        } else {
                                            return 22;
                                        }
                                    } else {
                                        return 23;
                                    }
                                }
                            } else {
                                /* node 24: if (nb_rb <= 54.5) -> 25 else 30 */
                                if (nb_rb <= 54.5) {
                                    /* node 25: if (nb_rb <= 51.5) -> 26 else 27 */
                                    if (nb_rb <= 51.5) {
                                        return 26;
                                    } else {
                                        /* node 27: if (nb_rb <= 52.5) -> 28 else 29 */
                                        if (nb_rb <= 52.5) {
                                            return 28;
                                        } else {
                                            return 29;
                                        }
                                    }
                                } else {
                                    /* node 30: if (nb_rb <= 56.5) -> 31 else 32 */
                                    if (nb_rb <= 56.5) {
                                        return 31;
                                    } else {
                                        /* node 32: if (nb_rb <= 57.5) -> 33 else 34 */
                                        if (nb_rb <= 57.5) {
                                            return 33;
                                        } else {
                                            return 34;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 35: if (nb_symbol <= 7.5) -> 36 else 39 */
                        if (nb_symbol <= 7.5) {
                            /* node 36: if (nb_rb <= 50.5) -> 37 else 38 */
                            if (nb_rb <= 50.5) {
                                return 37;
                            } else {
                                return 38;
                            }
                        } else {
                            /* node 39: if (nb_rb <= 51.5) -> 40 else 41 */
                            if (nb_rb <= 51.5) {
                                return 40;
                            } else {
                                /* node 41: if (nb_rb <= 56.5) -> 42 else 47 */
                                if (nb_rb <= 56.5) {
                                    /* node 42: if (mcs <= 8.5) -> 43 else 46 */
                                    if (mcs <= 8.5) {
                                        /* node 43: if (nb_rb <= 54.5) -> 44 else 45 */
                                        if (nb_rb <= 54.5) {
                                            return 44;
                                        } else {
                                            return 45;
                                        }
                                    } else {
                                        return 46;
                                    }
                                } else {
                                    return 47;
                                }
                            }
                        }
                    }
                }
            } else {
                /* node 48: if (nb_symbol <= 7.5) -> 49 else 110 */
                if (nb_symbol <= 7.5) {
                    /* node 49: if (nb_rb <= 108.5) -> 50 else 81 */
                    if (nb_rb <= 108.5) {
                        /* node 50: if (mcs <= 6.5) -> 51 else 66 */
                        if (mcs <= 6.5) {
                            /* node 51: if (nb_rb <= 74.5) -> 52 else 57 */
                            if (nb_rb <= 74.5) {
                                /* node 52: if (nb_rb <= 63.5) -> 53 else 54 */
                                if (nb_rb <= 63.5) {
                                    return 53;
                                } else {
                                    /* node 54: if (nb_rb <= 67.5) -> 55 else 56 */
                                    if (nb_rb <= 67.5) {
                                        return 55;
                                    } else {
                                        return 56;
                                    }
                                }
                            } else {
                                /* node 57: if (nb_rb <= 95.5) -> 58 else 63 */
                                if (nb_rb <= 95.5) {
                                    /* node 58: if (nb_rb <= 90.5) -> 59 else 62 */
                                    if (nb_rb <= 90.5) {
                                        /* node 59: if (nb_rb <= 81.5) -> 60 else 61 */
                                        if (nb_rb <= 81.5) {
                                            return 60;
                                        } else {
                                            return 61;
                                        }
                                    } else {
                                        return 62;
                                    }
                                } else {
                                    /* node 63: if (nb_rb <= 102.5) -> 64 else 65 */
                                    if (nb_rb <= 102.5) {
                                        return 64;
                                    } else {
                                        return 65;
                                    }
                                }
                            }
                        } else {
                            /* node 66: if (nb_rb <= 62.5) -> 67 else 68 */
                            if (nb_rb <= 62.5) {
                                return 67;
                            } else {
                                /* node 68: if (mcs <= 8.5) -> 69 else 76 */
                                if (mcs <= 8.5) {
                                    /* node 69: if (nb_rb <= 93.5) -> 70 else 73 */
                                    if (nb_rb <= 93.5) {
                                        /* node 70: if (nb_rb <= 70.5) -> 71 else 72 */
                                        if (nb_rb <= 70.5) {
                                            return 71;
                                        } else {
                                            return 72;
                                        }
                                    } else {
                                        /* node 73: if (mcs <= 7.5) -> 74 else 75 */
                                        if (mcs <= 7.5) {
                                            return 74;
                                        } else {
                                            return 75;
                                        }
                                    }
                                } else {
                                    /* node 76: if (nb_rb <= 93.5) -> 77 else 80 */
                                    if (nb_rb <= 93.5) {
                                        /* node 77: if (nb_rb <= 79.5) -> 78 else 79 */
                                        if (nb_rb <= 79.5) {
                                            return 78;
                                        } else {
                                            return 79;
                                        }
                                    } else {
                                        return 80;
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 81: if (mcs <= 6.5) -> 82 else 91 */
                        if (mcs <= 6.5) {
                            /* node 82: if (nb_rb <= 145.5) -> 83 else 90 */
                            if (nb_rb <= 145.5) {
                                /* node 83: if (nb_rb <= 117.5) -> 84 else 85 */
                                if (nb_rb <= 117.5) {
                                    return 84;
                                } else {
                                    /* node 85: if (nb_rb <= 126.5) -> 86 else 87 */
                                    if (nb_rb <= 126.5) {
                                        return 86;
                                    } else {
                                        /* node 87: if (nb_rb <= 131.5) -> 88 else 89 */
                                        if (nb_rb <= 131.5) {
                                            return 88;
                                        } else {
                                            return 89;
                                        }
                                    }
                                }
                            } else {
                                return 90;
                            }
                        } else {
                            /* node 91: if (nb_rb <= 124.5) -> 92 else 101 */
                            if (nb_rb <= 124.5) {
                                /* node 92: if (mcs <= 7.5) -> 93 else 98 */
                                if (mcs <= 7.5) {
                                    /* node 93: if (nb_rb <= 114.5) -> 94 else 95 */
                                    if (nb_rb <= 114.5) {
                                        return 94;
                                    } else {
                                        /* node 95: if (nb_rb <= 118.5) -> 96 else 97 */
                                        if (nb_rb <= 118.5) {
                                            return 96;
                                        } else {
                                            return 97;
                                        }
                                    }
                                } else {
                                    /* node 98: if (nb_rb <= 115.5) -> 99 else 100 */
                                    if (nb_rb <= 115.5) {
                                        return 99;
                                    } else {
                                        return 100;
                                    }
                                }
                            } else {
                                /* node 101: if (mcs <= 8.5) -> 102 else 109 */
                                if (mcs <= 8.5) {
                                    /* node 102: if (nb_rb <= 140.5) -> 103 else 106 */
                                    if (nb_rb <= 140.5) {
                                        /* node 103: if (nb_rb <= 137.5) -> 104 else 105 */
                                        if (nb_rb <= 137.5) {
                                            return 104;
                                        } else {
                                            return 105;
                                        }
                                    } else {
                                        /* node 106: if (nb_rb <= 145.5) -> 107 else 108 */
                                        if (nb_rb <= 145.5) {
                                            return 107;
                                        } else {
                                            return 108;
                                        }
                                    }
                                } else {
                                    return 109;
                                }
                            }
                        }
                    }
                } else {
                    /* node 110: if (nb_rb <= 117.5) -> 111 else 170 */
                    if (nb_rb <= 117.5) {
                        /* node 111: if (nb_rb <= 97.5) -> 112 else 143 */
                        if (nb_rb <= 97.5) {
                            /* node 112: if (nb_rb <= 68.5) -> 113 else 128 */
                            if (nb_rb <= 68.5) {
                                /* node 113: if (mcs <= 6.5) -> 114 else 121 */
                                if (mcs <= 6.5) {
                                    /* node 114: if (nb_rb <= 64.5) -> 115 else 118 */
                                    if (nb_rb <= 64.5) {
                                        /* node 115: if (nb_rb <= 60.5) -> 116 else 117 */
                                        if (nb_rb <= 60.5) {
                                            return 116;
                                        } else {
                                            return 117;
                                        }
                                    } else {
                                        /* node 118: if (nb_rb <= 66.5) -> 119 else 120 */
                                        if (nb_rb <= 66.5) {
                                            return 119;
                                        } else {
                                            return 120;
                                        }
                                    }
                                } else {
                                    /* node 121: if (nb_rb <= 64.5) -> 122 else 125 */
                                    if (nb_rb <= 64.5) {
                                        /* node 122: if (mcs <= 8.5) -> 123 else 124 */
                                        if (mcs <= 8.5) {
                                            return 123;
                                        } else {
                                            return 124;
                                        }
                                    } else {
                                        /* node 125: if (mcs <= 8.5) -> 126 else 127 */
                                        if (mcs <= 8.5) {
                                            return 126;
                                        } else {
                                            return 127;
                                        }
                                    }
                                }
                            } else {
                                /* node 128: if (nb_rb <= 79.5) -> 129 else 136 */
                                if (nb_rb <= 79.5) {
                                    /* node 129: if (mcs <= 6.5) -> 130 else 133 */
                                    if (mcs <= 6.5) {
                                        /* node 130: if (nb_rb <= 75.5) -> 131 else 132 */
                                        if (nb_rb <= 75.5) {
                                            return 131;
                                        } else {
                                            return 132;
                                        }
                                    } else {
                                        /* node 133: if (mcs <= 8.5) -> 134 else 135 */
                                        if (mcs <= 8.5) {
                                            return 134;
                                        } else {
                                            return 135;
                                        }
                                    }
                                } else {
                                    /* node 136: if (mcs <= 6.5) -> 137 else 140 */
                                    if (mcs <= 6.5) {
                                        /* node 137: if (nb_rb <= 92.5) -> 138 else 139 */
                                        if (nb_rb <= 92.5) {
                                            return 138;
                                        } else {
                                            return 139;
                                        }
                                    } else {
                                        /* node 140: if (mcs <= 7.5) -> 141 else 142 */
                                        if (mcs <= 7.5) {
                                            return 141;
                                        } else {
                                            return 142;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 143: if (mcs <= 7.5) -> 144 else 157 */
                            if (mcs <= 7.5) {
                                /* node 144: if (mcs <= 6.5) -> 145 else 150 */
                                if (mcs <= 6.5) {
                                    /* node 145: if (nb_rb <= 115.5) -> 146 else 149 */
                                    if (nb_rb <= 115.5) {
                                        /* node 146: if (nb_rb <= 104.5) -> 147 else 148 */
                                        if (nb_rb <= 104.5) {
                                            return 147;
                                        } else {
                                            return 148;
                                        }
                                    } else {
                                        return 149;
                                    }
                                } else {
                                    /* node 150: if (nb_rb <= 109.5) -> 151 else 154 */
                                    if (nb_rb <= 109.5) {
                                        /* node 151: if (nb_rb <= 101.5) -> 152 else 153 */
                                        if (nb_rb <= 101.5) {
                                            return 152;
                                        } else {
                                            return 153;
                                        }
                                    } else {
                                        /* node 154: if (nb_rb <= 113.5) -> 155 else 156 */
                                        if (nb_rb <= 113.5) {
                                            return 155;
                                        } else {
                                            return 156;
                                        }
                                    }
                                }
                            } else {
                                /* node 157: if (nb_rb <= 107.5) -> 158 else 165 */
                                if (nb_rb <= 107.5) {
                                    /* node 158: if (mcs <= 8.5) -> 159 else 162 */
                                    if (mcs <= 8.5) {
                                        /* node 159: if (nb_rb <= 102.5) -> 160 else 161 */
                                        if (nb_rb <= 102.5) {
                                            return 160;
                                        } else {
                                            return 161;
                                        }
                                    } else {
                                        /* node 162: if (nb_rb <= 102.5) -> 163 else 164 */
                                        if (nb_rb <= 102.5) {
                                            return 163;
                                        } else {
                                            return 164;
                                        }
                                    }
                                } else {
                                    /* node 165: if (nb_rb <= 115.5) -> 166 else 169 */
                                    if (nb_rb <= 115.5) {
                                        /* node 166: if (mcs <= 8.5) -> 167 else 168 */
                                        if (mcs <= 8.5) {
                                            return 167;
                                        } else {
                                            return 168;
                                        }
                                    } else {
                                        return 169;
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 170: if (mcs <= 6.5) -> 171 else 198 */
                        if (mcs <= 6.5) {
                            /* node 171: if (nb_rb <= 137.5) -> 172 else 185 */
                            if (nb_rb <= 137.5) {
                                /* node 172: if (nb_rb <= 128.5) -> 173 else 178 */
                                if (nb_rb <= 128.5) {
                                    /* node 173: if (nb_rb <= 120.5) -> 174 else 175 */
                                    if (nb_rb <= 120.5) {
                                        return 174;
                                    } else {
                                        /* node 175: if (nb_rb <= 126.5) -> 176 else 177 */
                                        if (nb_rb <= 126.5) {
                                            return 176;
                                        } else {
                                            return 177;
                                        }
                                    }
                                } else {
                                    /* node 178: if (nb_rb <= 133.5) -> 179 else 182 */
                                    if (nb_rb <= 133.5) {
                                        /* node 179: if (nb_rb <= 131.5) -> 180 else 181 */
                                        if (nb_rb <= 131.5) {
                                            return 180;
                                        } else {
                                            return 181;
                                        }
                                    } else {
                                        /* node 182: if (nb_rb <= 135.5) -> 183 else 184 */
                                        if (nb_rb <= 135.5) {
                                            return 183;
                                        } else {
                                            return 184;
                                        }
                                    }
                                }
                            } else {
                                /* node 185: if (nb_rb <= 148.5) -> 186 else 193 */
                                if (nb_rb <= 148.5) {
                                    /* node 186: if (nb_rb <= 144.5) -> 187 else 190 */
                                    if (nb_rb <= 144.5) {
                                        /* node 187: if (nb_rb <= 142.5) -> 188 else 189 */
                                        if (nb_rb <= 142.5) {
                                            return 188;
                                        } else {
                                            return 189;
                                        }
                                    } else {
                                        /* node 190: if (nb_rb <= 146.5) -> 191 else 192 */
                                        if (nb_rb <= 146.5) {
                                            return 191;
                                        } else {
                                            return 192;
                                        }
                                    }
                                } else {
                                    /* node 193: if (nb_rb <= 150.5) -> 194 else 195 */
                                    if (nb_rb <= 150.5) {
                                        return 194;
                                    } else {
                                        /* node 195: if (nb_rb <= 151.5) -> 196 else 197 */
                                        if (nb_rb <= 151.5) {
                                            return 196;
                                        } else {
                                            return 197;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 198: if (nb_rb <= 143.5) -> 199 else 214 */
                            if (nb_rb <= 143.5) {
                                /* node 199: if (nb_rb <= 129.5) -> 200 else 207 */
                                if (nb_rb <= 129.5) {
                                    /* node 200: if (nb_rb <= 118.5) -> 201 else 204 */
                                    if (nb_rb <= 118.5) {
                                        /* node 201: if (mcs <= 7.5) -> 202 else 203 */
                                        if (mcs <= 7.5) {
                                            return 202;
                                        } else {
                                            return 203;
                                        }
                                    } else {
                                        /* node 204: if (nb_rb <= 127.5) -> 205 else 206 */
                                        if (nb_rb <= 127.5) {
                                            return 205;
                                        } else {
                                            return 206;
                                        }
                                    }
                                } else {
                                    /* node 207: if (mcs <= 7.5) -> 208 else 211 */
                                    if (mcs <= 7.5) {
                                        /* node 208: if (nb_rb <= 133.5) -> 209 else 210 */
                                        if (nb_rb <= 133.5) {
                                            return 209;
                                        } else {
                                            return 210;
                                        }
                                    } else {
                                        /* node 211: if (nb_rb <= 138.5) -> 212 else 213 */
                                        if (nb_rb <= 138.5) {
                                            return 212;
                                        } else {
                                            return 213;
                                        }
                                    }
                                }
                            } else {
                                /* node 214: if (mcs <= 8.5) -> 215 else 222 */
                                if (mcs <= 8.5) {
                                    /* node 215: if (mcs <= 7.5) -> 216 else 219 */
                                    if (mcs <= 7.5) {
                                        /* node 216: if (nb_rb <= 150.5) -> 217 else 218 */
                                        if (nb_rb <= 150.5) {
                                            return 217;
                                        } else {
                                            return 218;
                                        }
                                    } else {
                                        /* node 219: if (nb_rb <= 149.5) -> 220 else 221 */
                                        if (nb_rb <= 149.5) {
                                            return 220;
                                        } else {
                                            return 221;
                                        }
                                    }
                                } else {
                                    /* node 222: if (nb_rb <= 147.5) -> 223 else 224 */
                                    if (nb_rb <= 147.5) {
                                        return 223;
                                    } else {
                                        return 224;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            /* node 225: if (nb_symbol <= 7.5) -> 226 else 377 */
            if (nb_symbol <= 7.5) {
                /* node 226: if (nb_rb <= 115.5) -> 227 else 296 */
                if (nb_rb <= 115.5) {
                    /* node 227: if (mcs <= 18.5) -> 228 else 275 */
                    if (mcs <= 18.5) {
                        /* node 228: if (mcs <= 15.5) -> 229 else 258 */
                        if (mcs <= 15.5) {
                            /* node 229: if (nb_rb <= 75.5) -> 230 else 243 */
                            if (nb_rb <= 75.5) {
                                /* node 230: if (mcs <= 10.5) -> 231 else 236 */
                                if (mcs <= 10.5) {
                                    /* node 231: if (nb_rb <= 64.5) -> 232 else 235 */
                                    if (nb_rb <= 64.5) {
                                        /* node 232: if (nb_rb <= 57.5) -> 233 else 234 */
                                        if (nb_rb <= 57.5) {
                                            return 233;
                                        } else {
                                            return 234;
                                        }
                                    } else {
                                        return 235;
                                    }
                                } else {
                                    /* node 236: if (mcs <= 13.5) -> 237 else 240 */
                                    if (mcs <= 13.5) {
                                        /* node 237: if (nb_rb <= 62.5) -> 238 else 239 */
                                        if (nb_rb <= 62.5) {
                                            return 238;
                                        } else {
                                            return 239;
                                        }
                                    } else {
                                        /* node 240: if (nb_rb <= 63.5) -> 241 else 242 */
                                        if (nb_rb <= 63.5) {
                                            return 241;
                                        } else {
                                            return 242;
                                        }
                                    }
                                }
                            } else {
                                /* node 243: if (mcs <= 10.5) -> 244 else 251 */
                                if (mcs <= 10.5) {
                                    /* node 244: if (nb_rb <= 95.5) -> 245 else 248 */
                                    if (nb_rb <= 95.5) {
                                        /* node 245: if (nb_rb <= 84.5) -> 246 else 247 */
                                        if (nb_rb <= 84.5) {
                                            return 246;
                                        } else {
                                            return 247;
                                        }
                                    } else {
                                        /* node 248: if (nb_rb <= 106.5) -> 249 else 250 */
                                        if (nb_rb <= 106.5) {
                                            return 249;
                                        } else {
                                            return 250;
                                        }
                                    }
                                } else {
                                    /* node 251: if (nb_rb <= 86.5) -> 252 else 255 */
                                    if (nb_rb <= 86.5) {
                                        /* node 252: if (mcs <= 12.5) -> 253 else 254 */
                                        if (mcs <= 12.5) {
                                            return 253;
                                        } else {
                                            return 254;
                                        }
                                    } else {
                                        /* node 255: if (nb_rb <= 97.5) -> 256 else 257 */
                                        if (nb_rb <= 97.5) {
                                            return 256;
                                        } else {
                                            return 257;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 258: if (nb_rb <= 108.5) -> 259 else 272 */
                            if (nb_rb <= 108.5) {
                                /* node 259: if (mcs <= 16.5) -> 260 else 267 */
                                if (mcs <= 16.5) {
                                    /* node 260: if (nb_rb <= 59.5) -> 261 else 264 */
                                    if (nb_rb <= 59.5) {
                                        /* node 261: if (nb_rb <= 54.5) -> 262 else 263 */
                                        if (nb_rb <= 54.5) {
                                            return 262;
                                        } else {
                                            return 263;
                                        }
                                    } else {
                                        /* node 264: if (nb_rb <= 84.5) -> 265 else 266 */
                                        if (nb_rb <= 84.5) {
                                            return 265;
                                        } else {
                                            return 266;
                                        }
                                    }
                                } else {
                                    /* node 267: if (nb_rb <= 101.0) -> 268 else 271 */
                                    if (nb_rb <= 101) {
                                        /* node 268: if (nb_rb <= 59.5) -> 269 else 270 */
                                        if (nb_rb <= 59.5) {
                                            return 269;
                                        } else {
                                            return 270;
                                        }
                                    } else {
                                        return 271;
                                    }
                                }
                            } else {
                                /* node 272: if (mcs <= 16.5) -> 273 else 274 */
                                if (mcs <= 16.5) {
                                    return 273;
                                } else {
                                    return 274;
                                }
                            }
                        }
                    } else {
                        /* node 275: if (nb_rb <= 88.5) -> 276 else 287 */
                        if (nb_rb <= 88.5) {
                            /* node 276: if (nb_rb <= 60.5) -> 277 else 280 */
                            if (nb_rb <= 60.5) {
                                /* node 277: if (mcs <= 22.5) -> 278 else 279 */
                                if (mcs <= 22.5) {
                                    return 278;
                                } else {
                                    return 279;
                                }
                            } else {
                                /* node 280: if (mcs <= 20.5) -> 281 else 282 */
                                if (mcs <= 20.5) {
                                    return 281;
                                } else {
                                    /* node 282: if (nb_rb <= 77.5) -> 283 else 286 */
                                    if (nb_rb <= 77.5) {
                                        /* node 283: if (nb_rb <= 70.5) -> 284 else 285 */
                                        if (nb_rb <= 70.5) {
                                            return 284;
                                        } else {
                                            return 285;
                                        }
                                    } else {
                                        return 286;
                                    }
                                }
                            }
                        } else {
                            /* node 287: if (mcs <= 22.5) -> 288 else 293 */
                            if (mcs <= 22.5) {
                                /* node 288: if (mcs <= 20.5) -> 289 else 290 */
                                if (mcs <= 20.5) {
                                    return 289;
                                } else {
                                    /* node 290: if (nb_rb <= 103.5) -> 291 else 292 */
                                    if (nb_rb <= 103.5) {
                                        return 291;
                                    } else {
                                        return 292;
                                    }
                                }
                            } else {
                                /* node 293: if (nb_rb <= 103.5) -> 294 else 295 */
                                if (nb_rb <= 103.5) {
                                    return 294;
                                } else {
                                    return 295;
                                }
                            }
                        }
                    }
                } else {
                    /* node 296: if (mcs <= 13.5) -> 297 else 334 */
                    if (mcs <= 13.5) {
                        /* node 297: if (nb_rb <= 145.5) -> 298 else 323 */
                        if (nb_rb <= 145.5) {
                            /* node 298: if (nb_rb <= 138.5) -> 299 else 312 */
                            if (nb_rb <= 138.5) {
                                /* node 299: if (nb_rb <= 125.5) -> 300 else 305 */
                                if (nb_rb <= 125.5) {
                                    /* node 300: if (nb_rb <= 124.5) -> 301 else 304 */
                                    if (nb_rb <= 124.5) {
                                        /* node 301: if (nb_rb <= 120.5) -> 302 else 303 */
                                        if (nb_rb <= 120.5) {
                                            return 302;
                                        } else {
                                            return 303;
                                        }
                                    } else {
                                        return 304;
                                    }
                                } else {
                                    /* node 305: if (nb_rb <= 133.5) -> 306 else 309 */
                                    if (nb_rb <= 133.5) {
                                        /* node 306: if (mcs <= 10.5) -> 307 else 308 */
                                        if (mcs <= 10.5) {
                                            return 307;
                                        } else {
                                            return 308;
                                        }
                                    } else {
                                        /* node 309: if (mcs <= 12.5) -> 310 else 311 */
                                        if (mcs <= 12.5) {
                                            return 310;
                                        } else {
                                            return 311;
                                        }
                                    }
                                }
                            } else {
                                /* node 312: if (mcs <= 12.5) -> 313 else 320 */
                                if (mcs <= 12.5) {
                                    /* node 313: if (nb_rb <= 141.5) -> 314 else 317 */
                                    if (nb_rb <= 141.5) {
                                        /* node 314: if (mcs <= 11.5) -> 315 else 316 */
                                        if (mcs <= 11.5) {
                                            return 315;
                                        } else {
                                            return 316;
                                        }
                                    } else {
                                        /* node 317: if (mcs <= 11.5) -> 318 else 319 */
                                        if (mcs <= 11.5) {
                                            return 318;
                                        } else {
                                            return 319;
                                        }
                                    }
                                } else {
                                    /* node 320: if (nb_rb <= 141.5) -> 321 else 322 */
                                    if (nb_rb <= 141.5) {
                                        return 321;
                                    } else {
                                        return 322;
                                    }
                                }
                            }
                        } else {
                            /* node 323: if (mcs <= 12.5) -> 324 else 331 */
                            if (mcs <= 12.5) {
                                /* node 324: if (mcs <= 11.5) -> 325 else 326 */
                                if (mcs <= 11.5) {
                                    return 325;
                                } else {
                                    /* node 326: if (nb_rb <= 147.5) -> 327 else 328 */
                                    if (nb_rb <= 147.5) {
                                        return 327;
                                    } else {
                                        /* node 328: if (nb_rb <= 149.5) -> 329 else 330 */
                                        if (nb_rb <= 149.5) {
                                            return 329;
                                        } else {
                                            return 330;
                                        }
                                    }
                                }
                            } else {
                                /* node 331: if (nb_rb <= 148.5) -> 332 else 333 */
                                if (nb_rb <= 148.5) {
                                    return 332;
                                } else {
                                    return 333;
                                }
                            }
                        }
                    } else {
                        /* node 334: if (mcs <= 14.5) -> 335 else 350 */
                        if (mcs <= 14.5) {
                            /* node 335: if (nb_rb <= 128.5) -> 336 else 341 */
                            if (nb_rb <= 128.5) {
                                /* node 336: if (nb_rb <= 125.5) -> 337 else 340 */
                                if (nb_rb <= 125.5) {
                                    /* node 337: if (nb_rb <= 119.5) -> 338 else 339 */
                                    if (nb_rb <= 119.5) {
                                        return 338;
                                    } else {
                                        return 339;
                                    }
                                } else {
                                    return 340;
                                }
                            } else {
                                /* node 341: if (nb_rb <= 133.5) -> 342 else 343 */
                                if (nb_rb <= 133.5) {
                                    return 342;
                                } else {
                                    /* node 343: if (nb_rb <= 144.5) -> 344 else 347 */
                                    if (nb_rb <= 144.5) {
                                        /* node 344: if (nb_rb <= 137.5) -> 345 else 346 */
                                        if (nb_rb <= 137.5) {
                                            return 345;
                                        } else {
                                            return 346;
                                        }
                                    } else {
                                        /* node 347: if (nb_rb <= 148.5) -> 348 else 349 */
                                        if (nb_rb <= 148.5) {
                                            return 348;
                                        } else {
                                            return 349;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 350: if (mcs <= 17.5) -> 351 else 364 */
                            if (mcs <= 17.5) {
                                /* node 351: if (mcs <= 16.5) -> 352 else 359 */
                                if (mcs <= 16.5) {
                                    /* node 352: if (nb_rb <= 127.5) -> 353 else 356 */
                                    if (nb_rb <= 127.5) {
                                        /* node 353: if (nb_rb <= 123.5) -> 354 else 355 */
                                        if (nb_rb <= 123.5) {
                                            return 354;
                                        } else {
                                            return 355;
                                        }
                                    } else {
                                        /* node 356: if (nb_rb <= 144.5) -> 357 else 358 */
                                        if (nb_rb <= 144.5) {
                                            return 357;
                                        } else {
                                            return 358;
                                        }
                                    }
                                } else {
                                    /* node 359: if (nb_rb <= 140.5) -> 360 else 363 */
                                    if (nb_rb <= 140.5) {
                                        /* node 360: if (nb_rb <= 128.5) -> 361 else 362 */
                                        if (nb_rb <= 128.5) {
                                            return 361;
                                        } else {
                                            return 362;
                                        }
                                    } else {
                                        return 363;
                                    }
                                }
                            } else {
                                /* node 364: if (nb_rb <= 132.5) -> 365 else 370 */
                                if (nb_rb <= 132.5) {
                                    /* node 365: if (nb_rb <= 121.5) -> 366 else 367 */
                                    if (nb_rb <= 121.5) {
                                        return 366;
                                    } else {
                                        /* node 367: if (mcs <= 18.5) -> 368 else 369 */
                                        if (mcs <= 18.5) {
                                            return 368;
                                        } else {
                                            return 369;
                                        }
                                    }
                                } else {
                                    /* node 370: if (mcs <= 20.5) -> 371 else 374 */
                                    if (mcs <= 20.5) {
                                        /* node 371: if (mcs <= 18.5) -> 372 else 373 */
                                        if (mcs <= 18.5) {
                                            return 372;
                                        } else {
                                            return 373;
                                        }
                                    } else {
                                        /* node 374: if (mcs <= 22.5) -> 375 else 376 */
                                        if (mcs <= 22.5) {
                                            return 375;
                                        } else {
                                            return 376;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                /* node 377: if (nb_rb <= 100.5) -> 378 else 495 */
                if (nb_rb <= 100.5) {
                    /* node 378: if (mcs <= 16.5) -> 379 else 442 */
                    if (mcs <= 16.5) {
                        /* node 379: if (nb_rb <= 71.5) -> 380 else 411 */
                        if (nb_rb <= 71.5) {
                            /* node 380: if (nb_rb <= 55.5) -> 381 else 396 */
                            if (nb_rb <= 55.5) {
                                /* node 381: if (nb_rb <= 25.5) -> 382 else 389 */
                                if (nb_rb <= 25.5) {
                                    /* node 382: if (nb_rb <= 12.5) -> 383 else 386 */
                                    if (nb_rb <= 12.5) {
                                        /* node 383: if (nb_rb <= 7.5) -> 384 else 385 */
                                        if (nb_rb <= 7.5) {
                                            return 384;
                                        } else {
                                            return 385;
                                        }
                                    } else {
                                        /* node 386: if (nb_rb <= 17.5) -> 387 else 388 */
                                        if (nb_rb <= 17.5) {
                                            return 387;
                                        } else {
                                            return 388;
                                        }
                                    }
                                } else {
                                    /* node 389: if (mcs <= 14.5) -> 390 else 393 */
                                    if (mcs <= 14.5) {
                                        /* node 390: if (nb_rb <= 41.5) -> 391 else 392 */
                                        if (nb_rb <= 41.5) {
                                            return 391;
                                        } else {
                                            return 392;
                                        }
                                    } else {
                                        /* node 393: if (nb_rb <= 50.5) -> 394 else 395 */
                                        if (nb_rb <= 50.5) {
                                            return 394;
                                        } else {
                                            return 395;
                                        }
                                    }
                                }
                            } else {
                                /* node 396: if (mcs <= 13.5) -> 397 else 404 */
                                if (mcs <= 13.5) {
                                    /* node 397: if (nb_rb <= 63.5) -> 398 else 401 */
                                    if (nb_rb <= 63.5) {
                                        /* node 398: if (nb_rb <= 59.5) -> 399 else 400 */
                                        if (nb_rb <= 59.5) {
                                            return 399;
                                        } else {
                                            return 400;
                                        }
                                    } else {
                                        /* node 401: if (mcs <= 12.5) -> 402 else 403 */
                                        if (mcs <= 12.5) {
                                            return 402;
                                        } else {
                                            return 403;
                                        }
                                    }
                                } else {
                                    /* node 404: if (nb_rb <= 64.5) -> 405 else 408 */
                                    if (nb_rb <= 64.5) {
                                        /* node 405: if (nb_rb <= 59.5) -> 406 else 407 */
                                        if (nb_rb <= 59.5) {
                                            return 406;
                                        } else {
                                            return 407;
                                        }
                                    } else {
                                        /* node 408: if (round <= 0.5) -> 409 else 410 */
                                        if (round <= 0.5) {
                                            return 409;
                                        } else {
                                            return 410;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 411: if (nb_rb <= 84.5) -> 412 else 427 */
                            if (nb_rb <= 84.5) {
                                /* node 412: if (mcs <= 14.5) -> 413 else 420 */
                                if (mcs <= 14.5) {
                                    /* node 413: if (mcs <= 11.5) -> 414 else 417 */
                                    if (mcs <= 11.5) {
                                        /* node 414: if (nb_rb <= 81.5) -> 415 else 416 */
                                        if (nb_rb <= 81.5) {
                                            return 415;
                                        } else {
                                            return 416;
                                        }
                                    } else {
                                        /* node 417: if (round <= 0.5) -> 418 else 419 */
                                        if (round <= 0.5) {
                                            return 418;
                                        } else {
                                            return 419;
                                        }
                                    }
                                } else {
                                    /* node 420: if (nb_rb <= 76.5) -> 421 else 424 */
                                    if (nb_rb <= 76.5) {
                                        /* node 421: if (mcs <= 15.5) -> 422 else 423 */
                                        if (mcs <= 15.5) {
                                            return 422;
                                        } else {
                                            return 423;
                                        }
                                    } else {
                                        /* node 424: if (nb_rb <= 79.5) -> 425 else 426 */
                                        if (nb_rb <= 79.5) {
                                            return 425;
                                        } else {
                                            return 426;
                                        }
                                    }
                                }
                            } else {
                                /* node 427: if (mcs <= 13.5) -> 428 else 435 */
                                if (mcs <= 13.5) {
                                    /* node 428: if (nb_rb <= 90.5) -> 429 else 432 */
                                    if (nb_rb <= 90.5) {
                                        /* node 429: if (mcs <= 10.5) -> 430 else 431 */
                                        if (mcs <= 10.5) {
                                            return 430;
                                        } else {
                                            return 431;
                                        }
                                    } else {
                                        /* node 432: if (nb_rb <= 96.5) -> 433 else 434 */
                                        if (nb_rb <= 96.5) {
                                            return 433;
                                        } else {
                                            return 434;
                                        }
                                    }
                                } else {
                                    /* node 435: if (nb_rb <= 93.5) -> 436 else 439 */
                                    if (nb_rb <= 93.5) {
                                        /* node 436: if (mcs <= 14.5) -> 437 else 438 */
                                        if (mcs <= 14.5) {
                                            return 437;
                                        } else {
                                            return 438;
                                        }
                                    } else {
                                        /* node 439: if (mcs <= 15.5) -> 440 else 441 */
                                        if (mcs <= 15.5) {
                                            return 440;
                                        } else {
                                            return 441;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 442: if (nb_rb <= 71.5) -> 443 else 468 */
                        if (nb_rb <= 71.5) {
                            /* node 443: if (round <= 0.5) -> 444 else 459 */
                            if (round <= 0.5) {
                                /* node 444: if (nb_rb <= 61.5) -> 445 else 452 */
                                if (nb_rb <= 61.5) {
                                    /* node 445: if (mcs <= 17.5) -> 446 else 449 */
                                    if (mcs <= 17.5) {
                                        /* node 446: if (nb_rb <= 54.5) -> 447 else 448 */
                                        if (nb_rb <= 54.5) {
                                            return 447;
                                        } else {
                                            return 448;
                                        }
                                    } else {
                                        /* node 449: if (mcs <= 20.5) -> 450 else 451 */
                                        if (mcs <= 20.5) {
                                            return 450;
                                        } else {
                                            return 451;
                                        }
                                    }
                                } else {
                                    /* node 452: if (mcs <= 18.5) -> 453 else 456 */
                                    if (mcs <= 18.5) {
                                        /* node 453: if (nb_rb <= 67.5) -> 454 else 455 */
                                        if (nb_rb <= 67.5) {
                                            return 454;
                                        } else {
                                            return 455;
                                        }
                                    } else {
                                        /* node 456: if (mcs <= 22.5) -> 457 else 458 */
                                        if (mcs <= 22.5) {
                                            return 457;
                                        } else {
                                            return 458;
                                        }
                                    }
                                }
                            } else {
                                /* node 459: if (mcs <= 22.5) -> 460 else 467 */
                                if (mcs <= 22.5) {
                                    /* node 460: if (nb_rb <= 61.5) -> 461 else 464 */
                                    if (nb_rb <= 61.5) {
                                        /* node 461: if (mcs <= 17.5) -> 462 else 463 */
                                        if (mcs <= 17.5) {
                                            return 462;
                                        } else {
                                            return 463;
                                        }
                                    } else {
                                        /* node 464: if (nb_rb <= 67.5) -> 465 else 466 */
                                        if (nb_rb <= 67.5) {
                                            return 465;
                                        } else {
                                            return 466;
                                        }
                                    }
                                } else {
                                    return 467;
                                }
                            }
                        } else {
                            /* node 468: if (round <= 0.5) -> 469 else 484 */
                            if (round <= 0.5) {
                                /* node 469: if (nb_rb <= 88.5) -> 470 else 477 */
                                if (nb_rb <= 88.5) {
                                    /* node 470: if (nb_rb <= 79.5) -> 471 else 474 */
                                    if (nb_rb <= 79.5) {
                                        /* node 471: if (mcs <= 25.5) -> 472 else 473 */
                                        if (mcs <= 25.5) {
                                            return 472;
                                        } else {
                                            return 473;
                                        }
                                    } else {
                                        /* node 474: if (mcs <= 20.5) -> 475 else 476 */
                                        if (mcs <= 20.5) {
                                            return 475;
                                        } else {
                                            return 476;
                                        }
                                    }
                                } else {
                                    /* node 477: if (nb_rb <= 94.5) -> 478 else 481 */
                                    if (nb_rb <= 94.5) {
                                        /* node 478: if (mcs <= 22.5) -> 479 else 480 */
                                        if (mcs <= 22.5) {
                                            return 479;
                                        } else {
                                            return 480;
                                        }
                                    } else {
                                        /* node 481: if (mcs <= 19.5) -> 482 else 483 */
                                        if (mcs <= 19.5) {
                                            return 482;
                                        } else {
                                            return 483;
                                        }
                                    }
                                }
                            } else {
                                /* node 484: if (mcs <= 22.5) -> 485 else 492 */
                                if (mcs <= 22.5) {
                                    /* node 485: if (nb_rb <= 88.5) -> 486 else 489 */
                                    if (nb_rb <= 88.5) {
                                        /* node 486: if (nb_rb <= 74.5) -> 487 else 488 */
                                        if (nb_rb <= 74.5) {
                                            return 487;
                                        } else {
                                            return 488;
                                        }
                                    } else {
                                        /* node 489: if (round <= 1.5) -> 490 else 491 */
                                        if (round <= 1.5) {
                                            return 490;
                                        } else {
                                            return 491;
                                        }
                                    }
                                } else {
                                    /* node 492: if (nb_rb <= 87.5) -> 493 else 494 */
                                    if (nb_rb <= 87.5) {
                                        return 493;
                                    } else {
                                        return 494;
                                    }
                                }
                            }
                        }
                    }
                } else {
                    /* node 495: if (mcs <= 16.5) -> 496 else 559 */
                    if (mcs <= 16.5) {
                        /* node 496: if (nb_rb <= 128.5) -> 497 else 528 */
                        if (nb_rb <= 128.5) {
                            /* node 497: if (mcs <= 13.5) -> 498 else 513 */
                            if (mcs <= 13.5) {
                                /* node 498: if (nb_rb <= 108.5) -> 499 else 506 */
                                if (nb_rb <= 108.5) {
                                    /* node 499: if (mcs <= 12.5) -> 500 else 503 */
                                    if (mcs <= 12.5) {
                                        /* node 500: if (round <= 0.5) -> 501 else 502 */
                                        if (round <= 0.5) {
                                            return 501;
                                        } else {
                                            return 502;
                                        }
                                    } else {
                                        /* node 503: if (nb_rb <= 103.5) -> 504 else 505 */
                                        if (nb_rb <= 103.5) {
                                            return 504;
                                        } else {
                                            return 505;
                                        }
                                    }
                                } else {
                                    /* node 506: if (mcs <= 11.5) -> 507 else 510 */
                                    if (mcs <= 11.5) {
                                        /* node 507: if (nb_rb <= 124.5) -> 508 else 509 */
                                        if (nb_rb <= 124.5) {
                                            return 508;
                                        } else {
                                            return 509;
                                        }
                                    } else {
                                        /* node 510: if (nb_rb <= 119.5) -> 511 else 512 */
                                        if (nb_rb <= 119.5) {
                                            return 511;
                                        } else {
                                            return 512;
                                        }
                                    }
                                }
                            } else {
                                /* node 513: if (nb_rb <= 111.5) -> 514 else 521 */
                                if (nb_rb <= 111.5) {
                                    /* node 514: if (mcs <= 14.5) -> 515 else 518 */
                                    if (mcs <= 14.5) {
                                        /* node 515: if (round <= 0.5) -> 516 else 517 */
                                        if (round <= 0.5) {
                                            return 516;
                                        } else {
                                            return 517;
                                        }
                                    } else {
                                        /* node 518: if (nb_rb <= 106.5) -> 519 else 520 */
                                        if (nb_rb <= 106.5) {
                                            return 519;
                                        } else {
                                            return 520;
                                        }
                                    }
                                } else {
                                    /* node 521: if (nb_rb <= 119.5) -> 522 else 525 */
                                    if (nb_rb <= 119.5) {
                                        /* node 522: if (mcs <= 14.5) -> 523 else 524 */
                                        if (mcs <= 14.5) {
                                            return 523;
                                        } else {
                                            return 524;
                                        }
                                    } else {
                                        /* node 525: if (mcs <= 15.5) -> 526 else 527 */
                                        if (mcs <= 15.5) {
                                            return 526;
                                        } else {
                                            return 527;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 528: if (mcs <= 13.5) -> 529 else 544 */
                            if (mcs <= 13.5) {
                                /* node 529: if (mcs <= 10.5) -> 530 else 537 */
                                if (mcs <= 10.5) {
                                    /* node 530: if (round <= 0.5) -> 531 else 534 */
                                    if (round <= 0.5) {
                                        /* node 531: if (nb_rb <= 138.5) -> 532 else 533 */
                                        if (nb_rb <= 138.5) {
                                            return 532;
                                        } else {
                                            return 533;
                                        }
                                    } else {
                                        /* node 534: if (nb_rb <= 138.5) -> 535 else 536 */
                                        if (nb_rb <= 138.5) {
                                            return 535;
                                        } else {
                                            return 536;
                                        }
                                    }
                                } else {
                                    /* node 537: if (nb_rb <= 142.5) -> 538 else 541 */
                                    if (nb_rb <= 142.5) {
                                        /* node 538: if (mcs <= 12.5) -> 539 else 540 */
                                        if (mcs <= 12.5) {
                                            return 539;
                                        } else {
                                            return 540;
                                        }
                                    } else {
                                        /* node 541: if (mcs <= 11.5) -> 542 else 543 */
                                        if (mcs <= 11.5) {
                                            return 542;
                                        } else {
                                            return 543;
                                        }
                                    }
                                }
                            } else {
                                /* node 544: if (nb_rb <= 142.5) -> 545 else 552 */
                                if (nb_rb <= 142.5) {
                                    /* node 545: if (mcs <= 14.5) -> 546 else 549 */
                                    if (mcs <= 14.5) {
                                        /* node 546: if (round <= 0.5) -> 547 else 548 */
                                        if (round <= 0.5) {
                                            return 547;
                                        } else {
                                            return 548;
                                        }
                                    } else {
                                        /* node 549: if (mcs <= 15.5) -> 550 else 551 */
                                        if (mcs <= 15.5) {
                                            return 550;
                                        } else {
                                            return 551;
                                        }
                                    }
                                } else {
                                    /* node 552: if (mcs <= 15.5) -> 553 else 556 */
                                    if (mcs <= 15.5) {
                                        /* node 553: if (mcs <= 14.5) -> 554 else 555 */
                                        if (mcs <= 14.5) {
                                            return 554;
                                        } else {
                                            return 555;
                                        }
                                    } else {
                                        /* node 556: if (nb_rb <= 145.5) -> 557 else 558 */
                                        if (nb_rb <= 145.5) {
                                            return 557;
                                        } else {
                                            return 558;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 559: if (nb_rb <= 120.5) -> 560 else 589 */
                        if (nb_rb <= 120.5) {
                            /* node 560: if (mcs <= 18.5) -> 561 else 576 */
                            if (mcs <= 18.5) {
                                /* node 561: if (nb_rb <= 112.5) -> 562 else 569 */
                                if (nb_rb <= 112.5) {
                                    /* node 562: if (round <= 0.5) -> 563 else 566 */
                                    if (round <= 0.5) {
                                        /* node 563: if (mcs <= 17.5) -> 564 else 565 */
                                        if (mcs <= 17.5) {
                                            return 564;
                                        } else {
                                            return 565;
                                        }
                                    } else {
                                        /* node 566: if (round <= 1.5) -> 567 else 568 */
                                        if (round <= 1.5) {
                                            return 567;
                                        } else {
                                            return 568;
                                        }
                                    }
                                } else {
                                    /* node 569: if (round <= 0.5) -> 570 else 573 */
                                    if (round <= 0.5) {
                                        /* node 570: if (mcs <= 17.5) -> 571 else 572 */
                                        if (mcs <= 17.5) {
                                            return 571;
                                        } else {
                                            return 572;
                                        }
                                    } else {
                                        /* node 573: if (nb_rb <= 116.5) -> 574 else 575 */
                                        if (nb_rb <= 116.5) {
                                            return 574;
                                        } else {
                                            return 575;
                                        }
                                    }
                                }
                            } else {
                                /* node 576: if (round <= 0.5) -> 577 else 584 */
                                if (round <= 0.5) {
                                    /* node 577: if (mcs <= 22.5) -> 578 else 581 */
                                    if (mcs <= 22.5) {
                                        /* node 578: if (mcs <= 20.5) -> 579 else 580 */
                                        if (mcs <= 20.5) {
                                            return 579;
                                        } else {
                                            return 580;
                                        }
                                    } else {
                                        /* node 581: if (mcs <= 26.5) -> 582 else 583 */
                                        if (mcs <= 26.5) {
                                            return 582;
                                        } else {
                                            return 583;
                                        }
                                    }
                                } else {
                                    /* node 584: if (mcs <= 23.5) -> 585 else 588 */
                                    if (mcs <= 23.5) {
                                        /* node 585: if (nb_rb <= 111.5) -> 586 else 587 */
                                        if (nb_rb <= 111.5) {
                                            return 586;
                                        } else {
                                            return 587;
                                        }
                                    } else {
                                        return 588;
                                    }
                                }
                            }
                        } else {
                            /* node 589: if (round <= 0.5) -> 590 else 605 */
                            if (round <= 0.5) {
                                /* node 590: if (nb_rb <= 137.5) -> 591 else 598 */
                                if (nb_rb <= 137.5) {
                                    /* node 591: if (mcs <= 18.5) -> 592 else 595 */
                                    if (mcs <= 18.5) {
                                        /* node 592: if (nb_rb <= 134.5) -> 593 else 594 */
                                        if (nb_rb <= 134.5) {
                                            return 593;
                                        } else {
                                            return 594;
                                        }
                                    } else {
                                        /* node 595: if (mcs <= 22.5) -> 596 else 597 */
                                        if (mcs <= 22.5) {
                                            return 596;
                                        } else {
                                            return 597;
                                        }
                                    }
                                } else {
                                    /* node 598: if (mcs <= 18.5) -> 599 else 602 */
                                    if (mcs <= 18.5) {
                                        /* node 599: if (nb_rb <= 143.5) -> 600 else 601 */
                                        if (nb_rb <= 143.5) {
                                            return 600;
                                        } else {
                                            return 601;
                                        }
                                    } else {
                                        /* node 602: if (mcs <= 27.5) -> 603 else 604 */
                                        if (mcs <= 27.5) {
                                            return 603;
                                        } else {
                                            return 604;
                                        }
                                    }
                                }
                            } else {
                                /* node 605: if (mcs <= 22.5) -> 606 else 611 */
                                if (mcs <= 22.5) {
                                    /* node 606: if (mcs <= 20.5) -> 607 else 610 */
                                    if (mcs <= 20.5) {
                                        /* node 607: if (nb_rb <= 130.5) -> 608 else 609 */
                                        if (nb_rb <= 130.5) {
                                            return 608;
                                        } else {
                                            return 609;
                                        }
                                    } else {
                                        return 610;
                                    }
                                } else {
                                    /* node 611: if (nb_rb <= 138.5) -> 612 else 613 */
                                    if (nb_rb <= 138.5) {
                                        return 612;
                                    } else {
                                        return 613;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        /* node 614: if (nb_symbol <= 7.5) -> 615 else 896 */
        if (nb_symbol <= 7.5) {
            /* node 615: if (mcs <= 13.5) -> 616 else 761 */
            if (mcs <= 13.5) {
                /* node 616: if (mcs <= 9.5) -> 617 else 668 */
                if (mcs <= 9.5) {
                    /* node 617: if (mcs <= 7.5) -> 618 else 647 */
                    if (mcs <= 7.5) {
                        /* node 618: if (nb_rb <= 270.5) -> 619 else 646 */
                        if (nb_rb <= 270.5) {
                            /* node 619: if (nb_rb <= 245.5) -> 620 else 635 */
                            if (nb_rb <= 245.5) {
                                /* node 620: if (nb_rb <= 165.5) -> 621 else 628 */
                                if (nb_rb <= 165.5) {
                                    /* node 621: if (mcs <= 6.5) -> 622 else 625 */
                                    if (mcs <= 6.5) {
                                        /* node 622: if (nb_rb <= 158.5) -> 623 else 624 */
                                        if (nb_rb <= 158.5) {
                                            return 623;
                                        } else {
                                            return 624;
                                        }
                                    } else {
                                        /* node 625: if (nb_rb <= 158.5) -> 626 else 627 */
                                        if (nb_rb <= 158.5) {
                                            return 626;
                                        } else {
                                            return 627;
                                        }
                                    }
                                } else {
                                    /* node 628: if (mcs <= 6.5) -> 629 else 632 */
                                    if (mcs <= 6.5) {
                                        /* node 629: if (nb_rb <= 188.5) -> 630 else 631 */
                                        if (nb_rb <= 188.5) {
                                            return 630;
                                        } else {
                                            return 631;
                                        }
                                    } else {
                                        /* node 632: if (nb_rb <= 229.5) -> 633 else 634 */
                                        if (nb_rb <= 229.5) {
                                            return 633;
                                        } else {
                                            return 634;
                                        }
                                    }
                                }
                            } else {
                                /* node 635: if (mcs <= 6.5) -> 636 else 641 */
                                if (mcs <= 6.5) {
                                    /* node 636: if (nb_rb <= 265.5) -> 637 else 640 */
                                    if (nb_rb <= 265.5) {
                                        /* node 637: if (nb_rb <= 253.5) -> 638 else 639 */
                                        if (nb_rb <= 253.5) {
                                            return 638;
                                        } else {
                                            return 639;
                                        }
                                    } else {
                                        return 640;
                                    }
                                } else {
                                    /* node 641: if (nb_rb <= 252.5) -> 642 else 643 */
                                    if (nb_rb <= 252.5) {
                                        return 642;
                                    } else {
                                        /* node 643: if (nb_rb <= 263.5) -> 644 else 645 */
                                        if (nb_rb <= 263.5) {
                                            return 644;
                                        } else {
                                            return 645;
                                        }
                                    }
                                }
                            }
                        } else {
                            return 646;
                        }
                    } else {
                        /* node 647: if (nb_rb <= 236.5) -> 648 else 661 */
                        if (nb_rb <= 236.5) {
                            /* node 648: if (nb_rb <= 214.5) -> 649 else 658 */
                            if (nb_rb <= 214.5) {
                                /* node 649: if (nb_rb <= 198.5) -> 650 else 655 */
                                if (nb_rb <= 198.5) {
                                    /* node 650: if (nb_rb <= 160.5) -> 651 else 652 */
                                    if (nb_rb <= 160.5) {
                                        return 651;
                                    } else {
                                        /* node 652: if (nb_rb <= 167.5) -> 653 else 654 */
                                        if (nb_rb <= 167.5) {
                                            return 653;
                                        } else {
                                            return 654;
                                        }
                                    }
                                } else {
                                    /* node 655: if (mcs <= 8.5) -> 656 else 657 */
                                    if (mcs <= 8.5) {
                                        return 656;
                                    } else {
                                        return 657;
                                    }
                                }
                            } else {
                                /* node 658: if (mcs <= 8.5) -> 659 else 660 */
                                if (mcs <= 8.5) {
                                    return 659;
                                } else {
                                    return 660;
                                }
                            }
                        } else {
                            /* node 661: if (nb_rb <= 266.5) -> 662 else 667 */
                            if (nb_rb <= 266.5) {
                                /* node 662: if (nb_rb <= 260.5) -> 663 else 666 */
                                if (nb_rb <= 260.5) {
                                    /* node 663: if (mcs <= 8.5) -> 664 else 665 */
                                    if (mcs <= 8.5) {
                                        return 664;
                                    } else {
                                        return 665;
                                    }
                                } else {
                                    return 666;
                                }
                            } else {
                                return 667;
                            }
                        }
                    }
                } else {
                    /* node 668: if (nb_rb <= 188.5) -> 669 else 716 */
                    if (nb_rb <= 188.5) {
                        /* node 669: if (mcs <= 11.5) -> 670 else 689 */
                        if (mcs <= 11.5) {
                            /* node 670: if (nb_rb <= 165.5) -> 671 else 678 */
                            if (nb_rb <= 165.5) {
                                /* node 671: if (mcs <= 10.5) -> 672 else 675 */
                                if (mcs <= 10.5) {
                                    /* node 672: if (nb_rb <= 159.5) -> 673 else 674 */
                                    if (nb_rb <= 159.5) {
                                        return 673;
                                    } else {
                                        return 674;
                                    }
                                } else {
                                    /* node 675: if (nb_rb <= 160.5) -> 676 else 677 */
                                    if (nb_rb <= 160.5) {
                                        return 676;
                                    } else {
                                        return 677;
                                    }
                                }
                            } else {
                                /* node 678: if (nb_rb <= 172.5) -> 679 else 682 */
                                if (nb_rb <= 172.5) {
                                    /* node 679: if (nb_rb <= 168.5) -> 680 else 681 */
                                    if (nb_rb <= 168.5) {
                                        return 680;
                                    } else {
                                        return 681;
                                    }
                                } else {
                                    /* node 682: if (mcs <= 10.5) -> 683 else 686 */
                                    if (mcs <= 10.5) {
                                        /* node 683: if (nb_rb <= 180.5) -> 684 else 685 */
                                        if (nb_rb <= 180.5) {
                                            return 684;
                                        } else {
                                            return 685;
                                        }
                                    } else {
                                        /* node 686: if (nb_rb <= 183.5) -> 687 else 688 */
                                        if (nb_rb <= 183.5) {
                                            return 687;
                                        } else {
                                            return 688;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 689: if (nb_rb <= 164.5) -> 690 else 701 */
                            if (nb_rb <= 164.5) {
                                /* node 690: if (mcs <= 12.5) -> 691 else 696 */
                                if (mcs <= 12.5) {
                                    /* node 691: if (nb_rb <= 156.5) -> 692 else 693 */
                                    if (nb_rb <= 156.5) {
                                        return 692;
                                    } else {
                                        /* node 693: if (nb_rb <= 159.5) -> 694 else 695 */
                                        if (nb_rb <= 159.5) {
                                            return 694;
                                        } else {
                                            return 695;
                                        }
                                    }
                                } else {
                                    /* node 696: if (nb_rb <= 160.5) -> 697 else 700 */
                                    if (nb_rb <= 160.5) {
                                        /* node 697: if (nb_rb <= 155.5) -> 698 else 699 */
                                        if (nb_rb <= 155.5) {
                                            return 698;
                                        } else {
                                            return 699;
                                        }
                                    } else {
                                        return 700;
                                    }
                                }
                            } else {
                                /* node 701: if (mcs <= 12.5) -> 702 else 709 */
                                if (mcs <= 12.5) {
                                    /* node 702: if (nb_rb <= 179.5) -> 703 else 706 */
                                    if (nb_rb <= 179.5) {
                                        /* node 703: if (nb_rb <= 170.5) -> 704 else 705 */
                                        if (nb_rb <= 170.5) {
                                            return 704;
                                        } else {
                                            return 705;
                                        }
                                    } else {
                                        /* node 706: if (nb_rb <= 185.5) -> 707 else 708 */
                                        if (nb_rb <= 185.5) {
                                            return 707;
                                        } else {
                                            return 708;
                                        }
                                    }
                                } else {
                                    /* node 709: if (nb_rb <= 172.5) -> 710 else 713 */
                                    if (nb_rb <= 172.5) {
                                        /* node 710: if (nb_rb <= 167.5) -> 711 else 712 */
                                        if (nb_rb <= 167.5) {
                                            return 711;
                                        } else {
                                            return 712;
                                        }
                                    } else {
                                        /* node 713: if (nb_rb <= 180.5) -> 714 else 715 */
                                        if (nb_rb <= 180.5) {
                                            return 714;
                                        } else {
                                            return 715;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 716: if (mcs <= 10.5) -> 717 else 734 */
                        if (mcs <= 10.5) {
                            /* node 717: if (nb_rb <= 209.5) -> 718 else 721 */
                            if (nb_rb <= 209.5) {
                                /* node 718: if (nb_rb <= 197.5) -> 719 else 720 */
                                if (nb_rb <= 197.5) {
                                    return 719;
                                } else {
                                    return 720;
                                }
                            } else {
                                /* node 721: if (nb_rb <= 244.5) -> 722 else 729 */
                                if (nb_rb <= 244.5) {
                                    /* node 722: if (nb_rb <= 229.5) -> 723 else 726 */
                                    if (nb_rb <= 229.5) {
                                        /* node 723: if (nb_rb <= 215.5) -> 724 else 725 */
                                        if (nb_rb <= 215.5) {
                                            return 724;
                                        } else {
                                            return 725;
                                        }
                                    } else {
                                        /* node 726: if (nb_rb <= 238.5) -> 727 else 728 */
                                        if (nb_rb <= 238.5) {
                                            return 727;
                                        } else {
                                            return 728;
                                        }
                                    }
                                } else {
                                    /* node 729: if (nb_rb <= 251.5) -> 730 else 731 */
                                    if (nb_rb <= 251.5) {
                                        return 730;
                                    } else {
                                        /* node 731: if (nb_rb <= 260.5) -> 732 else 733 */
                                        if (nb_rb <= 260.5) {
                                            return 732;
                                        } else {
                                            return 733;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 734: if (nb_rb <= 239.5) -> 735 else 748 */
                            if (nb_rb <= 239.5) {
                                /* node 735: if (mcs <= 12.5) -> 736 else 743 */
                                if (mcs <= 12.5) {
                                    /* node 736: if (nb_rb <= 219.5) -> 737 else 740 */
                                    if (nb_rb <= 219.5) {
                                        /* node 737: if (mcs <= 11.5) -> 738 else 739 */
                                        if (mcs <= 11.5) {
                                            return 738;
                                        } else {
                                            return 739;
                                        }
                                    } else {
                                        /* node 740: if (mcs <= 11.5) -> 741 else 742 */
                                        if (mcs <= 11.5) {
                                            return 741;
                                        } else {
                                            return 742;
                                        }
                                    }
                                } else {
                                    /* node 743: if (nb_rb <= 194.5) -> 744 else 745 */
                                    if (nb_rb <= 194.5) {
                                        return 744;
                                    } else {
                                        /* node 745: if (nb_rb <= 224.5) -> 746 else 747 */
                                        if (nb_rb <= 224.5) {
                                            return 746;
                                        } else {
                                            return 747;
                                        }
                                    }
                                }
                            } else {
                                /* node 748: if (mcs <= 12.5) -> 749 else 756 */
                                if (mcs <= 12.5) {
                                    /* node 749: if (nb_rb <= 250.5) -> 750 else 753 */
                                    if (nb_rb <= 250.5) {
                                        /* node 750: if (mcs <= 11.5) -> 751 else 752 */
                                        if (mcs <= 11.5) {
                                            return 751;
                                        } else {
                                            return 752;
                                        }
                                    } else {
                                        /* node 753: if (nb_rb <= 271.5) -> 754 else 755 */
                                        if (nb_rb <= 271.5) {
                                            return 754;
                                        } else {
                                            return 755;
                                        }
                                    }
                                } else {
                                    /* node 756: if (nb_rb <= 244.5) -> 757 else 758 */
                                    if (nb_rb <= 244.5) {
                                        return 757;
                                    } else {
                                        /* node 758: if (nb_rb <= 270.5) -> 759 else 760 */
                                        if (nb_rb <= 270.5) {
                                            return 759;
                                        } else {
                                            return 760;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                /* node 761: if (mcs <= 18.5) -> 762 else 857 */
                if (mcs <= 18.5) {
                    /* node 762: if (nb_rb <= 223.5) -> 763 else 814 */
                    if (nb_rb <= 223.5) {
                        /* node 763: if (mcs <= 16.5) -> 764 else 795 */
                        if (mcs <= 16.5) {
                            /* node 764: if (nb_rb <= 194.5) -> 765 else 780 */
                            if (nb_rb <= 194.5) {
                                /* node 765: if (nb_rb <= 173.5) -> 766 else 773 */
                                if (nb_rb <= 173.5) {
                                    /* node 766: if (mcs <= 14.5) -> 767 else 770 */
                                    if (mcs <= 14.5) {
                                        /* node 767: if (nb_rb <= 161.5) -> 768 else 769 */
                                        if (nb_rb <= 161.5) {
                                            return 768;
                                        } else {
                                            return 769;
                                        }
                                    } else {
                                        /* node 770: if (nb_rb <= 155.5) -> 771 else 772 */
                                        if (nb_rb <= 155.5) {
                                            return 771;
                                        } else {
                                            return 772;
                                        }
                                    }
                                } else {
                                    /* node 773: if (mcs <= 15.5) -> 774 else 777 */
                                    if (mcs <= 15.5) {
                                        /* node 774: if (nb_rb <= 186.5) -> 775 else 776 */
                                        if (nb_rb <= 186.5) {
                                            return 775;
                                        } else {
                                            return 776;
                                        }
                                    } else {
                                        /* node 777: if (nb_rb <= 180.5) -> 778 else 779 */
                                        if (nb_rb <= 180.5) {
                                            return 778;
                                        } else {
                                            return 779;
                                        }
                                    }
                                }
                            } else {
                                /* node 780: if (mcs <= 14.5) -> 781 else 788 */
                                if (mcs <= 14.5) {
                                    /* node 781: if (nb_rb <= 214.5) -> 782 else 785 */
                                    if (nb_rb <= 214.5) {
                                        /* node 782: if (nb_rb <= 198.5) -> 783 else 784 */
                                        if (nb_rb <= 198.5) {
                                            return 783;
                                        } else {
                                            return 784;
                                        }
                                    } else {
                                        /* node 785: if (nb_rb <= 219.5) -> 786 else 787 */
                                        if (nb_rb <= 219.5) {
                                            return 786;
                                        } else {
                                            return 787;
                                        }
                                    }
                                } else {
                                    /* node 788: if (nb_rb <= 216.5) -> 789 else 792 */
                                    if (nb_rb <= 216.5) {
                                        /* node 789: if (nb_rb <= 199.5) -> 790 else 791 */
                                        if (nb_rb <= 199.5) {
                                            return 790;
                                        } else {
                                            return 791;
                                        }
                                    } else {
                                        /* node 792: if (mcs <= 15.5) -> 793 else 794 */
                                        if (mcs <= 15.5) {
                                            return 793;
                                        } else {
                                            return 794;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 795: if (nb_rb <= 203.5) -> 796 else 809 */
                            if (nb_rb <= 203.5) {
                                /* node 796: if (nb_rb <= 178.5) -> 797 else 804 */
                                if (nb_rb <= 178.5) {
                                    /* node 797: if (mcs <= 17.5) -> 798 else 801 */
                                    if (mcs <= 17.5) {
                                        /* node 798: if (nb_rb <= 167.5) -> 799 else 800 */
                                        if (nb_rb <= 167.5) {
                                            return 799;
                                        } else {
                                            return 800;
                                        }
                                    } else {
                                        /* node 801: if (nb_rb <= 169.5) -> 802 else 803 */
                                        if (nb_rb <= 169.5) {
                                            return 802;
                                        } else {
                                            return 803;
                                        }
                                    }
                                } else {
                                    /* node 804: if (nb_rb <= 183.5) -> 805 else 806 */
                                    if (nb_rb <= 183.5) {
                                        return 805;
                                    } else {
                                        /* node 806: if (nb_rb <= 197.5) -> 807 else 808 */
                                        if (nb_rb <= 197.5) {
                                            return 807;
                                        } else {
                                            return 808;
                                        }
                                    }
                                }
                            } else {
                                /* node 809: if (mcs <= 17.5) -> 810 else 811 */
                                if (mcs <= 17.5) {
                                    return 810;
                                } else {
                                    /* node 811: if (nb_rb <= 214.5) -> 812 else 813 */
                                    if (nb_rb <= 214.5) {
                                        return 812;
                                    } else {
                                        return 813;
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 814: if (mcs <= 14.5) -> 815 else 834 */
                        if (mcs <= 14.5) {
                            /* node 815: if (nb_rb <= 257.5) -> 816 else 827 */
                            if (nb_rb <= 257.5) {
                                /* node 816: if (nb_rb <= 242.5) -> 817 else 822 */
                                if (nb_rb <= 242.5) {
                                    /* node 817: if (nb_rb <= 236.5) -> 818 else 821 */
                                    if (nb_rb <= 236.5) {
                                        /* node 818: if (nb_rb <= 227.5) -> 819 else 820 */
                                        if (nb_rb <= 227.5) {
                                            return 819;
                                        } else {
                                            return 820;
                                        }
                                    } else {
                                        return 821;
                                    }
                                } else {
                                    /* node 822: if (nb_rb <= 253.5) -> 823 else 826 */
                                    if (nb_rb <= 253.5) {
                                        /* node 823: if (nb_rb <= 250.5) -> 824 else 825 */
                                        if (nb_rb <= 250.5) {
                                            return 824;
                                        } else {
                                            return 825;
                                        }
                                    } else {
                                        return 826;
                                    }
                                }
                            } else {
                                /* node 827: if (nb_rb <= 270.5) -> 828 else 833 */
                                if (nb_rb <= 270.5) {
                                    /* node 828: if (nb_rb <= 265.5) -> 829 else 832 */
                                    if (nb_rb <= 265.5) {
                                        /* node 829: if (nb_rb <= 260.5) -> 830 else 831 */
                                        if (nb_rb <= 260.5) {
                                            return 830;
                                        } else {
                                            return 831;
                                        }
                                    } else {
                                        return 832;
                                    }
                                } else {
                                    return 833;
                                }
                            }
                        } else {
                            /* node 834: if (mcs <= 16.5) -> 835 else 846 */
                            if (mcs <= 16.5) {
                                /* node 835: if (nb_rb <= 230.5) -> 836 else 839 */
                                if (nb_rb <= 230.5) {
                                    /* node 836: if (mcs <= 15.5) -> 837 else 838 */
                                    if (mcs <= 15.5) {
                                        return 837;
                                    } else {
                                        return 838;
                                    }
                                } else {
                                    /* node 839: if (nb_rb <= 247.5) -> 840 else 843 */
                                    if (nb_rb <= 247.5) {
                                        /* node 840: if (nb_rb <= 242.5) -> 841 else 842 */
                                        if (nb_rb <= 242.5) {
                                            return 841;
                                        } else {
                                            return 842;
                                        }
                                    } else {
                                        /* node 843: if (nb_rb <= 261.5) -> 844 else 845 */
                                        if (nb_rb <= 261.5) {
                                            return 844;
                                        } else {
                                            return 845;
                                        }
                                    }
                                }
                            } else {
                                /* node 846: if (nb_rb <= 259.5) -> 847 else 854 */
                                if (nb_rb <= 259.5) {
                                    /* node 847: if (mcs <= 17.5) -> 848 else 851 */
                                    if (mcs <= 17.5) {
                                        /* node 848: if (nb_rb <= 240.5) -> 849 else 850 */
                                        if (nb_rb <= 240.5) {
                                            return 849;
                                        } else {
                                            return 850;
                                        }
                                    } else {
                                        /* node 851: if (nb_rb <= 248.0) -> 852 else 853 */
                                        if (nb_rb <= 248) {
                                            return 852;
                                        } else {
                                            return 853;
                                        }
                                    }
                                } else {
                                    /* node 854: if (mcs <= 17.5) -> 855 else 856 */
                                    if (mcs <= 17.5) {
                                        return 855;
                                    } else {
                                        return 856;
                                    }
                                }
                            }
                        }
                    }
                } else {
                    /* node 857: if (round <= 0.5) -> 858 else 893 */
                    if (round <= 0.5) {
                        /* node 858: if (nb_rb <= 222.5) -> 859 else 878 */
                        if (nb_rb <= 222.5) {
                            /* node 859: if (nb_rb <= 182.5) -> 860 else 867 */
                            if (nb_rb <= 182.5) {
                                /* node 860: if (mcs <= 22.5) -> 861 else 864 */
                                if (mcs <= 22.5) {
                                    /* node 861: if (mcs <= 20.5) -> 862 else 863 */
                                    if (mcs <= 20.5) {
                                        return 862;
                                    } else {
                                        return 863;
                                    }
                                } else {
                                    /* node 864: if (mcs <= 25.0) -> 865 else 866 */
                                    if (mcs <= 25) {
                                        return 865;
                                    } else {
                                        return 866;
                                    }
                                }
                            } else {
                                /* node 867: if (mcs <= 22.5) -> 868 else 875 */
                                if (mcs <= 22.5) {
                                    /* node 868: if (mcs <= 20.5) -> 869 else 872 */
                                    if (mcs <= 20.5) {
                                        /* node 869: if (nb_rb <= 208.5) -> 870 else 871 */
                                        if (nb_rb <= 208.5) {
                                            return 870;
                                        } else {
                                            return 871;
                                        }
                                    } else {
                                        /* node 872: if (mcs <= 21.5) -> 873 else 874 */
                                        if (mcs <= 21.5) {
                                            return 873;
                                        } else {
                                            return 874;
                                        }
                                    }
                                } else {
                                    /* node 875: if (mcs <= 25.5) -> 876 else 877 */
                                    if (mcs <= 25.5) {
                                        return 876;
                                    } else {
                                        return 877;
                                    }
                                }
                            }
                        } else {
                            /* node 878: if (nb_rb <= 241.5) -> 879 else 884 */
                            if (nb_rb <= 241.5) {
                                /* node 879: if (mcs <= 22.5) -> 880 else 883 */
                                if (mcs <= 22.5) {
                                    /* node 880: if (mcs <= 20.5) -> 881 else 882 */
                                    if (mcs <= 20.5) {
                                        return 881;
                                    } else {
                                        return 882;
                                    }
                                } else {
                                    return 883;
                                }
                            } else {
                                /* node 884: if (mcs <= 19.5) -> 885 else 886 */
                                if (mcs <= 19.5) {
                                    return 885;
                                } else {
                                    /* node 886: if (mcs <= 22.5) -> 887 else 890 */
                                    if (mcs <= 22.5) {
                                        /* node 887: if (nb_rb <= 253.5) -> 888 else 889 */
                                        if (nb_rb <= 253.5) {
                                            return 888;
                                        } else {
                                            return 889;
                                        }
                                    } else {
                                        /* node 890: if (nb_rb <= 260.5) -> 891 else 892 */
                                        if (nb_rb <= 260.5) {
                                            return 891;
                                        } else {
                                            return 892;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 893: if (mcs <= 23.5) -> 894 else 895 */
                        if (mcs <= 23.5) {
                            return 894;
                        } else {
                            return 895;
                        }
                    }
                }
            }
        } else {
            /* node 896: if (mcs <= 14.5) -> 897 else 1144 */
            if (mcs <= 14.5) {
                /* node 897: if (mcs <= 9.5) -> 898 else 1017 */
                if (mcs <= 9.5) {
                    /* node 898: if (nb_rb <= 215.5) -> 899 else 958 */
                    if (nb_rb <= 215.5) {
                        /* node 899: if (nb_rb <= 178.5) -> 900 else 929 */
                        if (nb_rb <= 178.5) {
                            /* node 900: if (mcs <= 7.5) -> 901 else 914 */
                            if (mcs <= 7.5) {
                                /* node 901: if (mcs <= 6.5) -> 902 else 907 */
                                if (mcs <= 6.5) {
                                    /* node 902: if (nb_rb <= 175.5) -> 903 else 906 */
                                    if (nb_rb <= 175.5) {
                                        /* node 903: if (nb_rb <= 154.5) -> 904 else 905 */
                                        if (nb_rb <= 154.5) {
                                            return 904;
                                        } else {
                                            return 905;
                                        }
                                    } else {
                                        return 906;
                                    }
                                } else {
                                    /* node 907: if (nb_rb <= 164.5) -> 908 else 911 */
                                    if (nb_rb <= 164.5) {
                                        /* node 908: if (nb_rb <= 158.5) -> 909 else 910 */
                                        if (nb_rb <= 158.5) {
                                            return 909;
                                        } else {
                                            return 910;
                                        }
                                    } else {
                                        /* node 911: if (nb_rb <= 170.5) -> 912 else 913 */
                                        if (nb_rb <= 170.5) {
                                            return 912;
                                        } else {
                                            return 913;
                                        }
                                    }
                                }
                            } else {
                                /* node 914: if (nb_rb <= 158.5) -> 915 else 922 */
                                if (nb_rb <= 158.5) {
                                    /* node 915: if (mcs <= 8.5) -> 916 else 919 */
                                    if (mcs <= 8.5) {
                                        /* node 916: if (nb_rb <= 155.5) -> 917 else 918 */
                                        if (nb_rb <= 155.5) {
                                            return 917;
                                        } else {
                                            return 918;
                                        }
                                    } else {
                                        /* node 919: if (nb_rb <= 155.5) -> 920 else 921 */
                                        if (nb_rb <= 155.5) {
                                            return 920;
                                        } else {
                                            return 921;
                                        }
                                    }
                                } else {
                                    /* node 922: if (nb_rb <= 172.5) -> 923 else 926 */
                                    if (nb_rb <= 172.5) {
                                        /* node 923: if (nb_rb <= 169.5) -> 924 else 925 */
                                        if (nb_rb <= 169.5) {
                                            return 924;
                                        } else {
                                            return 925;
                                        }
                                    } else {
                                        /* node 926: if (mcs <= 8.5) -> 927 else 928 */
                                        if (mcs <= 8.5) {
                                            return 927;
                                        } else {
                                            return 928;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 929: if (mcs <= 6.5) -> 930 else 943 */
                            if (mcs <= 6.5) {
                                /* node 930: if (nb_rb <= 209.5) -> 931 else 938 */
                                if (nb_rb <= 209.5) {
                                    /* node 931: if (nb_rb <= 192.5) -> 932 else 935 */
                                    if (nb_rb <= 192.5) {
                                        /* node 932: if (nb_rb <= 182.5) -> 933 else 934 */
                                        if (nb_rb <= 182.5) {
                                            return 933;
                                        } else {
                                            return 934;
                                        }
                                    } else {
                                        /* node 935: if (nb_rb <= 200.5) -> 936 else 937 */
                                        if (nb_rb <= 200.5) {
                                            return 936;
                                        } else {
                                            return 937;
                                        }
                                    }
                                } else {
                                    /* node 938: if (nb_rb <= 211.5) -> 939 else 940 */
                                    if (nb_rb <= 211.5) {
                                        return 939;
                                    } else {
                                        /* node 940: if (nb_rb <= 213.5) -> 941 else 942 */
                                        if (nb_rb <= 213.5) {
                                            return 941;
                                        } else {
                                            return 942;
                                        }
                                    }
                                }
                            } else {
                                /* node 943: if (mcs <= 7.5) -> 944 else 951 */
                                if (mcs <= 7.5) {
                                    /* node 944: if (nb_rb <= 196.5) -> 945 else 948 */
                                    if (nb_rb <= 196.5) {
                                        /* node 945: if (nb_rb <= 186.5) -> 946 else 947 */
                                        if (nb_rb <= 186.5) {
                                            return 946;
                                        } else {
                                            return 947;
                                        }
                                    } else {
                                        /* node 948: if (nb_rb <= 213.5) -> 949 else 950 */
                                        if (nb_rb <= 213.5) {
                                            return 949;
                                        } else {
                                            return 950;
                                        }
                                    }
                                } else {
                                    /* node 951: if (nb_rb <= 197.5) -> 952 else 955 */
                                    if (nb_rb <= 197.5) {
                                        /* node 952: if (mcs <= 8.5) -> 953 else 954 */
                                        if (mcs <= 8.5) {
                                            return 953;
                                        } else {
                                            return 954;
                                        }
                                    } else {
                                        /* node 955: if (nb_rb <= 209.5) -> 956 else 957 */
                                        if (nb_rb <= 209.5) {
                                            return 956;
                                        } else {
                                            return 957;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 958: if (mcs <= 7.5) -> 959 else 990 */
                        if (mcs <= 7.5) {
                            /* node 959: if (mcs <= 6.5) -> 960 else 975 */
                            if (mcs <= 6.5) {
                                /* node 960: if (nb_rb <= 230.5) -> 961 else 968 */
                                if (nb_rb <= 230.5) {
                                    /* node 961: if (nb_rb <= 220.5) -> 962 else 965 */
                                    if (nb_rb <= 220.5) {
                                        /* node 962: if (nb_rb <= 218.5) -> 963 else 964 */
                                        if (nb_rb <= 218.5) {
                                            return 963;
                                        } else {
                                            return 964;
                                        }
                                    } else {
                                        /* node 965: if (nb_rb <= 225.5) -> 966 else 967 */
                                        if (nb_rb <= 225.5) {
                                            return 966;
                                        } else {
                                            return 967;
                                        }
                                    }
                                } else {
                                    /* node 968: if (nb_rb <= 256.5) -> 969 else 972 */
                                    if (nb_rb <= 256.5) {
                                        /* node 969: if (nb_rb <= 237.5) -> 970 else 971 */
                                        if (nb_rb <= 237.5) {
                                            return 970;
                                        } else {
                                            return 971;
                                        }
                                    } else {
                                        /* node 972: if (nb_rb <= 266.5) -> 973 else 974 */
                                        if (nb_rb <= 266.5) {
                                            return 973;
                                        } else {
                                            return 974;
                                        }
                                    }
                                }
                            } else {
                                /* node 975: if (nb_rb <= 234.5) -> 976 else 983 */
                                if (nb_rb <= 234.5) {
                                    /* node 976: if (nb_rb <= 218.5) -> 977 else 980 */
                                    if (nb_rb <= 218.5) {
                                        /* node 977: if (nb_rb <= 217.5) -> 978 else 979 */
                                        if (nb_rb <= 217.5) {
                                            return 978;
                                        } else {
                                            return 979;
                                        }
                                    } else {
                                        /* node 980: if (nb_rb <= 220.5) -> 981 else 982 */
                                        if (nb_rb <= 220.5) {
                                            return 981;
                                        } else {
                                            return 982;
                                        }
                                    }
                                } else {
                                    /* node 983: if (nb_rb <= 249.5) -> 984 else 987 */
                                    if (nb_rb <= 249.5) {
                                        /* node 984: if (nb_rb <= 247.5) -> 985 else 986 */
                                        if (nb_rb <= 247.5) {
                                            return 985;
                                        } else {
                                            return 986;
                                        }
                                    } else {
                                        /* node 987: if (nb_rb <= 266.5) -> 988 else 989 */
                                        if (nb_rb <= 266.5) {
                                            return 988;
                                        } else {
                                            return 989;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 990: if (nb_rb <= 261.5) -> 991 else 1006 */
                            if (nb_rb <= 261.5) {
                                /* node 991: if (nb_rb <= 237.5) -> 992 else 999 */
                                if (nb_rb <= 237.5) {
                                    /* node 992: if (nb_rb <= 232.5) -> 993 else 996 */
                                    if (nb_rb <= 232.5) {
                                        /* node 993: if (mcs <= 8.5) -> 994 else 995 */
                                        if (mcs <= 8.5) {
                                            return 994;
                                        } else {
                                            return 995;
                                        }
                                    } else {
                                        /* node 996: if (mcs <= 8.5) -> 997 else 998 */
                                        if (mcs <= 8.5) {
                                            return 997;
                                        } else {
                                            return 998;
                                        }
                                    }
                                } else {
                                    /* node 999: if (mcs <= 8.5) -> 1000 else 1003 */
                                    if (mcs <= 8.5) {
                                        /* node 1000: if (nb_rb <= 245.5) -> 1001 else 1002 */
                                        if (nb_rb <= 245.5) {
                                            return 1001;
                                        } else {
                                            return 1002;
                                        }
                                    } else {
                                        /* node 1003: if (nb_rb <= 254.5) -> 1004 else 1005 */
                                        if (nb_rb <= 254.5) {
                                            return 1004;
                                        } else {
                                            return 1005;
                                        }
                                    }
                                }
                            } else {
                                /* node 1006: if (mcs <= 8.5) -> 1007 else 1012 */
                                if (mcs <= 8.5) {
                                    /* node 1007: if (nb_rb <= 264.5) -> 1008 else 1009 */
                                    if (nb_rb <= 264.5) {
                                        return 1008;
                                    } else {
                                        /* node 1009: if (nb_rb <= 271.5) -> 1010 else 1011 */
                                        if (nb_rb <= 271.5) {
                                            return 1010;
                                        } else {
                                            return 1011;
                                        }
                                    }
                                } else {
                                    /* node 1012: if (nb_rb <= 267.5) -> 1013 else 1016 */
                                    if (nb_rb <= 267.5) {
                                        /* node 1013: if (nb_rb <= 264.5) -> 1014 else 1015 */
                                        if (nb_rb <= 264.5) {
                                            return 1014;
                                        } else {
                                            return 1015;
                                        }
                                    } else {
                                        return 1016;
                                    }
                                }
                            }
                        }
                    }
                } else {
                    /* node 1017: if (nb_rb <= 216.5) -> 1018 else 1081 */
                    if (nb_rb <= 216.5) {
                        /* node 1018: if (nb_rb <= 181.5) -> 1019 else 1050 */
                        if (nb_rb <= 181.5) {
                            /* node 1019: if (mcs <= 12.5) -> 1020 else 1035 */
                            if (mcs <= 12.5) {
                                /* node 1020: if (mcs <= 10.5) -> 1021 else 1028 */
                                if (mcs <= 10.5) {
                                    /* node 1021: if (round <= 0.5) -> 1022 else 1025 */
                                    if (round <= 0.5) {
                                        /* node 1022: if (nb_rb <= 170.5) -> 1023 else 1024 */
                                        if (nb_rb <= 170.5) {
                                            return 1023;
                                        } else {
                                            return 1024;
                                        }
                                    } else {
                                        /* node 1025: if (nb_rb <= 169.5) -> 1026 else 1027 */
                                        if (nb_rb <= 169.5) {
                                            return 1026;
                                        } else {
                                            return 1027;
                                        }
                                    }
                                } else {
                                    /* node 1028: if (nb_rb <= 163.5) -> 1029 else 1032 */
                                    if (nb_rb <= 163.5) {
                                        /* node 1029: if (mcs <= 11.5) -> 1030 else 1031 */
                                        if (mcs <= 11.5) {
                                            return 1030;
                                        } else {
                                            return 1031;
                                        }
                                    } else {
                                        /* node 1032: if (mcs <= 11.5) -> 1033 else 1034 */
                                        if (mcs <= 11.5) {
                                            return 1033;
                                        } else {
                                            return 1034;
                                        }
                                    }
                                }
                            } else {
                                /* node 1035: if (nb_rb <= 170.5) -> 1036 else 1043 */
                                if (nb_rb <= 170.5) {
                                    /* node 1036: if (mcs <= 13.5) -> 1037 else 1040 */
                                    if (mcs <= 13.5) {
                                        /* node 1037: if (nb_rb <= 160.5) -> 1038 else 1039 */
                                        if (nb_rb <= 160.5) {
                                            return 1038;
                                        } else {
                                            return 1039;
                                        }
                                    } else {
                                        /* node 1040: if (round <= 0.5) -> 1041 else 1042 */
                                        if (round <= 0.5) {
                                            return 1041;
                                        } else {
                                            return 1042;
                                        }
                                    }
                                } else {
                                    /* node 1043: if (mcs <= 13.5) -> 1044 else 1047 */
                                    if (mcs <= 13.5) {
                                        /* node 1044: if (round <= 0.5) -> 1045 else 1046 */
                                        if (round <= 0.5) {
                                            return 1045;
                                        } else {
                                            return 1046;
                                        }
                                    } else {
                                        /* node 1047: if (round <= 0.5) -> 1048 else 1049 */
                                        if (round <= 0.5) {
                                            return 1048;
                                        } else {
                                            return 1049;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1050: if (mcs <= 11.5) -> 1051 else 1066 */
                            if (mcs <= 11.5) {
                                /* node 1051: if (nb_rb <= 208.5) -> 1052 else 1059 */
                                if (nb_rb <= 208.5) {
                                    /* node 1052: if (nb_rb <= 191.5) -> 1053 else 1056 */
                                    if (nb_rb <= 191.5) {
                                        /* node 1053: if (mcs <= 10.5) -> 1054 else 1055 */
                                        if (mcs <= 10.5) {
                                            return 1054;
                                        } else {
                                            return 1055;
                                        }
                                    } else {
                                        /* node 1056: if (mcs <= 10.5) -> 1057 else 1058 */
                                        if (mcs <= 10.5) {
                                            return 1057;
                                        } else {
                                            return 1058;
                                        }
                                    }
                                } else {
                                    /* node 1059: if (mcs <= 10.5) -> 1060 else 1063 */
                                    if (mcs <= 10.5) {
                                        /* node 1060: if (round <= 0.5) -> 1061 else 1062 */
                                        if (round <= 0.5) {
                                            return 1061;
                                        } else {
                                            return 1062;
                                        }
                                    } else {
                                        /* node 1063: if (nb_rb <= 209.5) -> 1064 else 1065 */
                                        if (nb_rb <= 209.5) {
                                            return 1064;
                                        } else {
                                            return 1065;
                                        }
                                    }
                                }
                            } else {
                                /* node 1066: if (mcs <= 13.5) -> 1067 else 1074 */
                                if (mcs <= 13.5) {
                                    /* node 1067: if (nb_rb <= 199.5) -> 1068 else 1071 */
                                    if (nb_rb <= 199.5) {
                                        /* node 1068: if (nb_rb <= 191.5) -> 1069 else 1070 */
                                        if (nb_rb <= 191.5) {
                                            return 1069;
                                        } else {
                                            return 1070;
                                        }
                                    } else {
                                        /* node 1071: if (mcs <= 12.5) -> 1072 else 1073 */
                                        if (mcs <= 12.5) {
                                            return 1072;
                                        } else {
                                            return 1073;
                                        }
                                    }
                                } else {
                                    /* node 1074: if (nb_rb <= 197.5) -> 1075 else 1078 */
                                    if (nb_rb <= 197.5) {
                                        /* node 1075: if (round <= 0.5) -> 1076 else 1077 */
                                        if (round <= 0.5) {
                                            return 1076;
                                        } else {
                                            return 1077;
                                        }
                                    } else {
                                        /* node 1078: if (round <= 0.5) -> 1079 else 1080 */
                                        if (round <= 0.5) {
                                            return 1079;
                                        } else {
                                            return 1080;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 1081: if (mcs <= 12.5) -> 1082 else 1113 */
                        if (mcs <= 12.5) {
                            /* node 1082: if (mcs <= 11.5) -> 1083 else 1098 */
                            if (mcs <= 11.5) {
                                /* node 1083: if (nb_rb <= 248.5) -> 1084 else 1091 */
                                if (nb_rb <= 248.5) {
                                    /* node 1084: if (nb_rb <= 231.5) -> 1085 else 1088 */
                                    if (nb_rb <= 231.5) {
                                        /* node 1085: if (mcs <= 10.5) -> 1086 else 1087 */
                                        if (mcs <= 10.5) {
                                            return 1086;
                                        } else {
                                            return 1087;
                                        }
                                    } else {
                                        /* node 1088: if (round <= 0.5) -> 1089 else 1090 */
                                        if (round <= 0.5) {
                                            return 1089;
                                        } else {
                                            return 1090;
                                        }
                                    }
                                } else {
                                    /* node 1091: if (mcs <= 10.5) -> 1092 else 1095 */
                                    if (mcs <= 10.5) {
                                        /* node 1092: if (round <= 0.5) -> 1093 else 1094 */
                                        if (round <= 0.5) {
                                            return 1093;
                                        } else {
                                            return 1094;
                                        }
                                    } else {
                                        /* node 1095: if (nb_rb <= 263.5) -> 1096 else 1097 */
                                        if (nb_rb <= 263.5) {
                                            return 1096;
                                        } else {
                                            return 1097;
                                        }
                                    }
                                }
                            } else {
                                /* node 1098: if (nb_rb <= 251.5) -> 1099 else 1106 */
                                if (nb_rb <= 251.5) {
                                    /* node 1099: if (nb_rb <= 229.5) -> 1100 else 1103 */
                                    if (nb_rb <= 229.5) {
                                        /* node 1100: if (round <= 0.5) -> 1101 else 1102 */
                                        if (round <= 0.5) {
                                            return 1101;
                                        } else {
                                            return 1102;
                                        }
                                    } else {
                                        /* node 1103: if (round <= 0.5) -> 1104 else 1105 */
                                        if (round <= 0.5) {
                                            return 1104;
                                        } else {
                                            return 1105;
                                        }
                                    }
                                } else {
                                    /* node 1106: if (nb_rb <= 265.5) -> 1107 else 1110 */
                                    if (nb_rb <= 265.5) {
                                        /* node 1107: if (nb_symbol <= 12.5) -> 1108 else 1109 */
                                        if (nb_symbol <= 12.5) {
                                            return 1108;
                                        } else {
                                            return 1109;
                                        }
                                    } else {
                                        /* node 1110: if (round <= 0.5) -> 1111 else 1112 */
                                        if (round <= 0.5) {
                                            return 1111;
                                        } else {
                                            return 1112;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1113: if (nb_rb <= 252.5) -> 1114 else 1129 */
                            if (nb_rb <= 252.5) {
                                /* node 1114: if (mcs <= 13.5) -> 1115 else 1122 */
                                if (mcs <= 13.5) {
                                    /* node 1115: if (nb_rb <= 223.5) -> 1116 else 1119 */
                                    if (nb_rb <= 223.5) {
                                        /* node 1116: if (round <= 0.5) -> 1117 else 1118 */
                                        if (round <= 0.5) {
                                            return 1117;
                                        } else {
                                            return 1118;
                                        }
                                    } else {
                                        /* node 1119: if (round <= 0.5) -> 1120 else 1121 */
                                        if (round <= 0.5) {
                                            return 1120;
                                        } else {
                                            return 1121;
                                        }
                                    }
                                } else {
                                    /* node 1122: if (nb_rb <= 223.5) -> 1123 else 1126 */
                                    if (nb_rb <= 223.5) {
                                        /* node 1123: if (round <= 0.5) -> 1124 else 1125 */
                                        if (round <= 0.5) {
                                            return 1124;
                                        } else {
                                            return 1125;
                                        }
                                    } else {
                                        /* node 1126: if (nb_rb <= 229.5) -> 1127 else 1128 */
                                        if (nb_rb <= 229.5) {
                                            return 1127;
                                        } else {
                                            return 1128;
                                        }
                                    }
                                }
                            } else {
                                /* node 1129: if (mcs <= 13.5) -> 1130 else 1137 */
                                if (mcs <= 13.5) {
                                    /* node 1130: if (round <= 0.5) -> 1131 else 1134 */
                                    if (round <= 0.5) {
                                        /* node 1131: if (nb_rb <= 260.5) -> 1132 else 1133 */
                                        if (nb_rb <= 260.5) {
                                            return 1132;
                                        } else {
                                            return 1133;
                                        }
                                    } else {
                                        /* node 1134: if (nb_rb <= 259.5) -> 1135 else 1136 */
                                        if (nb_rb <= 259.5) {
                                            return 1135;
                                        } else {
                                            return 1136;
                                        }
                                    }
                                } else {
                                    /* node 1137: if (nb_rb <= 257.5) -> 1138 else 1141 */
                                    if (nb_rb <= 257.5) {
                                        /* node 1138: if (round <= 0.5) -> 1139 else 1140 */
                                        if (round <= 0.5) {
                                            return 1139;
                                        } else {
                                            return 1140;
                                        }
                                    } else {
                                        /* node 1141: if (round <= 0.5) -> 1142 else 1143 */
                                        if (round <= 0.5) {
                                            return 1142;
                                        } else {
                                            return 1143;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                /* node 1144: if (nb_rb <= 216.5) -> 1145 else 1266 */
                if (nb_rb <= 216.5) {
                    /* node 1145: if (mcs <= 16.5) -> 1146 else 1205 */
                    if (mcs <= 16.5) {
                        /* node 1146: if (nb_rb <= 177.5) -> 1147 else 1174 */
                        if (nb_rb <= 177.5) {
                            /* node 1147: if (nb_rb <= 166.5) -> 1148 else 1161 */
                            if (nb_rb <= 166.5) {
                                /* node 1148: if (round <= 0.5) -> 1149 else 1156 */
                                if (round <= 0.5) {
                                    /* node 1149: if (mcs <= 15.5) -> 1150 else 1153 */
                                    if (mcs <= 15.5) {
                                        /* node 1150: if (nb_rb <= 161.5) -> 1151 else 1152 */
                                        if (nb_rb <= 161.5) {
                                            return 1151;
                                        } else {
                                            return 1152;
                                        }
                                    } else {
                                        /* node 1153: if (nb_rb <= 158.5) -> 1154 else 1155 */
                                        if (nb_rb <= 158.5) {
                                            return 1154;
                                        } else {
                                            return 1155;
                                        }
                                    }
                                } else {
                                    /* node 1156: if (nb_rb <= 161.5) -> 1157 else 1160 */
                                    if (nb_rb <= 161.5) {
                                        /* node 1157: if (nb_rb <= 157.5) -> 1158 else 1159 */
                                        if (nb_rb <= 157.5) {
                                            return 1158;
                                        } else {
                                            return 1159;
                                        }
                                    } else {
                                        return 1160;
                                    }
                                }
                            } else {
                                /* node 1161: if (mcs <= 15.5) -> 1162 else 1167 */
                                if (mcs <= 15.5) {
                                    /* node 1162: if (round <= 0.5) -> 1163 else 1166 */
                                    if (round <= 0.5) {
                                        /* node 1163: if (nb_rb <= 167.5) -> 1164 else 1165 */
                                        if (nb_rb <= 167.5) {
                                            return 1164;
                                        } else {
                                            return 1165;
                                        }
                                    } else {
                                        return 1166;
                                    }
                                } else {
                                    /* node 1167: if (nb_rb <= 174.5) -> 1168 else 1171 */
                                    if (nb_rb <= 174.5) {
                                        /* node 1168: if (nb_rb <= 169.5) -> 1169 else 1170 */
                                        if (nb_rb <= 169.5) {
                                            return 1169;
                                        } else {
                                            return 1170;
                                        }
                                    } else {
                                        /* node 1171: if (nb_rb <= 176.5) -> 1172 else 1173 */
                                        if (nb_rb <= 176.5) {
                                            return 1172;
                                        } else {
                                            return 1173;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1174: if (nb_rb <= 200.5) -> 1175 else 1190 */
                            if (nb_rb <= 200.5) {
                                /* node 1175: if (nb_rb <= 187.5) -> 1176 else 1183 */
                                if (nb_rb <= 187.5) {
                                    /* node 1176: if (nb_rb <= 186.5) -> 1177 else 1180 */
                                    if (nb_rb <= 186.5) {
                                        /* node 1177: if (round <= 0.5) -> 1178 else 1179 */
                                        if (round <= 0.5) {
                                            return 1178;
                                        } else {
                                            return 1179;
                                        }
                                    } else {
                                        /* node 1180: if (mcs <= 15.5) -> 1181 else 1182 */
                                        if (mcs <= 15.5) {
                                            return 1181;
                                        } else {
                                            return 1182;
                                        }
                                    }
                                } else {
                                    /* node 1183: if (nb_rb <= 194.5) -> 1184 else 1187 */
                                    if (nb_rb <= 194.5) {
                                        /* node 1184: if (nb_rb <= 193.5) -> 1185 else 1186 */
                                        if (nb_rb <= 193.5) {
                                            return 1185;
                                        } else {
                                            return 1186;
                                        }
                                    } else {
                                        /* node 1187: if (mcs <= 15.5) -> 1188 else 1189 */
                                        if (mcs <= 15.5) {
                                            return 1188;
                                        } else {
                                            return 1189;
                                        }
                                    }
                                }
                            } else {
                                /* node 1190: if (mcs <= 15.5) -> 1191 else 1198 */
                                if (mcs <= 15.5) {
                                    /* node 1191: if (nb_rb <= 206.5) -> 1192 else 1195 */
                                    if (nb_rb <= 206.5) {
                                        /* node 1192: if (nb_rb <= 201.5) -> 1193 else 1194 */
                                        if (nb_rb <= 201.5) {
                                            return 1193;
                                        } else {
                                            return 1194;
                                        }
                                    } else {
                                        /* node 1195: if (round <= 0.5) -> 1196 else 1197 */
                                        if (round <= 0.5) {
                                            return 1196;
                                        } else {
                                            return 1197;
                                        }
                                    }
                                } else {
                                    /* node 1198: if (nb_rb <= 212.5) -> 1199 else 1202 */
                                    if (nb_rb <= 212.5) {
                                        /* node 1199: if (nb_rb <= 201.5) -> 1200 else 1201 */
                                        if (nb_rb <= 201.5) {
                                            return 1200;
                                        } else {
                                            return 1201;
                                        }
                                    } else {
                                        /* node 1202: if (nb_rb <= 213.5) -> 1203 else 1204 */
                                        if (nb_rb <= 213.5) {
                                            return 1203;
                                        } else {
                                            return 1204;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 1205: if (nb_rb <= 183.5) -> 1206 else 1235 */
                        if (nb_rb <= 183.5) {
                            /* node 1206: if (mcs <= 20.5) -> 1207 else 1222 */
                            if (mcs <= 20.5) {
                                /* node 1207: if (nb_rb <= 166.5) -> 1208 else 1215 */
                                if (nb_rb <= 166.5) {
                                    /* node 1208: if (round <= 1.5) -> 1209 else 1212 */
                                    if (round <= 1.5) {
                                        /* node 1209: if (mcs <= 18.5) -> 1210 else 1211 */
                                        if (mcs <= 18.5) {
                                            return 1210;
                                        } else {
                                            return 1211;
                                        }
                                    } else {
                                        /* node 1212: if (nb_rb <= 159.5) -> 1213 else 1214 */
                                        if (nb_rb <= 159.5) {
                                            return 1213;
                                        } else {
                                            return 1214;
                                        }
                                    }
                                } else {
                                    /* node 1215: if (round <= 0.5) -> 1216 else 1219 */
                                    if (round <= 0.5) {
                                        /* node 1216: if (nb_rb <= 176.5) -> 1217 else 1218 */
                                        if (nb_rb <= 176.5) {
                                            return 1217;
                                        } else {
                                            return 1218;
                                        }
                                    } else {
                                        /* node 1219: if (round <= 1.5) -> 1220 else 1221 */
                                        if (round <= 1.5) {
                                            return 1220;
                                        } else {
                                            return 1221;
                                        }
                                    }
                                }
                            } else {
                                /* node 1222: if (round <= 0.5) -> 1223 else 1230 */
                                if (round <= 0.5) {
                                    /* node 1223: if (mcs <= 22.5) -> 1224 else 1227 */
                                    if (mcs <= 22.5) {
                                        /* node 1224: if (nb_rb <= 170.5) -> 1225 else 1226 */
                                        if (nb_rb <= 170.5) {
                                            return 1225;
                                        } else {
                                            return 1226;
                                        }
                                    } else {
                                        /* node 1227: if (mcs <= 25.5) -> 1228 else 1229 */
                                        if (mcs <= 25.5) {
                                            return 1228;
                                        } else {
                                            return 1229;
                                        }
                                    }
                                } else {
                                    /* node 1230: if (mcs <= 23.5) -> 1231 else 1232 */
                                    if (mcs <= 23.5) {
                                        return 1231;
                                    } else {
                                        /* node 1232: if (mcs <= 25.5) -> 1233 else 1234 */
                                        if (mcs <= 25.5) {
                                            return 1233;
                                        } else {
                                            return 1234;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1235: if (mcs <= 20.5) -> 1236 else 1251 */
                            if (mcs <= 20.5) {
                                /* node 1236: if (nb_rb <= 203.5) -> 1237 else 1244 */
                                if (nb_rb <= 203.5) {
                                    /* node 1237: if (round <= 1.5) -> 1238 else 1241 */
                                    if (round <= 1.5) {
                                        /* node 1238: if (mcs <= 18.5) -> 1239 else 1240 */
                                        if (mcs <= 18.5) {
                                            return 1239;
                                        } else {
                                            return 1240;
                                        }
                                    } else {
                                        /* node 1241: if (nb_rb <= 188.5) -> 1242 else 1243 */
                                        if (nb_rb <= 188.5) {
                                            return 1242;
                                        } else {
                                            return 1243;
                                        }
                                    }
                                } else {
                                    /* node 1244: if (mcs <= 18.5) -> 1245 else 1248 */
                                    if (mcs <= 18.5) {
                                        /* node 1245: if (round <= 1.5) -> 1246 else 1247 */
                                        if (round <= 1.5) {
                                            return 1246;
                                        } else {
                                            return 1247;
                                        }
                                    } else {
                                        /* node 1248: if (nb_rb <= 212.5) -> 1249 else 1250 */
                                        if (nb_rb <= 212.5) {
                                            return 1249;
                                        } else {
                                            return 1250;
                                        }
                                    }
                                }
                            } else {
                                /* node 1251: if (round <= 0.5) -> 1252 else 1259 */
                                if (round <= 0.5) {
                                    /* node 1252: if (mcs <= 22.5) -> 1253 else 1256 */
                                    if (mcs <= 22.5) {
                                        /* node 1253: if (mcs <= 21.5) -> 1254 else 1255 */
                                        if (mcs <= 21.5) {
                                            return 1254;
                                        } else {
                                            return 1255;
                                        }
                                    } else {
                                        /* node 1256: if (mcs <= 26.5) -> 1257 else 1258 */
                                        if (mcs <= 26.5) {
                                            return 1257;
                                        } else {
                                            return 1258;
                                        }
                                    }
                                } else {
                                    /* node 1259: if (mcs <= 23.5) -> 1260 else 1263 */
                                    if (mcs <= 23.5) {
                                        /* node 1260: if (nb_rb <= 198.5) -> 1261 else 1262 */
                                        if (nb_rb <= 198.5) {
                                            return 1261;
                                        } else {
                                            return 1262;
                                        }
                                    } else {
                                        /* node 1263: if (mcs <= 24.5) -> 1264 else 1265 */
                                        if (mcs <= 24.5) {
                                            return 1264;
                                        } else {
                                            return 1265;
                                        }
                                    }
                                }
                            }
                        }
                    }
                } else {
                    /* node 1266: if (mcs <= 16.5) -> 1267 else 1330 */
                    if (mcs <= 16.5) {
                        /* node 1267: if (nb_rb <= 256.5) -> 1268 else 1299 */
                        if (nb_rb <= 256.5) {
                            /* node 1268: if (nb_rb <= 231.5) -> 1269 else 1284 */
                            if (nb_rb <= 231.5) {
                                /* node 1269: if (mcs <= 15.5) -> 1270 else 1277 */
                                if (mcs <= 15.5) {
                                    /* node 1270: if (round <= 0.5) -> 1271 else 1274 */
                                    if (round <= 0.5) {
                                        /* node 1271: if (nb_rb <= 219.5) -> 1272 else 1273 */
                                        if (nb_rb <= 219.5) {
                                            return 1272;
                                        } else {
                                            return 1273;
                                        }
                                    } else {
                                        /* node 1274: if (nb_rb <= 224.5) -> 1275 else 1276 */
                                        if (nb_rb <= 224.5) {
                                            return 1275;
                                        } else {
                                            return 1276;
                                        }
                                    }
                                } else {
                                    /* node 1277: if (nb_rb <= 222.5) -> 1278 else 1281 */
                                    if (nb_rb <= 222.5) {
                                        /* node 1278: if (nb_rb <= 218.5) -> 1279 else 1280 */
                                        if (nb_rb <= 218.5) {
                                            return 1279;
                                        } else {
                                            return 1280;
                                        }
                                    } else {
                                        /* node 1281: if (nb_rb <= 226.5) -> 1282 else 1283 */
                                        if (nb_rb <= 226.5) {
                                            return 1282;
                                        } else {
                                            return 1283;
                                        }
                                    }
                                }
                            } else {
                                /* node 1284: if (nb_rb <= 239.5) -> 1285 else 1292 */
                                if (nb_rb <= 239.5) {
                                    /* node 1285: if (mcs <= 15.5) -> 1286 else 1289 */
                                    if (mcs <= 15.5) {
                                        /* node 1286: if (round <= 0.5) -> 1287 else 1288 */
                                        if (round <= 0.5) {
                                            return 1287;
                                        } else {
                                            return 1288;
                                        }
                                    } else {
                                        /* node 1289: if (nb_rb <= 236.5) -> 1290 else 1291 */
                                        if (nb_rb <= 236.5) {
                                            return 1290;
                                        } else {
                                            return 1291;
                                        }
                                    }
                                } else {
                                    /* node 1292: if (mcs <= 15.5) -> 1293 else 1296 */
                                    if (mcs <= 15.5) {
                                        /* node 1293: if (round <= 0.5) -> 1294 else 1295 */
                                        if (round <= 0.5) {
                                            return 1294;
                                        } else {
                                            return 1295;
                                        }
                                    } else {
                                        /* node 1296: if (nb_rb <= 248.5) -> 1297 else 1298 */
                                        if (nb_rb <= 248.5) {
                                            return 1297;
                                        } else {
                                            return 1298;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1299: if (nb_rb <= 262.5) -> 1300 else 1315 */
                            if (nb_rb <= 262.5) {
                                /* node 1300: if (mcs <= 15.5) -> 1301 else 1308 */
                                if (mcs <= 15.5) {
                                    /* node 1301: if (nb_rb <= 259.5) -> 1302 else 1305 */
                                    if (nb_rb <= 259.5) {
                                        /* node 1302: if (nb_rb <= 257.5) -> 1303 else 1304 */
                                        if (nb_rb <= 257.5) {
                                            return 1303;
                                        } else {
                                            return 1304;
                                        }
                                    } else {
                                        /* node 1305: if (nb_rb <= 261.5) -> 1306 else 1307 */
                                        if (nb_rb <= 261.5) {
                                            return 1306;
                                        } else {
                                            return 1307;
                                        }
                                    }
                                } else {
                                    /* node 1308: if (nb_rb <= 259.5) -> 1309 else 1312 */
                                    if (nb_rb <= 259.5) {
                                        /* node 1309: if (nb_rb <= 258.5) -> 1310 else 1311 */
                                        if (nb_rb <= 258.5) {
                                            return 1310;
                                        } else {
                                            return 1311;
                                        }
                                    } else {
                                        /* node 1312: if (nb_rb <= 260.5) -> 1313 else 1314 */
                                        if (nb_rb <= 260.5) {
                                            return 1313;
                                        } else {
                                            return 1314;
                                        }
                                    }
                                }
                            } else {
                                /* node 1315: if (mcs <= 15.5) -> 1316 else 1323 */
                                if (mcs <= 15.5) {
                                    /* node 1316: if (round <= 0.5) -> 1317 else 1320 */
                                    if (round <= 0.5) {
                                        /* node 1317: if (nb_rb <= 272.5) -> 1318 else 1319 */
                                        if (nb_rb <= 272.5) {
                                            return 1318;
                                        } else {
                                            return 1319;
                                        }
                                    } else {
                                        /* node 1320: if (nb_rb <= 267.5) -> 1321 else 1322 */
                                        if (nb_rb <= 267.5) {
                                            return 1321;
                                        } else {
                                            return 1322;
                                        }
                                    }
                                } else {
                                    /* node 1323: if (nb_rb <= 270.5) -> 1324 else 1327 */
                                    if (nb_rb <= 270.5) {
                                        /* node 1324: if (nb_rb <= 266.5) -> 1325 else 1326 */
                                        if (nb_rb <= 266.5) {
                                            return 1325;
                                        } else {
                                            return 1326;
                                        }
                                    } else {
                                        /* node 1327: if (nb_rb <= 271.5) -> 1328 else 1329 */
                                        if (nb_rb <= 271.5) {
                                            return 1328;
                                        } else {
                                            return 1329;
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        /* node 1330: if (mcs <= 20.5) -> 1331 else 1362 */
                        if (mcs <= 20.5) {
                            /* node 1331: if (nb_rb <= 240.5) -> 1332 else 1347 */
                            if (nb_rb <= 240.5) {
                                /* node 1332: if (mcs <= 18.5) -> 1333 else 1340 */
                                if (mcs <= 18.5) {
                                    /* node 1333: if (round <= 1.5) -> 1334 else 1337 */
                                    if (round <= 1.5) {
                                        /* node 1334: if (nb_rb <= 225.5) -> 1335 else 1336 */
                                        if (nb_rb <= 225.5) {
                                            return 1335;
                                        } else {
                                            return 1336;
                                        }
                                    } else {
                                        /* node 1337: if (nb_rb <= 223.5) -> 1338 else 1339 */
                                        if (nb_rb <= 223.5) {
                                            return 1338;
                                        } else {
                                            return 1339;
                                        }
                                    }
                                } else {
                                    /* node 1340: if (nb_rb <= 222.5) -> 1341 else 1344 */
                                    if (nb_rb <= 222.5) {
                                        /* node 1341: if (nb_rb <= 219.5) -> 1342 else 1343 */
                                        if (nb_rb <= 219.5) {
                                            return 1342;
                                        } else {
                                            return 1343;
                                        }
                                    } else {
                                        /* node 1344: if (mcs <= 19.5) -> 1345 else 1346 */
                                        if (mcs <= 19.5) {
                                            return 1345;
                                        } else {
                                            return 1346;
                                        }
                                    }
                                }
                            } else {
                                /* node 1347: if (nb_rb <= 263.5) -> 1348 else 1355 */
                                if (nb_rb <= 263.5) {
                                    /* node 1348: if (mcs <= 18.5) -> 1349 else 1352 */
                                    if (mcs <= 18.5) {
                                        /* node 1349: if (round <= 1.5) -> 1350 else 1351 */
                                        if (round <= 1.5) {
                                            return 1350;
                                        } else {
                                            return 1351;
                                        }
                                    } else {
                                        /* node 1352: if (nb_rb <= 256.5) -> 1353 else 1354 */
                                        if (nb_rb <= 256.5) {
                                            return 1353;
                                        } else {
                                            return 1354;
                                        }
                                    }
                                } else {
                                    /* node 1355: if (round <= 1.5) -> 1356 else 1359 */
                                    if (round <= 1.5) {
                                        /* node 1356: if (mcs <= 18.5) -> 1357 else 1358 */
                                        if (mcs <= 18.5) {
                                            return 1357;
                                        } else {
                                            return 1358;
                                        }
                                    } else {
                                        /* node 1359: if (nb_rb <= 267.5) -> 1360 else 1361 */
                                        if (nb_rb <= 267.5) {
                                            return 1360;
                                        } else {
                                            return 1361;
                                        }
                                    }
                                }
                            }
                        } else {
                            /* node 1362: if (round <= 0.5) -> 1363 else 1378 */
                            if (round <= 0.5) {
                                /* node 1363: if (mcs <= 22.5) -> 1364 else 1371 */
                                if (mcs <= 22.5) {
                                    /* node 1364: if (nb_rb <= 252.5) -> 1365 else 1368 */
                                    if (nb_rb <= 252.5) {
                                        /* node 1365: if (mcs <= 21.5) -> 1366 else 1367 */
                                        if (mcs <= 21.5) {
                                            return 1366;
                                        } else {
                                            return 1367;
                                        }
                                    } else {
                                        /* node 1368: if (mcs <= 21.5) -> 1369 else 1370 */
                                        if (mcs <= 21.5) {
                                            return 1369;
                                        } else {
                                            return 1370;
                                        }
                                    }
                                } else {
                                    /* node 1371: if (mcs <= 27.5) -> 1372 else 1375 */
                                    if (mcs <= 27.5) {
                                        /* node 1372: if (nb_rb <= 246.5) -> 1373 else 1374 */
                                        if (nb_rb <= 246.5) {
                                            return 1373;
                                        } else {
                                            return 1374;
                                        }
                                    } else {
                                        /* node 1375: if (nb_rb <= 244.0) -> 1376 else 1377 */
                                        if (nb_rb <= 244) {
                                            return 1376;
                                        } else {
                                            return 1377;
                                        }
                                    }
                                }
                            } else {
                                /* node 1378: if (mcs <= 23.5) -> 1379 else 1386 */
                                if (mcs <= 23.5) {
                                    /* node 1379: if (nb_rb <= 243.5) -> 1380 else 1383 */
                                    if (nb_rb <= 243.5) {
                                        /* node 1380: if (nb_rb <= 231.5) -> 1381 else 1382 */
                                        if (nb_rb <= 231.5) {
                                            return 1381;
                                        } else {
                                            return 1382;
                                        }
                                    } else {
                                        /* node 1383: if (nb_rb <= 259.5) -> 1384 else 1385 */
                                        if (nb_rb <= 259.5) {
                                            return 1384;
                                        } else {
                                            return 1385;
                                        }
                                    }
                                } else {
                                    /* node 1386: if (nb_rb <= 252.5) -> 1387 else 1390 */
                                    if (nb_rb <= 252.5) {
                                        /* node 1387: if (mcs <= 26.5) -> 1388 else 1389 */
                                        if (mcs <= 26.5) {
                                            return 1388;
                                        } else {
                                            return 1389;
                                        }
                                    } else {
                                        /* node 1390: if (nb_rb <= 263.5) -> 1391 else 1392 */
                                        if (nb_rb <= 263.5) {
                                            return 1391;
                                        } else {
                                            return 1392;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


int LeafModelExported_predict_runtime_cost_p70(int mcs, int nb_symbol, int nb_rb, int round) {
    int leaf_id;

    leaf_id = LeafModelExported_predict_leaf_id(mcs, nb_symbol, nb_rb, round);
    switch (leaf_id) {
        case 5: return 23;
        case 6: return 20;
        case 10: return 33;
        case 12: return 35;
        case 13: return 34;
        case 17: return 44;
        case 18: return 44;
        case 21: return 45;
        case 22: return 46;
        case 23: return 47;
        case 26: return 46;
        case 28: return 48;
        case 29: return 47;
        case 31: return 50;
        case 33: return 50;
        case 34: return 50;
        case 37: return 46;
        case 38: return 38;
        case 40: return 52;
        case 44: return 70;
        case 45: return 70;
        case 46: return 75;
        case 47: return 72;
        case 53: return 33;
        case 55: return 34;
        case 56: return 33;
        case 60: return 35;
        case 61: return 35;
        case 62: return 35;
        case 64: return 34;
        case 65: return 34;
        case 67: return 35;
        case 71: return 37;
        case 72: return 37;
        case 74: return 38;
        case 75: return 40;
        case 78: return 39;
        case 79: return 42;
        case 80: return 40;
        case 84: return 35;
        case 86: return 39;
        case 88: return 37;
        case 89: return 38;
        case 90: return 43;
        case 94: return 40;
        case 96: return 37;
        case 97: return 38;
        case 99: return 44;
        case 100: return 44;
        case 104: return 43;
        case 105: return 43;
        case 107: return 46;
        case 108: return 44;
        case 109: return 45;
        case 116: return 47;
        case 117: return 48;
        case 119: return 49;
        case 120: return 50;
        case 123: return 73;
        case 124: return 72;
        case 126: return 73;
        case 127: return 80;
        case 131: return 71;
        case 132: return 73;
        case 134: return 77;
        case 135: return 78;
        case 138: return 76;
        case 139: return 79;
        case 141: return 80;
        case 142: return 84;
        case 147: return 80;
        case 148: return 81;
        case 149: return 87;
        case 152: return 83;
        case 153: return 86;
        case 155: return 90;
        case 156: return 91;
        case 160: return 88;
        case 161: return 111;
        case 163: return 113;
        case 164: return 82;
        case 167: return 112;
        case 168: return 116;
        case 169: return 115;
        case 174: return 87;
        case 176: return 88;
        case 177: return 87;
        case 180: return 92;
        case 181: return 90;
        case 183: return 92;
        case 184: return 93;
        case 188: return 114;
        case 189: return 113;
        case 191: return 113;
        case 192: return 114;
        case 194: return 114;
        case 196: return 115;
        case 197: return 114;
        case 202: return 111;
        case 203: return 110;
        case 205: return 115;
        case 206: return 113;
        case 209: return 115;
        case 210: return 117;
        case 212: return 125;
        case 213: return 119;
        case 217: return 116;
        case 218: return 124;
        case 220: return 127;
        case 221: return 128;
        case 223: return 150;
        case 224: return 152;
        case 233: return 52;
        case 234: return 53;
        case 235: return 47;
        case 238: return 40;
        case 239: return 42;
        case 241: return 43;
        case 242: return 46;
        case 246: return 54;
        case 247: return 56;
        case 249: return 43;
        case 250: return 45;
        case 253: return 44;
        case 254: return 46;
        case 256: return 46;
        case 257: return 47;
        case 262: return 42;
        case 263: return 44;
        case 265: return 47;
        case 266: return 46;
        case 269: return 47;
        case 270: return 49;
        case 271: return 71;
        case 273: return 73;
        case 274: return 76;
        case 278: return 50;
        case 279: return 46;
        case 281: return 50;
        case 284: return 56;
        case 285: return 61;
        case 286: return 74;
        case 289: return 79;
        case 291: return 83;
        case 292: return 84;
        case 294: return 61;
        case 295: return 70;
        case 302: return 47;
        case 303: return 47;
        case 304: return 49;
        case 307: return 47;
        case 308: return 46;
        case 310: return 47;
        case 311: return 47;
        case 315: return 48;
        case 316: return 46;
        case 318: return 46;
        case 319: return 46;
        case 321: return 49;
        case 322: return 47;
        case 325: return 47;
        case 327: return 46;
        case 329: return 47;
        case 330: return 48;
        case 332: return 75;
        case 333: return 74;
        case 338: return 46;
        case 339: return 47;
        case 340: return 48;
        case 342: return 73;
        case 345: return 75;
        case 346: return 74;
        case 348: return 75;
        case 349: return 75;
        case 354: return 73;
        case 355: return 75;
        case 357: return 77;
        case 358: return 77;
        case 361: return 77;
        case 362: return 80;
        case 363: return 84;
        case 366: return 82;
        case 368: return 80;
        case 369: return 85;
        case 372: return 84;
        case 373: return 86;
        case 375: return 89;
        case 376: return 86;
        case 384: return 42;
        case 385: return 44;
        case 387: return 50;
        case 388: return 52;
        case 391: return 80;
        case 392: return 96;
        case 394: return 102;
        case 395: return 115;
        case 399: return 102;
        case 400: return 107;
        case 402: return 112;
        case 403: return 126;
        case 406: return 120;
        case 407: return 122;
        case 409: return 126;
        case 410: return 135;
        case 415: return 120;
        case 416: return 148;
        case 418: return 139;
        case 419: return 160;
        case 422: return 130;
        case 423: return 152;
        case 425: return 154;
        case 426: return 161;
        case 430: return 128;
        case 431: return 151;
        case 433: return 159;
        case 434: return 164;
        case 437: return 162;
        case 438: return 166;
        case 440: return 173;
        case 441: return 189;
        case 447: return 149;
        case 448: return 163;
        case 450: return 141;
        case 451: return 158;
        case 454: return 159;
        case 455: return 174;
        case 457: return 188;
        case 458: return 166;
        case 462: return 179;
        case 463: return 212;
        case 465: return 199;
        case 466: return 214;
        case 467: return 243;
        case 472: return 196;
        case 473: return 202;
        case 475: return 204;
        case 476: return 230;
        case 479: return 231;
        case 480: return 210;
        case 482: return 230;
        case 483: return 249;
        case 487: return 226;
        case 488: return 248;
        case 490: return 252;
        case 491: return 260;
        case 493: return 307;
        case 494: return 346;
        case 501: return 170;
        case 502: return 192;
        case 504: return 168;
        case 505: return 175;
        case 508: return 176;
        case 509: return 198;
        case 511: return 192;
        case 512: return 203;
        case 516: return 176;
        case 517: return 187;
        case 519: return 198;
        case 520: return 205;
        case 523: return 205;
        case 524: return 207;
        case 526: return 214;
        case 527: return 236;
        case 532: return 181;
        case 533: return 204;
        case 535: return 206;
        case 536: return 242;
        case 539: return 213;
        case 540: return 215;
        case 542: return 224;
        case 543: return 227;
        case 547: return 225;
        case 548: return 233;
        case 550: return 253;
        case 551: return 244;
        case 554: return 257;
        case 555: return 260;
        case 557: return 274;
        case 558: return 279;
        case 564: return 248;
        case 565: return 235;
        case 567: return 257;
        case 568: return 274;
        case 571: return 259;
        case 572: return 273;
        case 574: return 284;
        case 575: return 288;
        case 579: return 274;
        case 580: return 300;
        case 582: return 244;
        case 583: return 304;
        case 586: return 305;
        case 587: return 368;
        case 588: return 401;
        case 593: return 293;
        case 594: return 306;
        case 596: return 339;
        case 597: return 291;
        case 600: return 317;
        case 601: return 335;
        case 603: return 361;
        case 604: return 430;
        case 608: return 332;
        case 609: return 366;
        case 610: return 399;
        case 612: return 446;
        case 613: return 512;
        case 623: return 41;
        case 624: return 42;
        case 626: return 44;
        case 627: return 44;
        case 630: return 44;
        case 631: return 45;
        case 633: return 45;
        case 634: return 46;
        case 638: return 45;
        case 639: return 44;
        case 640: return 47;
        case 642: return 46;
        case 644: return 50;
        case 645: return 49;
        case 646: return 69;
        case 651: return 46;
        case 653: return 45;
        case 654: return 45;
        case 656: return 45;
        case 657: return 49;
        case 659: return 46;
        case 660: return 73;
        case 664: return 71;
        case 665: return 76;
        case 666: return 72;
        case 667: return 76;
        case 673: return 49;
        case 674: return 48;
        case 676: return 46;
        case 677: return 48;
        case 680: return 48;
        case 681: return 50;
        case 684: return 50;
        case 685: return 48;
        case 687: return 48;
        case 688: return 49;
        case 692: return 47;
        case 694: return 50;
        case 695: return 48;
        case 698: return 74;
        case 699: return 75;
        case 700: return 77;
        case 704: return 74;
        case 705: return 75;
        case 707: return 76;
        case 708: return 76;
        case 711: return 77;
        case 712: return 75;
        case 714: return 79;
        case 715: return 78;
        case 719: return 49;
        case 720: return 52;
        case 724: return 74;
        case 725: return 76;
        case 727: return 76;
        case 728: return 77;
        case 730: return 78;
        case 732: return 81;
        case 733: return 80;
        case 738: return 76;
        case 739: return 78;
        case 741: return 79;
        case 742: return 82;
        case 744: return 77;
        case 746: return 83;
        case 747: return 83;
        case 751: return 79;
        case 752: return 83;
        case 754: return 84;
        case 755: return 84;
        case 757: return 84;
        case 759: return 86;
        case 760: return 89;
        case 768: return 79;
        case 769: return 77;
        case 771: return 79;
        case 772: return 81;
        case 775: return 82;
        case 776: return 83;
        case 778: return 83;
        case 779: return 84;
        case 783: return 84;
        case 784: return 84;
        case 786: return 85;
        case 787: return 83;
        case 790: return 85;
        case 791: return 85;
        case 793: return 86;
        case 794: return 88;
        case 799: return 85;
        case 800: return 85;
        case 802: return 87;
        case 803: return 88;
        case 805: return 89;
        case 807: return 89;
        case 808: return 90;
        case 810: return 114;
        case 812: return 119;
        case 813: return 119;
        case 819: return 86;
        case 820: return 85;
        case 821: return 86;
        case 824: return 87;
        case 825: return 88;
        case 826: return 88;
        case 830: return 115;
        case 831: return 115;
        case 832: return 114;
        case 833: return 116;
        case 837: return 87;
        case 838: return 114;
        case 841: return 114;
        case 842: return 111;
        case 844: return 116;
        case 845: return 119;
        case 849: return 118;
        case 850: return 122;
        case 852: return 123;
        case 853: return 122;
        case 855: return 126;
        case 856: return 128;
        case 862: return 90;
        case 863: return 118;
        case 865: return 87;
        case 866: return 109;
        case 870: return 118;
        case 871: return 122;
        case 873: return 125;
        case 874: return 129;
        case 876: return 109;
        case 877: return 120;
        case 881: return 126;
        case 882: return 150;
        case 883: return 127;
        case 885: return 127;
        case 888: return 158;
        case 889: return 161;
        case 891: return 133;
        case 892: return 138;
        case 894: return 178;
        case 895: return 230;
        case 904: return 114;
        case 905: return 118;
        case 906: return 126;
        case 909: return 125;
        case 910: return 125;
        case 912: return 130;
        case 913: return 131;
        case 917: return 127;
        case 918: return 148;
        case 920: return 114;
        case 921: return 116;
        case 924: return 156;
        case 925: return 149;
        case 927: return 159;
        case 928: return 165;
        case 933: return 126;
        case 934: return 127;
        case 936: return 132;
        case 937: return 134;
        case 939: return 154;
        case 941: return 155;
        case 942: return 154;
        case 946: return 152;
        case 947: return 153;
        case 949: return 162;
        case 950: return 164;
        case 953: return 163;
        case 954: return 185;
        case 956: return 195;
        case 957: return 184;
        case 963: return 154;
        case 964: return 154;
        case 966: return 155;
        case 967: return 156;
        case 970: return 165;
        case 971: return 167;
        case 973: return 173;
        case 974: return 175;
        case 978: return 164;
        case 979: return 163;
        case 981: return 169;
        case 982: return 171;
        case 985: return 189;
        case 986: return 190;
        case 988: return 202;
        case 989: return 206;
        case 994: return 198;
        case 995: return 205;
        case 997: return 200;
        case 998: return 164;
        case 1001: return 206;
        case 1002: return 207;
        case 1004: return 236;
        case 1005: return 237;
        case 1008: return 235;
        case 1010: return 238;
        case 1011: return 238;
        case 1014: return 247;
        case 1015: return 247;
        case 1016: return 247;
        case 1023: return 219;
        case 1024: return 227;
        case 1026: return 255;
        case 1027: return 270;
        case 1030: return 233;
        case 1031: return 242;
        case 1033: return 247;
        case 1034: return 251;
        case 1038: return 232;
        case 1039: return 264;
        case 1041: return 266;
        case 1042: return 278;
        case 1045: return 264;
        case 1046: return 295;
        case 1048: return 297;
        case 1049: return 309;
        case 1054: return 247;
        case 1055: return 260;
        case 1057: return 262;
        case 1058: return 267;
        case 1061: return 268;
        case 1062: return 292;
        case 1064: return 305;
        case 1065: return 308;
        case 1069: return 290;
        case 1070: return 298;
        case 1072: return 307;
        case 1073: return 313;
        case 1076: return 310;
        case 1077: return 319;
        case 1079: return 343;
        case 1080: return 359;
        case 1086: return 276;
        case 1087: return 311;
        case 1089: return 318;
        case 1090: return 350;
        case 1093: return 321;
        case 1094: return 367;
        case 1096: return 347;
        case 1097: return 362;
        case 1101: return 335;
        case 1102: return 337;
        case 1104: return 347;
        case 1105: return 348;
        case 1108: return 342;
        case 1109: return 375;
        case 1111: return 389;
        case 1112: return 384;
        case 1117: return 307;
        case 1118: return 336;
        case 1120: return 343;
        case 1121: return 379;
        case 1124: return 347;
        case 1125: return 365;
        case 1127: return 380;
        case 1128: return 395;
        case 1132: return 375;
        case 1133: return 385;
        case 1135: return 410;
        case 1136: return 425;
        case 1139: return 395;
        case 1140: return 414;
        case 1142: return 431;
        case 1143: return 439;
        case 1151: return 288;
        case 1152: return 292;
        case 1154: return 282;
        case 1155: return 285;
        case 1158: return 302;
        case 1159: return 300;
        case 1160: return 310;
        case 1164: return 285;
        case 1165: return 300;
        case 1166: return 313;
        case 1169: return 314;
        case 1170: return 315;
        case 1172: return 323;
        case 1173: return 325;
        case 1178: return 325;
        case 1179: return 343;
        case 1181: return 348;
        case 1182: return 324;
        case 1185: return 352;
        case 1186: return 326;
        case 1188: return 346;
        case 1189: return 363;
        case 1193: return 386;
        case 1194: return 370;
        case 1196: return 377;
        case 1197: return 390;
        case 1200: return 368;
        case 1201: return 364;
        case 1203: return 364;
        case 1204: return 367;
        case 1210: return 364;
        case 1211: return 376;
        case 1213: return 410;
        case 1214: return 407;
        case 1217: return 392;
        case 1218: return 408;
        case 1220: return 415;
        case 1221: return 447;
        case 1225: return 425;
        case 1226: return 475;
        case 1228: return 364;
        case 1229: return 417;
        case 1231: return 470;
        case 1233: return 559;
        case 1234: return 616;
        case 1239: return 429;
        case 1240: return 445;
        case 1242: return 446;
        case 1243: return 485;
        case 1246: return 451;
        case 1247: return 506;
        case 1249: return 490;
        case 1250: return 489;
        case 1254: return 512;
        case 1255: return 557;
        case 1257: return 449;
        case 1258: return 554;
        case 1261: return 547;
        case 1262: return 568;
        case 1264: return 656;
        case 1265: return 721;
        case 1272: return 374;
        case 1273: return 378;
        case 1275: return 391;
        case 1276: return 392;
        case 1279: return 403;
        case 1280: return 401;
        case 1282: return 406;
        case 1283: return 404;
        case 1287: return 410;
        case 1288: return 426;
        case 1290: return 405;
        case 1291: return 405;
        case 1294: return 412;
        case 1295: return 431;
        case 1297: return 443;
        case 1298: return 444;
        case 1303: return 471;
        case 1304: return 457;
        case 1306: return 450;
        case 1307: return 452;
        case 1310: return 447;
        case 1311: return 448;
        case 1313: return 446;
        case 1314: return 448;
        case 1318: return 459;
        case 1319: return 465;
        case 1321: return 475;
        case 1322: return 466;
        case 1325: return 484;
        case 1326: return 482;
        case 1328: return 487;
        case 1329: return 484;
        case 1335: return 476;
        case 1336: return 495;
        case 1338: return 543;
        case 1339: return 548;
        case 1342: return 490;
        case 1343: return 499;
        case 1345: return 530;
        case 1346: return 536;
        case 1350: return 539;
        case 1351: return 606;
        case 1353: return 570;
        case 1354: return 600;
        case 1357: return 575;
        case 1358: return 610;
        case 1360: return 668;
        case 1361: return 655;
        case 1366: return 594;
        case 1367: return 658;
        case 1369: return 662;
        case 1370: return 735;
        case 1373: return 508;
        case 1374: return 572;
        case 1376: return 642;
        case 1377: return 706;
        case 1381: return 601;
        case 1382: return 660;
        case 1384: return 678;
        case 1385: return 722;
        case 1388: return 737;
        case 1389: return 823;
        case 1391: return 854;
        case 1392: return 884;
        default:
            return 282;
    }
}
