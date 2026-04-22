# gNB_scheduler_ulsch RB遍历替换代码状态

**Session ID:** ses_2697f3d63ffeoMG0rDU7VTDI1W
**Created:** 4/16/2026, 9:35:14 AM
**Updated:** 4/16/2026, 9:19:10 PM

---

## User

现在关于gNB_scheduler_ulsch手动替换RB用于遍历足够多的RB的代码写好了吗？有相关功能吗？

---

## Assistant (Plan · glm-5 · 53.9s)

_Thinking:_

用户在问关于 `gNB_scheduler_ulsch` 中手动替换 RB 用于遍历足够多的 RB 的代码是否已经写好了，以及是否有相关功能。

我需要搜索代码库来了解：
1. `gNB_scheduler_ulsch` 相关的代码在哪里
2. 是否有手动替换 RB 的相关代码
3. 这个功能的实现状态

让我先搜索相关文件和代码。

**Tool: grep**

**Input:**
```json
{
  "pattern": "gNB_scheduler_ulsch"
}
```

**Output:**
```
Found 4 matches
/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c:
  Line 22: /*! \file gNB_scheduler_ulsch.c


/home/bupt/wlh/ran/CMakeLists.txt:
  Line 1225:   ${NR_GNB_MAC_DIR}/gNB_scheduler_ulsch.c


/home/bupt/wlh/ran/doc/MAC/mac-usage.md:
  Line 38: [`gNB_scheduler_ulsch.c`](../../openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c)


/home/bupt/wlh/ran/doc/Doxyfile:
  Line 1678: @CMAKE_CURRENT_SOURCE_DIR@/../openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c \


(Some paths were inaccessible and skipped)
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "手动替换.*RB|RB.*遍历|手动.*RB"
}
```

**Output:**
```
No files found
```

---

## Assistant (Plan · glm-5 · 29.9s)

_Thinking:_

找到了 `gNB_scheduler_ulsch.c` 文件。让我查看这个文件的内容，特别是关于 RB 分配的相关代码。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c"
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
1: /*
2:  * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
3:  * contributor license agreements.  See the NOTICE file distributed with
4:  * this work for additional information regarding copyright ownership.
5:  * The OpenAirInterface Software Alliance licenses this file to You under
6:  * the OAI Public License, Version 1.1  (the "License"); you may not use this file
7:  * except in compliance with the License.
8:  * You may obtain a copy of the License at
9:  *
10:  *      http://www.openairinterface.org/?page_id=698
11:  *
12:  * Unless required by applicable law or agreed to in writing, software
13:  * distributed under the License is distributed on an "AS IS" BASIS,
14:  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
15:  * See the License for the specific language governing permissions and
16:  * limitations under the License.
17:  *-------------------------------------------------------------------------------
18:  * For more information about the OpenAirInterface (OAI) Software Alliance:
19:  *      contact@openairinterface.org
20:  */
21: 
22: /*! \file gNB_scheduler_ulsch.c
23:  * \brief gNB procedures for the ULSCH transport channel
24:  * \author Navid Nikaein and Raymond Knopp, Guido Casati
25:  * \date 2019
26:  * \email: guido.casati@iis.fraunhofer.de
27:  * \version 1.0
28:  * @ingroup _mac
29:  */
30: 
31: 
32: #include "LAYER2/NR_MAC_gNB/mac_proto.h"
33: #include "executables/softmodem-common.h"
34: #include "common/utils/nr/nr_common.h"
35: #include "utils.h"
36: #include <openair2/UTIL/OPT/opt.h>
37: #include "LAYER2/NR_MAC_COMMON/nr_mac_extern.h"
38: #include "LAYER2/nr_rlc/nr_rlc_oai_api.h"
39: #include "LAYER2/RLC/rlc.h"
40: #include <stdlib.h>
41: #include <stdint.h>
42: 
43: static void compute_rb_boundaries_for_mcs(uint8_t mcs, uint16_t R, uint8_t Qm,
44:                                           uint16_t symbols, uint16_t dmrs,
45:                                           uint8_t layers, uint16_t *rb_values,
46:                                           uint8_t *max_cb)
47: {
48:   uint32_t Kcb_1 = 8448;
49:   uint32_t Kcb_2 = 3840;
50:   uint8_t num_values = 0;
51:   uint8_t last_cb = 0;
52:   uint16_t min_rb = 5;
53:   uint16_t max_rb = 273;
54:   
55:   for (uint16_t rb = min_rb; rb <= max_rb && num_values < 32; rb++) {
56:     uint32_t tbs_bits = nr_compute_tbs(Qm, R, rb, symbols, dmrs, 0, 0, layers);
57:     uint8_t BG = get_BG(tbs_bits, R);
58:     uint32_t Kcb = (BG == 1) ? Kcb_1 : Kcb_2;
59:     uint8_t num_cb;
60:     if (tbs_bits <= Kcb) {
61:       num_cb = 1;
62:     } else {
63:       num_cb = tbs_bits / (Kcb - 24);
64:       if ((Kcb - 24) * num_cb < tbs_bits)
65:         num_cb++;
66:     }
67:     if (num_cb != last_cb) {
68:       rb_values[num_values] = rb;
69:       num_values++;
70:       last_cb = num_cb;
71:     }
72:   }
73:   *max_cb = last_cb;
74: }
75: #include "LAYER2/NR_MAC_gNB/leaf_model_exported.h"
76: #include "LAYER2/NR_MAC_gNB/leaf_model_wrapper.h"
77: //#define SRS_IND_DEBUG
78: 
79: 
80: 
81: /* 生成 [low, high] 之间的随机整数，要求 high >= low */
82: static inline uint16_t rand_in_range(uint16_t low, uint16_t high)
83: {
84:   if (high <= low)
85:     return low;
86:   return low + (rand() % (high - low + 1));
87: }
88: 
89: 
90: int get_ul_tda(gNB_MAC_INST *nrmac, int frame, int slot)
91: {
92:   /* we assume that this function is mutex-protected from outside */
93:   NR_SCHED_ENSURE_LOCKED(&nrmac->sched_lock);
94: 
95:   /* there is a mixed slot only when in TDD */
96:   frame_structure_t *fs = &nrmac->frame_structure;
97: 
98:   if (fs->frame_type == TDD) {
99:     // if there is uplink symbols in mixed slot
100:     int s = get_slot_idx_in_period(slot, fs);
101:     tdd_bitmap_t *tdd_slot_bitmap = fs->period_cfg.tdd_slot_bitmap;
102:     if ((tdd_slot_bitmap[s].num_ul_symbols > 1) && is_mixed_slot(s, fs)) {
103:       return 2;
104:     }
105:   }
106: 
107:   // Avoid slots with the SRS
108:   UE_iterator(nrmac->UE_info.list, UE) {
109:     NR_sched_srs_t sched_srs = UE->UE_sched_ctrl.sched_srs;
110:     if(sched_srs.srs_scheduled && sched_srs.frame == frame && sched_srs.slot == slot)
111:       return 1;
112:   }
113: 
114:   return 0; // if FDD or not mixed slot in TDD, for now use default TDA (TODO handle CSI-RS slots)
115: }
116: 
117: static int compute_ph_factor(int mu, int tbs_bits, int rb, int n_layers, int n_symbols, int n_dmrs, long *deltaMCS, bool include_bw)
118: {
119:   // 38.213 7.1.1
120:   // if the PUSCH transmission is over more than one layer delta_tf = 0
121:   float delta_tf = 0;
122:   if(deltaMCS != NULL && n_layers == 1) {
123:     const int n_re = (NR_NB_SC_PER_RB * n_symbols - n_dmrs) * rb;
124:     const float BPRE = (float) tbs_bits/n_re;  //TODO change for PUSCH with CSI
125:     const float f = pow(2, BPRE * 1.25);
126:     const float beta = 1.0f; //TODO change for PUSCH with CSI
127:     delta_tf = (10 * log10((f - 1) * beta));
128:     LOG_D(NR_MAC,
129:           "PH factor delta_tf %f (n_re %d, n_rb %d, n_dmrs %d, n_symbols %d, tbs %d BPRE %f f %f)\n",
130:           delta_tf,
131:           n_re,
132:           rb,
133:           n_dmrs,
134:           n_symbols,
135:           tbs_bits,
136:           BPRE,
137:           f);
138:   }
139:   const float bw_factor = (include_bw) ? 10 * log10(rb << mu) : 0;
140:   return ((int)roundf(delta_tf + bw_factor));
141: }
142: 
143: /* \brief over-estimate the BSR index, given real_index.
144:  *
145:  * BSR does not account for headers, so we need to estimate. See 38.321
146:  * 6.1.3.1: "The size of the RLC headers and MAC subheaders are not considered
147:  * in the buffer size computation." */
148: static int overestim_bsr_index(int real_index)
149: {
150:   /* if UE reports BSR 0, it means "no data"; otherwise, overestimate to
151:    * account for headers */
152:   const int add_overestim = 1;
153:   return real_index > 0 ? real_index + add_overestim : real_index;
154: }
155: 
156: static int estimate_ul_buffer_short_bsr(const NR_BSR_SHORT *bsr)
157: {
158:   /* NOTE: the short BSR might be for different LCGID than 0, but we do not
159:    * differentiate them */
160:   int rep_idx = bsr->Buffer_size;
161:   int estim_idx = overestim_bsr_index(rep_idx);
162:   int max = sizeofArray(NR_SHORT_BSR_TABLE) - 1;
163:   int idx = min(estim_idx, max);
164:   int estim_size = NR_SHORT_BSR_TABLE[idx];
165:   LOG_D(NR_MAC, "short BSR LCGID %d index %d estim index %d size %d\n", bsr->LcgID, rep_idx, estim_idx, estim_size);
166:   return estim_size;
167: }
168: 
169: static int estimate_ul_buffer_long_bsr(const NR_BSR_LONG *bsr)
170: {
171:   LOG_D(NR_MAC,
172:         "LONG BSR, LCG ID(7-0) %d/%d/%d/%d/%d/%d/%d/%d\n",
173:         bsr->LcgID7,
174:         bsr->LcgID6,
175:         bsr->LcgID5,
176:         bsr->LcgID4,
177:         bsr->LcgID3,
178:         bsr->LcgID2,
179:         bsr->LcgID1,
180:         bsr->LcgID0);
181:   bool bsr_active[8] = {bsr->LcgID0 != 0, bsr->LcgID1 != 0, bsr->LcgID2 != 0, bsr->LcgID3 != 0, bsr->LcgID4 != 0, bsr->LcgID5 != 0, bsr->LcgID6 != 0, bsr->LcgID7 != 0};
182: 
183:   int estim_size = 0;
184:   int max = sizeofArray(NR_LONG_BSR_TABLE) - 1;
185:   uint8_t *payload = ((uint8_t*) bsr) + 1;
186:   int m = 0;
187:   const int total_lcgids = 8; /* see 38.321 6.1.3.1 */
188:   for (int n = 0; n < total_lcgids; n++) {
189:     if (!bsr_active[n])
190:       continue;
191:     int rep_idx = payload[m];
192:     int estim_idx = overestim_bsr_index(rep_idx);
193:     int idx = min(estim_idx, max);
194:     estim_size += NR_LONG_BSR_TABLE[idx];
195: 
196:     LOG_D(NR_MAC, "LONG BSR LCGID/m %d/%d Index %d estim index %d size %d", n, m, rep_idx, estim_idx, estim_size);
197:     m++;
198:   }
199:   return estim_size;
200: }
201: 
202: //  For both UL-SCH except:
203: //   - UL-SCH: fixed-size MAC CE(known by LCID)
204: //   - UL-SCH: padding
205: //   - UL-SCH: MSG3 48-bits
206: //  |0|1|2|3|4|5|6|7|  bit-wise
207: //  |R|F|   LCID    |
208: //  |       L       |
209: //  |0|1|2|3|4|5|6|7|  bit-wise
210: //  |R|F|   LCID    |
211: //  |       L       |
212: //  |       L       |
213: //
214: //  For:
215: //   - UL-SCH: fixed-size MAC CE(known by LCID)
216: //   - UL-SCH: padding, for single/multiple 1-oct padding CE(s)
217: //   - UL-SCH: MSG3 48-bits
218: //  |0|1|2|3|4|5|6|7|  bit-wise
219: //  |R|R|   LCID    |
220: //
221: //  LCID: The Logical Channel ID field identifies the logical channel instance of the corresponding MAC SDU or the type of the corresponding MAC CE or padding as described in Tables 6.2.1-1 and 6.2.1-2 for the DL-SCH and UL-SCH respectively. There is one LCID field per MAC subheader. The LCID field size is 6 bits;
222: //  L: The Length field indicates the length of the corresponding MAC SDU or variable-sized MAC CE in bytes. There is one L field per MAC subheader except for subheaders corresponding to fixed-sized MAC CEs and padding. The size of the L field is indicated by the F field;
223: //  F: length of L is 0:8 or 1:16 bits wide
224: //  R: Reserved bit, set to zero.
225: 
226: // return: length of subPdu header
227: // 3GPP TS 38.321 Section 6
228: uint8_t decode_ul_mac_sub_pdu_header(uint8_t *pduP, uint8_t *lcid, uint16_t *length)
229: {
230:   uint16_t mac_subheader_len = 1;
231:   *lcid = pduP[0] & 0x3F;
232: 
233:   switch (*lcid) {
234:     case UL_SCH_LCID_CCCH_64_BITS:
235:       *length = 8;
236:       break;
237:     case UL_SCH_LCID_SRB1:
238:     case UL_SCH_LCID_SRB2:
239:     case UL_SCH_LCID_DTCH ...(UL_SCH_LCID_DTCH + 28):
240:     case UL_SCH_LCID_L_TRUNCATED_BSR:
241:     case UL_SCH_LCID_L_BSR:
242:       if (pduP[0] & 0x40) { // F = 1
243:         mac_subheader_len = 3;
244:         *length = (pduP[1] << 8) + pduP[2];
245:       } else { // F = 0
246:         mac_subheader_len = 2;
247:         *length = pduP[1];
248:       }
249:       break;
250:     case UL_SCH_LCID_CCCH_48_BITS:
251:       *length = 6;
252:       break;
253:     case UL_SCH_LCID_SINGLE_ENTRY_PHR:
254:     case UL_SCH_LCID_C_RNTI:
255:       *length = 2;
256:       break;
257:     case UL_SCH_LCID_S_TRUNCATED_BSR:
258:     case UL_SCH_LCID_S_BSR:
259:       *length = 1;
260:       break;
261:     case UL_SCH_LCID_PADDING:
262:       // Nothing to do
263:       break;
264:     default:
265:       LOG_E(NR_MAC, "LCID %0x not handled yet!\n", *lcid);
266:       break;
267:   }
268: 
269:   LOG_D(NR_MAC, "Decoded LCID 0x%X, header bytes: %d, payload bytes %d\n", *lcid, mac_subheader_len, *length);
270: 
271:   return mac_subheader_len;
272: }
273: 
274: static rnti_t lcid_crnti_lookahead(uint8_t *pdu, uint32_t pdu_len)
275: {
276:   while (pdu_len > 0) {
277:     uint16_t mac_len = 0;
278:     uint8_t lcid = 0;
279:     uint16_t mac_subheader_len = decode_ul_mac_sub_pdu_header(pdu, &lcid, &mac_len);
280:     // Check for valid PDU
281:     if (mac_subheader_len + mac_len > pdu_len) {
282:       LOG_E(NR_MAC,
283:             "Invalid PDU! mac_subheader_len: %d, mac_len: %d, remaining pdu_len: %d\n",
284:             mac_subheader_len,
285:             mac_len,
286:             pdu_len);
287: 
288:       LOG_E(NR_MAC, "Residual UL MAC PDU: ");
289:       uint32_t print_len = pdu_len > 30 ? 30 : pdu_len; // Only printf 1st - 30nd bytes
290:       for (int i = 0; i < print_len; i++)
291:         printf("%02x ", pdu[i]);
292:       printf("\n");
293:       return 0;
294:     }
295: 
296:     if (lcid == UL_SCH_LCID_C_RNTI) {
297:       // Extract C-RNTI value
298:       rnti_t crnti = ((pdu[1] & 0xFF) << 8) | (pdu[2] & 0xFF);
299:       LOG_D(NR_MAC, "Received a MAC CE for C-RNTI with %04x\n", crnti);
300:       return crnti;
301:     } else if (lcid == UL_SCH_LCID_PADDING) {
302:       // End of MAC PDU, can ignore the remaining bytes
303:       return 0;
304:     }
305: 
306:     pdu += mac_len + mac_subheader_len;
307:     pdu_len -= mac_len + mac_subheader_len;
308:   }
309:   return 0;
310: }
311: 
312: static int nr_process_mac_pdu(instance_t module_idP,
313:                               NR_UE_info_t *UE,
314:                               uint8_t CC_id,
315:                               frame_t frameP,
316:                               sub_frame_t slot,
317:                               uint8_t *pduP,
318:                               uint32_t pdu_len,
319:                               const int8_t harq_pid)
320: {
321:   int sdus = 0;
322:   NR_UE_UL_BWP_t *ul_bwp = &UE->current_UL_BWP;
323:   NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
324: 
325:   if (pduP[0] != UL_SCH_LCID_PADDING) {
326:     ws_trace_t tmp = {.nr = true,
327:                       .direction = DIRECTION_UPLINK,
328:                       .pdu_buffer = pduP,
329:                       .pdu_buffer_size = pdu_len,
330:                       .ueid = 0,
331:                       .rntiType = WS_C_RNTI,
332:                       .rnti = UE->rnti,
333:                       .sysFrame = frameP,
334:                       .subframe = slot,
335:                       .harq_pid = harq_pid};
336:     trace_pdu(&tmp);
337:   }
338: 
339: #ifdef ENABLE_MAC_PAYLOAD_DEBUG
340:   LOG_I(NR_MAC, "In %s: dumping MAC PDU in %d.%d:\n", __func__, frameP, slot);
341:   log_dump(NR_MAC, pduP, pdu_len, LOG_DUMP_CHAR, "\n");
342: #endif
343: 
344:   while (pdu_len > 0) {
345:     uint16_t mac_len = 0;
346:     uint8_t lcid = 0;
347: 
348:     uint16_t mac_subheader_len = decode_ul_mac_sub_pdu_header(pduP, &lcid, &mac_len);
349:     // Check for valid PDU
350:     if (mac_subheader_len + mac_len > pdu_len) {
351:       LOG_E(NR_MAC,
352:             "Invalid PDU in %d.%d for RNTI %04X! mac_subheader_len: %d, mac_len: %d, remaining pdu_len: %d\n",
353:             frameP,
354:             slot,
355:             UE->rnti,
356:             mac_subheader_len,
357:             mac_len,
358:             pdu_len);
359: 
360:       LOG_E(NR_MAC, "Residual UL MAC PDU: ");
361:       int print_len = pdu_len > 30 ? 30 : pdu_len; // Only printf 1st - 30nd bytes
362:       for (int i = 0; i < print_len; i++)
363:         printf("%02x ", pduP[i]);
364:       printf("\n");
365:       return 0;
366:     }
367: 
368:     LOG_D(NR_MAC,
369:           "Received UL-SCH sub-PDU with LCID 0x%X in %d.%d for RNTI %04X (remaining PDU length %d)\n",
370:           lcid,
371:           frameP,
372:           slot,
373:           UE->rnti,
374:           pdu_len);
375: 
376:     unsigned char *ce_ptr;
377: 
378:     switch (lcid) {
379:       case UL_SCH_LCID_CCCH_64_BITS:
380:       case UL_SCH_LCID_CCCH_48_BITS:
381:         if (lcid == UL_SCH_LCID_CCCH_64_BITS) {
382:           // Check if it is a valid CCCH1 message, we get all 00's messages very often
383:           bool valid_pdu = false;
384:           for (int i = 0; i < (mac_subheader_len + mac_len); i++) {
385:             if (pduP[i] != 0) {
386:               valid_pdu = true;
387:               break;
388:             }
389:           }
390:           if (!valid_pdu) {
391:             LOG_D(NR_MAC, "%s() Invalid CCCH1 message!, pdu_len: %d\n", __func__, pdu_len);
392:             return 0;
393:           }
394:         }
395: 
396:         LOG_I(MAC, "[RAPROC] Received SDU for CCCH length %d for UE %04x\n", mac_len, UE->rnti);
397: 
398:         if (prepare_initial_ul_rrc_message(RC.nrmac[module_idP], UE)) {
399:           mac_rlc_data_ind(module_idP,
400:                            UE->rnti,
401:                            module_idP,
402:                            frameP,
403:                            ENB_FLAG_YES,
404:                            MBMS_FLAG_NO,
405:                            0,
406:                            (char *)(pduP + mac_subheader_len),
407:                            mac_len,
408:                            1,
409:                            NULL);
410:         } else {
411:           LOG_E(NR_MAC, "prepare_initial_ul_rrc_message() returned false, cannot forward CCCH message\n");
412:         }
413:         break;
414: 
415:       case UL_SCH_LCID_SRB1:
416:       case UL_SCH_LCID_SRB2:
417:         AssertFatal(UE->CellGroup,
418:                     "UE %04x %d.%d: Received LCID %d which is not configured (UE has no CellGroup)\n",
419:                     UE->rnti,
420:                     frameP,
421:                     slot,
422:                     lcid);
423: 
424:         mac_rlc_data_ind(module_idP,
425:                          UE->rnti,
426:                          module_idP,
427:                          frameP,
428:                          ENB_FLAG_YES,
429:                          MBMS_FLAG_NO,
430:                          lcid,
431:                          (char *)(pduP + mac_subheader_len),
432:                          mac_len,
433:                          1,
434:                          NULL);
435: 
436:         UE->mac_stats.ul.total_sdu_bytes += mac_len;
437:         UE->mac_stats.ul.lc_bytes[lcid] += mac_len;
438:         break;
439: 
440:       case UL_SCH_LCID_DTCH ...(UL_SCH_LCID_DTCH + 28):
441:         LOG_D(NR_MAC,
442:               "[UE %04x] %d.%d : ULSCH -> UL-%s %d (gNB %ld, %d bytes)\n",
443:               UE->rnti,
444:               frameP,
445:               slot,
446:               lcid < 4 ? "DCCH" : "DTCH",
447:               lcid,
448:               module_idP,
449:               mac_len);
450:         UE->mac_stats.ul.lc_bytes[lcid] += mac_len;
451: 
452:         mac_rlc_data_ind(module_idP,
453:                          UE->rnti,
454:                          module_idP,
455:                          frameP,
456:                          ENB_FLAG_YES,
457:                          MBMS_FLAG_NO,
458:                          lcid,
459:                          (char *)(pduP + mac_subheader_len),
460:                          mac_len,
461:                          1,
462:                          NULL);
463: 
464:         sdus += 1;
465:         /* Updated estimated buffer when receiving data */
466:         if (sched_ctrl->estimated_ul_buffer >= mac_len)
467:           sched_ctrl->estimated_ul_buffer -= mac_len;
468:         else
469:           sched_ctrl->estimated_ul_buffer = 0;
470:         break;
471: 
472:       case UL_SCH_LCID_RECOMMENDED_BITRATE_QUERY:
473:         // 38.321 Ch6.1.3.20
474:         break;
475: 
476:       case UL_SCH_LCID_MULTI_ENTRY_PHR_4_OCT:
477:         LOG_E(NR_MAC, "Multi entry PHR not supported\n");
478:         break;
479: 
480:       case UL_SCH_LCID_CONFIGURED_GRANT_CONFIRMATION:
481:         // 38.321 Ch6.1.3.7
482:         break;
483: 
484:       case UL_SCH_LCID_MULTI_ENTRY_PHR_1_OCT:
485:         LOG_E(NR_MAC, "Multi entry PHR not supported\n");
486:         break;
487: 
488:       case UL_SCH_LCID_SINGLE_ENTRY_PHR:
489:         if (harq_pid < 0) {
490:           LOG_E(NR_MAC, "Invalid HARQ PID %d\n", harq_pid);
491:           return 0;
492:         }
493:         NR_sched_pusch_t *sched_pusch = &sched_ctrl->ul_harq_processes[harq_pid].sched_pusch;
494: 
495:         /* Extract SINGLE ENTRY PHR elements for PHR calculation */
496:         ce_ptr = &pduP[mac_subheader_len];
497:         NR_SINGLE_ENTRY_PHR_MAC_CE *phr = (NR_SINGLE_ENTRY_PHR_MAC_CE *)ce_ptr;
498:         /* Save the phr info */
499:         int PH;
500:         const int PCMAX = phr->PCMAX;
501:         /* 38.133 Table10.1.17.1-1 */
502:         if (phr->PH < 55) {
503:           PH = phr->PH - 32;
504:         } else if (phr->PH < 63) {
505:           PH = 24 + (phr->PH - 55) * 2;
506:         } else {
507:           PH = 38;
508:         }
509:         // in sched_ctrl we set normalized PH wrt MCS and PRBs
510:         long *deltaMCS = ul_bwp->pusch_Config ? ul_bwp->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
511:         sched_ctrl->ph = PH
512:                          + compute_ph_factor(ul_bwp->scs,
513:                                              sched_pusch->tb_size << 3,
514:                                              sched_pusch->rbSize,
515:                                              sched_pusch->nrOfLayers,
516:                                              sched_pusch->tda_info.nrOfSymbols, // n_symbols
517:                                              sched_pusch->dmrs_info.num_dmrs_symb * sched_pusch->dmrs_info.N_PRB_DMRS, // n_dmrs
518:                                              deltaMCS,
519:                                              true);
520:         sched_ctrl->ph0 = PH;
521:         /* 38.133 Table10.1.18.1-1 */
522:         sched_ctrl->pcmax = PCMAX - 29;
523:         LOG_D(NR_MAC,
524:               "SINGLE ENTRY PHR %d.%d R1 %d PH %d (%d dB) R2 %d PCMAX %d (%d dBm)\n",
525:               frameP,
526:               slot,
527:               phr->R1,
528:               PH,
529:               sched_ctrl->ph,
530:               phr->R2,
531:               PCMAX,
532:               sched_ctrl->pcmax);
533:         break;
534: 
535:       case UL_SCH_LCID_C_RNTI:
536:         for (int i = 0; i < NR_NB_RA_PROC_MAX; i++) {
537:           NR_RA_t *ra = &RC.nrmac[module_idP]->common_channels[CC_id].ra[i];
538:           if (ra->ra_state == nrRA_gNB_IDLE && ra->rnti == UE->rnti) {
539:             // Extract C-RNTI value
540:             rnti_t crnti = ((pduP[1] & 0xFF) << 8) | (pduP[2] & 0xFF);
541:             AssertFatal(false,
542:                         "Received MAC CE for C-RNTI %04x without RA running, procedure exists? Or is it a bug while decoding the "
543:                         "MAC PDU?\n",
544:                         crnti);
545:             break;
546:           }
547:         }
548:         break;
549: 
550:       case UL_SCH_LCID_S_TRUNCATED_BSR:
551:       case UL_SCH_LCID_S_BSR:
552:         /* Extract short BSR value */
553:         ce_ptr = &pduP[mac_subheader_len];
554:         sched_ctrl->estimated_ul_buffer = estimate_ul_buffer_short_bsr((NR_BSR_SHORT *)ce_ptr);
555:         LOG_W(NR_MAC, "SHORT BSR at %4d.%2d, est buf %d\n", frameP, slot, sched_ctrl->estimated_ul_buffer);
556:         break;
557: 
558:       case UL_SCH_LCID_L_TRUNCATED_BSR:
559:       case UL_SCH_LCID_L_BSR:
560:         /* Extract long BSR value */
561:         ce_ptr = &pduP[mac_subheader_len];
562:         sched_ctrl->estimated_ul_buffer = estimate_ul_buffer_long_bsr((NR_BSR_LONG *)ce_ptr);
563:         LOG_W(NR_MAC, "LONG BSR at %4d.%2d, estim buf %d\n", frameP, slot, sched_ctrl->estimated_ul_buffer);
564:         break;
565: 
566:       case UL_SCH_LCID_PADDING:
567:         // End of MAC PDU, can ignore the rest.
568:         return 0;
569: 
570:       default:
571:         LOG_E(NR_MAC, "RNTI %0x [%d.%d], received unknown MAC header (LCID = 0x%02x)\n", UE->rnti, frameP, slot, lcid);
572:         return -1;
573:         break;
574:     }
575: 
576: #ifdef ENABLE_MAC_PAYLOAD_DEBUG
577:     if (lcid < 45 || lcid == 52 || lcid == 63) {
578:       LOG_I(NR_MAC, "In %s: dumping UL MAC SDU sub-header with length %d (LCID = 0x%02x):\n", __func__, mac_subheader_len, lcid);
579:       log_dump(NR_MAC, pduP, mac_subheader_len, LOG_DUMP_CHAR, "\n");
580:       LOG_I(NR_MAC, "In %s: dumping UL MAC SDU with length %d (LCID = 0x%02x):\n", __func__, mac_len, lcid);
581:       log_dump(NR_MAC, pduP + mac_subheader_len, mac_len, LOG_DUMP_CHAR, "\n");
582:     } else {
583:       LOG_I(NR_MAC, "In %s: dumping UL MAC CE with length %d (LCID = 0x%02x):\n", __func__, mac_len, lcid);
584:       log_dump(NR_MAC, pduP + mac_subheader_len + mac_len, mac_len, LOG_DUMP_CHAR, "\n");
585:     }
586: #endif
587: 
588:     pduP += (mac_subheader_len + mac_len);
589:     pdu_len -= (mac_subheader_len + mac_len);
590:   }
591: 
592:   UE->mac_stats.ul.num_mac_sdu += sdus;
593: 
594:   return 0;
595: }
596: 
597: static void finish_nr_ul_harq(NR_UE_sched_ctrl_t *sched_ctrl, int harq_pid)
598: {
599:   NR_UE_ul_harq_t *harq = &sched_ctrl->ul_harq_processes[harq_pid];
600: 
601:   harq->ndi ^= 1;
602:   harq->round = 0;
603: 
604:   add_tail_nr_list(&sched_ctrl->available_ul_harq, harq_pid);
605: }
606: 
607: static void abort_nr_ul_harq(NR_UE_info_t *UE, int8_t harq_pid)
608: {
609:   NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
610:   NR_UE_ul_harq_t *harq = &sched_ctrl->ul_harq_processes[harq_pid];
611: 
612:   finish_nr_ul_harq(sched_ctrl, harq_pid);
613:   UE->mac_stats.ul.errors++;
614: 
615:   /* the transmission failed: the UE won't send the data we expected initially,
616:    * so retrieve to correctly schedule after next BSR */
617:   sched_ctrl->sched_ul_bytes -= harq->sched_pusch.tb_size;
618:   if (sched_ctrl->sched_ul_bytes < 0)
619:     sched_ctrl->sched_ul_bytes = 0;
620: }
621: 
622: static bool get_UE_waiting_CFRA_msg3(const gNB_MAC_INST *gNB_mac,
623:                                      const int CC_id,
624:                                      const frame_t frame,
625:                                      const sub_frame_t slot,
626:                                      rnti_t rnti)
627: {
628:   bool UE_waiting_CFRA_msg3 = false;
629:   for (int i = 0; i < NR_NB_RA_PROC_MAX; i++) {
630:     const NR_RA_t *ra = &gNB_mac->common_channels[CC_id].ra[i];
631:     if (ra->cfra && ra->ra_state == nrRA_WAIT_Msg3 && frame == ra->Msg3_frame && slot == ra->Msg3_slot && rnti == ra->rnti) {
632:       UE_waiting_CFRA_msg3 = true;
633:       break;
634:     }
635:   }
636:   return UE_waiting_CFRA_msg3;
637: }
638: 
639: void handle_nr_ul_harq(const int CC_idP,
640:                        module_id_t mod_id,
641:                        frame_t frame,
642:                        sub_frame_t slot,
643:                        const nfapi_nr_crc_t *crc_pdu)
644: {
645:   gNB_MAC_INST *nrmac = RC.nrmac[mod_id];
646:   if (nrmac->radio_config.disable_harq) {
647:     LOG_D(NR_MAC, "skipping UL feedback handling as HARQ is disabled\n");
648:     return;
649:   }
650: 
651:   NR_SCHED_LOCK(&nrmac->sched_lock);
652:   for (int i = 0; i < NR_NB_RA_PROC_MAX; ++i) {
653:     NR_RA_t *ra = &nrmac->common_channels[CC_idP].ra[i];
654:     // if we find any ongoing RA that has already scheduled MSG3
655:     // and it is expecting its reception in current frame and slot with matching RNTI
656:     // we can exit the function (no HARQ involved)
657:     if (ra->ra_state >= nrRA_WAIT_Msg3 && ra->rnti == crc_pdu->rnti && frame == ra->Msg3_frame && slot == ra->Msg3_slot) {
658:       LOG_D(NR_MAC, "UL for rnti %04x in RA (MSG3), no need to process HARQ\n", crc_pdu->rnti);
659:       NR_SCHED_UNLOCK(&nrmac->sched_lock);
660:       return;
661:     }
662:   }
663: 
664:   NR_UE_info_t *UE = find_nr_UE(&nrmac->UE_info, crc_pdu->rnti);
665:   if (!UE) {
666:     NR_SCHED_UNLOCK(&nrmac->sched_lock);
667:     LOG_E(NR_MAC, "Couldn't identify UE connected with current UL HARQ process\n");
668:     return;
669:   }
670: 
671:   NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
672:   int8_t harq_pid = sched_ctrl->feedback_ul_harq.head;
673:   LOG_D(NR_MAC, "Comparing crc_pdu->harq_id vs feedback harq_pid = %d %d\n",crc_pdu->harq_id, harq_pid);
674:   while (crc_pdu->harq_id != harq_pid || harq_pid < 0) {
675:     LOG_W(NR_MAC, "Unexpected ULSCH HARQ PID %d (have %d) for RNTI 0x%04x\n", crc_pdu->harq_id, harq_pid, crc_pdu->rnti);
676:     if (harq_pid < 0) {
677:       NR_SCHED_UNLOCK(&nrmac->sched_lock);
678:       return;
679:     }
680: 
681:     remove_front_nr_list(&sched_ctrl->feedback_ul_harq);
682:     sched_ctrl->ul_harq_processes[harq_pid].is_waiting = false;
683: 
684:     if(sched_ctrl->ul_harq_processes[harq_pid].round >= RC.nrmac[mod_id]->ul_bler.harq_round_max - 1) {
685:       LOG_W(NR_MAC, "HARQ PID %d Abort because of round exceeding\n" ,harq_pid);
686:       abort_nr_ul_harq(UE, harq_pid);
687:     } else {
688:       sched_ctrl->ul_harq_processes[harq_pid].round++;
689:       add_tail_nr_list(&sched_ctrl->retrans_ul_harq, harq_pid);
690:     }
691:     harq_pid = sched_ctrl->feedback_ul_harq.head;
692:   }
693:   remove_front_nr_list(&sched_ctrl->feedback_ul_harq);
694:   NR_UE_ul_harq_t *harq = &sched_ctrl->ul_harq_processes[harq_pid];
695:   DevAssert(harq->is_waiting);
696:   harq->feedback_slot = -1;
697:   harq->is_waiting = false;
698:   if (!crc_pdu->tb_crc_status) {
699:     finish_nr_ul_harq(sched_ctrl, harq_pid);
700:     LOG_D(NR_MAC,
701:           "Ulharq id %d crc passed for RNTI %04x\n",
702:           harq_pid,
703:           crc_pdu->rnti);
704:   } else if (harq->round >= RC.nrmac[mod_id]->ul_bler.harq_round_max  - 1) {
705:     abort_nr_ul_harq(UE, harq_pid);
706:     LOG_D(NR_MAC,
707:           "RNTI %04x: Ulharq id %d crc failed in all rounds\n",
708:           crc_pdu->rnti,
709:           harq_pid);
710:   } else {
711:     harq->round++;
712:     LOG_D(NR_MAC,
713:           "Ulharq id %d crc failed for RNTI %04x\n",
714:           harq_pid,
715:           crc_pdu->rnti);
716:     add_tail_nr_list(&sched_ctrl->retrans_ul_harq, harq_pid);
717:   }
718:   NR_SCHED_UNLOCK(&nrmac->sched_lock);
719: }
720: 
721: static void handle_msg3_failed_rx(NR_RA_t *ra, int i, int harq_round_max)
722: {
723:   // for CFRA (NSA) do not schedule retransmission of msg3
724:   if (ra->cfra) {
725:     LOG_D(NR_MAC, "Random Access %i failed at state %s (NSA msg3 reception failed)\n", i, nrra_text[ra->ra_state]);
726:     nr_clear_ra_proc(ra);
727:     return;
728:   }
729: 
730:   if (ra->msg3_round >= harq_round_max - 1) {
731:     LOG_W(NR_MAC, "Random Access %i failed at state %s (Reached msg3 max harq rounds)\n", i, nrra_text[ra->ra_state]);
732:     nr_clear_ra_proc(ra);
733:     return;
734:   }
735: 
736:   LOG_D(NR_MAC, "Random Access %i Msg3 CRC did not pass\n", i);
737:   ra->msg3_round++;
738:   ra->ra_state = nrRA_Msg3_retransmission;
739: }
740: 
741: /*
742: * When data are received on PHY and transmitted to MAC
743: */
744: static void _nr_rx_sdu(const module_id_t gnb_mod_idP,
745:                        const int CC_idP,
746:                        const frame_t frameP,
747:                        const sub_frame_t slotP,
748:                        const rnti_t rntiP,
749:                        uint8_t *sduP,
750:                        const uint32_t sdu_lenP,
751:                        const int8_t harq_pid,
752:                        const uint16_t timing_advance,
753:                        const uint8_t ul_cqi,
754:                        const uint16_t rssi)
755: {
756:   gNB_MAC_INST *gNB_mac = RC.nrmac[gnb_mod_idP];
757: 
758:   const int current_rnti = rntiP;
759:   LOG_D(NR_MAC, "rx_sdu for rnti %04x\n", current_rnti);
760:   const int target_snrx10 = gNB_mac->pusch_target_snrx10;
761:   const int rssi_threshold = gNB_mac->pusch_rssi_threshold;
762:   const int pusch_failure_thres = gNB_mac->pusch_failure_thres;
763: 
764:   NR_UE_info_t *UE = find_nr_UE(&gNB_mac->UE_info, current_rnti);
765:   bool UE_waiting_CFRA_msg3 = get_UE_waiting_CFRA_msg3(gNB_mac, CC_idP, frameP, slotP, current_rnti);
766: 
767:   if (UE && UE_waiting_CFRA_msg3 == false) {
768: 
769:     NR_UE_sched_ctrl_t *UE_scheduling_control = &UE->UE_sched_ctrl;
770: 
771:     if (sduP)
772:       T(T_GNB_MAC_UL_PDU_WITH_DATA, T_INT(gnb_mod_idP), T_INT(CC_idP),
773:         T_INT(rntiP), T_INT(frameP), T_INT(slotP), T_INT(harq_pid),
774:         T_BUFFER(sduP, sdu_lenP));
775: 
776:     UE->mac_stats.ul.total_bytes += sdu_lenP;
777:     LOG_D(NR_MAC, "[gNB %d][PUSCH %d] CC_id %d %d.%d Received ULSCH sdu from PHY (rnti %04x) ul_cqi %d TA %d sduP %p, rssi %d\n",
778:           gnb_mod_idP,
779:           harq_pid,
780:           CC_idP,
781:           frameP,
782:           slotP,
783:           current_rnti,
784:           ul_cqi,
785:           timing_advance,
786:           sduP,
787:           rssi);
788:     if (harq_pid < 0) {
789:       LOG_E(NR_MAC, "UE %04x received ULSCH when feedback UL HARQ %d (unexpected ULSCH transmission)\n", rntiP, harq_pid);
790:       return;
791:     }
792: 
793:     // if not missed detection (10dB threshold for now)
794:     if (rssi > 0) {
795:       int txpower_calc = UE_scheduling_control->ul_harq_processes[harq_pid].sched_pusch.phr_txpower_calc;
796:       UE->mac_stats.deltaMCS = txpower_calc;
797:       UE->mac_stats.NPRB = UE_scheduling_control->ul_harq_processes[harq_pid].sched_pusch.rbSize;
798:       if (ul_cqi != 0xff)
799:         UE_scheduling_control->tpc0 = nr_get_tpc(target_snrx10, ul_cqi, 30, txpower_calc);
800:       if (UE_scheduling_control->ph < 0 && UE_scheduling_control->tpc0 > 1)
801:         UE_scheduling_control->tpc0 = 1;
802: 
803:       UE_scheduling_control->tpc0 = nr_limit_tpc(UE_scheduling_control->tpc0, rssi, rssi_threshold);
804: 
805:       if (timing_advance != 0xffff)
806:         UE_scheduling_control->ta_update = timing_advance;
807:       UE_scheduling_control->raw_rssi = rssi;
808:       UE_scheduling_control->pusch_snrx10 = ul_cqi * 5 - 640 - (txpower_calc * 10);
809: 
810:       if (UE_scheduling_control->tpc0 > 1)
811:         LOG_D(NR_MAC,
812:               "[UE %04x] %d.%d. PUSCH TPC %d and TA %d pusch_snrx10 %d rssi %d phrx_tx_power %d PHR (1PRB) %d mcs %d, nb_rb %d\n",
813:               UE->rnti,
814:               frameP,
815:               slotP,
816:               UE_scheduling_control->tpc0,
817:               UE_scheduling_control->ta_update,
818:               UE_scheduling_control->pusch_snrx10,
819:               UE_scheduling_control->raw_rssi,
820:               txpower_calc,
821:               UE_scheduling_control->ph,
822:               UE_scheduling_control->ul_harq_processes[harq_pid].sched_pusch.mcs,
823:               UE_scheduling_control->ul_harq_processes[harq_pid].sched_pusch.rbSize);
824: 
825:       NR_UE_ul_harq_t *cur_harq = &UE_scheduling_control->ul_harq_processes[harq_pid];
826:       if (cur_harq->round == 0)
827:        UE->mac_stats.pusch_snrx10 = UE_scheduling_control->pusch_snrx10;
828:       LOG_D(NR_MAC, "[UE %04x] PUSCH TPC %d and TA %d\n",UE->rnti,UE_scheduling_control->tpc0,UE_scheduling_control->ta_update);
829:     }
830:     else{
831:       LOG_D(NR_MAC,"[UE %04x] Detected DTX : increasing UE TX power\n",UE->rnti);
832:       UE_scheduling_control->tpc0 = 1;
833:     }
834: 
835: #if defined(ENABLE_MAC_PAYLOAD_DEBUG)
836: 
837:     LOG_I(NR_MAC, "Printing received UL MAC payload at gNB side: %d \n");
838:     for (uint32_t i = 0; i < sdu_lenP; i++) {
839:       // harq_process_ul_ue->a[i] = (unsigned char) rand();
840:       // printf("a[%d]=0x%02x\n",i,harq_process_ul_ue->a[i]);
841:       printf("%02x ", (unsigned char)sduP[i]);
842:     }
843:     printf("\n");
844: 
845: #endif
846: 
847:     if (sduP != NULL) {
848:       LOG_D(NR_MAC, "Received PDU at MAC gNB \n");
849: 
850:       UE->UE_sched_ctrl.pusch_consecutive_dtx_cnt = 0;
851:       UE_scheduling_control->sched_ul_bytes -= sdu_lenP;
852:       if (UE_scheduling_control->sched_ul_bytes < 0)
853:         UE_scheduling_control->sched_ul_bytes = 0;
854: 
855:       nr_process_mac_pdu(gnb_mod_idP, UE, CC_idP, frameP, slotP, sduP, sdu_lenP, harq_pid);
856:     }
857:     else {
858:       if (ul_cqi == 0xff || ul_cqi <= 128) {
859:         UE->UE_sched_ctrl.pusch_consecutive_dtx_cnt++;
860:         UE->mac_stats.ulsch_DTX++;
861:       }
862: 
863:       if (!get_softmodem_params()->phy_test && UE->UE_sched_ctrl.pusch_consecutive_dtx_cnt >= pusch_failure_thres) {
864:         LOG_W(NR_MAC,
865:               "UE %04x: Detected UL Failure on PUSCH after %d PUSCH DTX, stopping scheduling\n",
866:               UE->rnti,
867:               UE->UE_sched_ctrl.pusch_consecutive_dtx_cnt);
868:         nr_mac_trigger_ul_failure(&UE->UE_sched_ctrl, UE->current_UL_BWP.scs);
869:       }
870:     }
871:   } else if (sduP) {
872: 
873:     bool no_sig = true;
874:     for (uint32_t k = 0; k < sdu_lenP; k++) {
875:       if (sduP[k] != 0) {
876:         no_sig = false;
877:         break;
878:       }
879:     }
880: 
881:     T(T_GNB_MAC_UL_PDU_WITH_DATA, T_INT(gnb_mod_idP), T_INT(CC_idP),
882:       T_INT(rntiP), T_INT(frameP), T_INT(slotP), T_INT(-1) /* harq_pid */,
883:       T_BUFFER(sduP, sdu_lenP));
884:     
885:     /* we don't know this UE (yet). Check whether there is a ongoing RA (Msg 3)
886:      * and check the corresponding UE's RNTI match, in which case we activate
887:      * it. */
888:     for (int i = 0; i < NR_NB_RA_PROC_MAX; ++i) {
889:       NR_RA_t *ra = &gNB_mac->common_channels[CC_idP].ra[i];
890:       if (ra->ra_type == RA_4_STEP && ra->ra_state != nrRA_WAIT_Msg3)
891:         continue;
892: 
893:       if (no_sig) {
894:         LOG_W(NR_MAC, "Random Access %i ULSCH with no signal\n", i);
895:         handle_msg3_failed_rx(ra, i, gNB_mac->ul_bler.harq_round_max);
896:         continue;
897:       }
898:       if (ra->ra_type == RA_2_STEP) {
899:         // random access pusch with RA-RNTI
900:         if (ra->RA_rnti != current_rnti) {
901:           LOG_E(NR_MAC, "expected TC_RNTI %04x to match current RNTI %04x\n", ra->RA_rnti, current_rnti);
902:           continue;
903:         }
904:       } else {
905:         // random access pusch with TC-RNTI
906:         if (ra->rnti != current_rnti) {
907:           LOG_E(NR_MAC, "expected TC_RNTI %04x to match current RNTI %04x\n", ra->rnti, current_rnti);
908: 
909:           if ((frameP == ra->Msg3_frame) && (slotP == ra->Msg3_slot)) {
910:             LOG_W(NR_MAC,
911:                   "Random Access %i failed at state %s (TC_RNTI %04x RNTI %04x)\n",
912:                   i,
913:                   nrra_text[ra->ra_state],
914:                   ra->rnti,
915:                   current_rnti);
916:             nr_clear_ra_proc(ra);
917:           }
918: 
919:           continue;
920:         }
921:       }
922: 
923:       UE = UE ? UE : add_new_nr_ue(gNB_mac, ra->rnti, ra->CellGroup);
924:       if (!UE) {
925:         LOG_W(NR_MAC,
926:               "Random Access %i discarded at state %s (TC_RNTI %04x RNTI %04x): max number of users achieved!\n",
927:               i,
928:               nrra_text[ra->ra_state],
929:               ra->rnti,
930:               current_rnti);
931: 
932:         nr_clear_ra_proc(ra);
933:         return;
934:       }
935: 
936:       UE->UE_beam_index = ra->beam_id;
937: 
938:       // re-initialize ta update variables after RA procedure completion
939:       UE->UE_sched_ctrl.ta_frame = frameP;
940: 
941:       LOG_A(NR_MAC, "%4d.%2d PUSCH with TC_RNTI 0x%04x received correctly\n", frameP, slotP, current_rnti);
942: 
943:       NR_UE_sched_ctrl_t *UE_scheduling_control = &UE->UE_sched_ctrl;
944:       if (ul_cqi != 0xff) {
945:         UE_scheduling_control->tpc0 = nr_get_tpc(target_snrx10, ul_cqi, 30, UE_scheduling_control->sched_pusch.phr_txpower_calc);
946:         UE_scheduling_control->pusch_snrx10 = ul_cqi * 5 - 640 - UE_scheduling_control->sched_pusch.phr_txpower_calc * 10;
947:       }
948:       if (timing_advance != 0xffff)
949:         UE_scheduling_control->ta_update = timing_advance;
950:       UE_scheduling_control->raw_rssi = rssi;
951:       LOG_D(NR_MAC, "[UE %04x] PUSCH TPC %d and TA %d\n", UE->rnti, UE_scheduling_control->tpc0, UE_scheduling_control->ta_update);
952:       if (ra->cfra) {
953:         LOG_A(NR_MAC, "(rnti 0x%04x) CFRA procedure succeeded!\n", ra->rnti);
954:         nr_mac_reset_ul_failure(UE_scheduling_control);
955:         reset_dl_harq_list(UE_scheduling_control);
956:         reset_ul_harq_list(UE_scheduling_control);
957:         process_addmod_bearers_cellGroupConfig(&UE->UE_sched_ctrl, ra->CellGroup->rlc_BearerToAddModList);
958:         nr_clear_ra_proc(ra);
959:       } else {
960:         LOG_D(NR_MAC, "[RAPROC] Received %s:\n", ra->ra_type == RA_2_STEP ? "MsgA-PUSCH" : "Msg3");
961:         for (uint32_t k = 0; k < sdu_lenP; k++) {
962:           LOG_D(NR_MAC, "(%i): 0x%x\n", k, sduP[k]);
963:         }
964: 
965:         // 3GPP TS 38.321 Section 5.4.3 Multiplexing and assembly
966:         // Logical channels shall be prioritised in accordance with the following order (highest priority listed first):
967:         // - MAC CE for C-RNTI, or data from UL-CCCH;
968:         // This way, we need to process MAC CE for C-RNTI if RA is active and it is present in the MAC PDU
969:         // Search for MAC CE for C-RNTI
970:         rnti_t crnti = lcid_crnti_lookahead(sduP, sdu_lenP);
971:         if (crnti != 0) { // 3GPP TS 38.321 Table 7.1-1: RNTI values, RNTI 0x0000: N/A
972:           // this UE is the one identified by the RNTI in sduP
973:           ra->rnti = crnti;
974:           // Remove UE context just created after Msg.3 in some milliseconds as the UE is one already known (not now, as the UE
975:           // context is still needed for the moment)
976:           nr_mac_trigger_release_timer(&UE->UE_sched_ctrl, UE->current_UL_BWP.scs);
977: 
978:           // Replace the current UE by the UE identified by C-RNTI
979:           UE = find_nr_UE(&gNB_mac->UE_info, crnti);
980:           if (!UE) {
981:             // The UE identified by C-RNTI no longer exists at the gNB
982:             // Let's abort the current RA, so the UE will trigger a new RA later but using RRCSetupRequest instead. A better
983:             // solution may be implemented
984:             LOG_W(NR_MAC, "No UE found with C-RNTI %04x, ignoring Msg3 to have UE come back with new RA attempt\n", ra->rnti);
985:             mac_remove_nr_ue(gNB_mac, ra->rnti);
986:             nr_clear_ra_proc(ra);
987:             return;
988:           }
989: 
990:           // The UE identified by C-RNTI still exists at the gNB
991:           // Reset Msg4_ACKed to not schedule ULSCH and DLSCH before RRC Reconfiguration
992:           UE->Msg4_MsgB_ACKed = false;
993:           nr_mac_reset_ul_failure(&UE->UE_sched_ctrl);
994:           // Reset HARQ processes
995:           reset_dl_harq_list(&UE->UE_sched_ctrl);
996:           reset_ul_harq_list(&UE->UE_sched_ctrl);
997: 
998:           // Switch to BWP where RA is configured, typically in the InitialBWP
999:           // At this point, UE already switched and triggered RA in that BWP, need to do BWP switching also at gNB for C-RNTI
1000:           if (ra->DL_BWP.bwp_id != UE->current_DL_BWP.bwp_id || ra->UL_BWP.bwp_id != UE->current_UL_BWP.bwp_id) {
1001:             LOG_D(NR_MAC, "UE %04x Switch BWP from %ld to BWP id %ld\n", UE->rnti, UE->current_DL_BWP.bwp_id, ra->DL_BWP.bwp_id);
1002:             NR_ServingCellConfigCommon_t *scc = gNB_mac->common_channels[CC_idP].ServingCellConfigCommon;
1003:             configure_UE_BWP(gNB_mac, scc, &UE->UE_sched_ctrl, NULL, UE, ra->DL_BWP.bwp_id, ra->UL_BWP.bwp_id);
1004:           }
1005: 
1006:           if (UE->reconfigCellGroup) {
1007:             // Nothing to do
1008:             // A RRCReconfiguration message should be already pending (for example, an ongoing RRCReestablishment), and it will be
1009:             // transmitted in Msg4
1010:           } else {
1011:             // Trigger RRC Reconfiguration
1012:             LOG_I(NR_MAC, "Received UL_SCH_LCID_C_RNTI with C-RNTI 0x%04x, triggering RRC Reconfiguration\n", UE->rnti);
1013:             nr_mac_trigger_reconfiguration(gNB_mac, UE);
1014:           }
1015:         } else {
1016:           // UE Contention Resolution Identity
1017:           // Store the first 48 bits belonging to the uplink CCCH SDU within Msg3 to fill in Msg4
1018:           // First byte corresponds to R/LCID MAC sub-header
1019:           memcpy(ra->cont_res_id, &sduP[1], sizeof(uint8_t) * 6);
1020:         }
1021: 
1022:         // Decode MAC PDU for the correct UE, after checking for MAC CE for C-RNTI
1023:         // harq_pid set a non valid value because it is not used in this call
1024:         // the function is only called to decode the contention resolution sub-header
1025:         nr_process_mac_pdu(gnb_mod_idP, UE, CC_idP, frameP, slotP, sduP, sdu_lenP, -1);
1026: 
1027:         LOG_I(NR_MAC,
1028:               "Activating scheduling %s for TC_RNTI 0x%04x (state %s)\n",
1029:               ra->ra_type == RA_2_STEP ? "MsgB" : "Msg4",
1030:               ra->rnti,
1031:               nrra_text[ra->ra_state]);
1032:         ra->ra_state = ra->ra_type == RA_2_STEP ? nrRA_MsgB : nrRA_Msg4;
1033:         LOG_D(NR_MAC, "TC_RNTI 0x%04x next RA state %s\n", ra->rnti, nrra_text[ra->ra_state]);
1034:         return;
1035:       }
1036:     }
1037:   } else {
1038:     for (int i = 0; i < NR_NB_RA_PROC_MAX; ++i) {
1039:       NR_RA_t *ra = &gNB_mac->common_channels[CC_idP].ra[i];
1040:       if (ra->ra_state != nrRA_WAIT_Msg3)
1041:         continue;
1042: 
1043:       if((frameP!=ra->Msg3_frame) || (slotP!=ra->Msg3_slot))
1044:         continue;
1045: 
1046:       if (ul_cqi != 0xff)
1047:         ra->msg3_TPC = nr_get_tpc(target_snrx10, ul_cqi, 30, 0);
1048: 
1049:       handle_msg3_failed_rx(ra, i, gNB_mac->ul_bler.harq_round_max);
1050:     }
1051:   }
1052: }
1053: 
1054: void nr_rx_sdu(const module_id_t gnb_mod_idP,
1055:                const int CC_idP,
1056:                const frame_t frameP,
1057:                const sub_frame_t slotP,
1058:                const rnti_t rntiP,
1059:                uint8_t *sduP,
1060:                const uint32_t sdu_lenP,
1061:                const int8_t harq_pid,
1062:                const uint16_t timing_advance,
1063:                const uint8_t ul_cqi,
1064:                const uint16_t rssi)
1065: {
1066:   gNB_MAC_INST *gNB_mac = RC.nrmac[gnb_mod_idP];
1067:   NR_SCHED_LOCK(&gNB_mac->sched_lock);
1068:   _nr_rx_sdu(gnb_mod_idP, CC_idP, frameP, slotP, rntiP, sduP, sdu_lenP, harq_pid, timing_advance, ul_cqi, rssi);
1069:   NR_SCHED_UNLOCK(&gNB_mac->sched_lock);
1070: }
1071: 
1072: static uint32_t calc_power_complex(const int16_t *x, const int16_t *y, const uint32_t size)
1073: {
1074:   // Real part value
1075:   int64_t sum_x = 0;
1076:   int64_t sum_x2 = 0;
1077:   for(int k = 0; k<size; k++) {
1078:     sum_x = sum_x + x[k];
1079:     sum_x2 = sum_x2 + x[k]*x[k];
1080:   }
1081:   uint32_t power_re = sum_x2/size - (sum_x/size)*(sum_x/size);
1082: 
1083:   // Imaginary part power
1084:   int64_t sum_y = 0;
1085:   int64_t sum_y2 = 0;
1086:   for(int k = 0; k<size; k++) {
1087:     sum_y = sum_y + y[k];
1088:     sum_y2 = sum_y2 + y[k]*y[k];
1089:   }
1090:   uint32_t power_im = sum_y2/size - (sum_y/size)*(sum_y/size);
1091: 
1092:   return power_re+power_im;
1093: }
1094: 
1095: static c16_t nr_h_times_w(c16_t h, char w)
1096: {
1097:   c16_t output;
1098:     switch (w) {
1099:       case '0': // 0
1100:         output.r = 0;
1101:         output.i = 0;
1102:         break;
1103:       case '1': // 1
1104:         output.r = h.r;
1105:         output.i = h.i;
1106:         break;
1107:       case 'n': // -1
1108:         output.r = -h.r;
1109:         output.i = -h.i;
1110:         break;
1111:       case 'j': // j
1112:         output.r = -h.i;
1113:         output.i = h.r;
1114:         break;
1115:       case 'o': // -j
1116:         output.r = h.i;
1117:         output.i = -h.r;
1118:         break;
1119:       default:
1120:         AssertFatal(1==0,"Invalid precoder value %c\n", w);
1121:     }
1122:   return output;
1123: }
1124: 
1125: static uint8_t get_max_tpmi(const NR_PUSCH_Config_t *pusch_Config,
1126:                             const uint16_t num_ue_srs_ports,
1127:                             const uint8_t *nrOfLayers,
1128:                             int *additional_max_tpmi)
1129: {
1130:   uint8_t max_tpmi = 0;
1131: 
1132:   if (!pusch_Config
1133:       || (pusch_Config->txConfig != NULL && *pusch_Config->txConfig == NR_PUSCH_Config__txConfig_nonCodebook)
1134:       || num_ue_srs_ports == 1)
1135:     return max_tpmi;
1136: 
1137:   long max_rank = *pusch_Config->maxRank;
1138:   long *ul_FullPowerTransmission = pusch_Config->ext1 ? pusch_Config->ext1->ul_FullPowerTransmission_r16 : NULL;
1139:   long *codebookSubset = pusch_Config->codebookSubset;
1140: 
1141:   if (num_ue_srs_ports == 2) {
1142: 
1143:     if (max_rank == 1) {
1144:       if (ul_FullPowerTransmission && *ul_FullPowerTransmission == NR_PUSCH_Config__ext1__ul_FullPowerTransmission_r16_fullpowerMode1) {
1145:         max_tpmi = 2;
1146:       } else {
1147:         if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1148:           max_tpmi = 1;
1149:         } else {
1150:           max_tpmi = 5;
1151:         }
1152:       }
1153:     } else {
1154:       if (ul_FullPowerTransmission && *ul_FullPowerTransmission == NR_PUSCH_Config__ext1__ul_FullPowerTransmission_r16_fullpowerMode1) {
1155:         max_tpmi = *nrOfLayers == 1 ? 2 : 0;
1156:       } else {
1157:         if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1158:           max_tpmi = *nrOfLayers == 1 ? 1 : 0;
1159:         } else {
1160:           max_tpmi = *nrOfLayers == 1 ? 5 : 2;
1161:         }
1162:       }
1163:     }
1164: 
1165:   } else if (num_ue_srs_ports == 4) {
1166: 
1167:     if (max_rank == 1) {
1168:       if (ul_FullPowerTransmission && *ul_FullPowerTransmission == NR_PUSCH_Config__ext1__ul_FullPowerTransmission_r16_fullpowerMode1) {
1169:         if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1170:           max_tpmi = 3;
1171:           *additional_max_tpmi = 13;
1172:         } else {
1173:           max_tpmi = 15;
1174:         }
1175:       } else {
1176:         if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1177:           max_tpmi = 3;
1178:         } else if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_partialAndNonCoherent) {
1179:           max_tpmi = 11;
1180:         } else {
1181:           max_tpmi = 27;
1182:         }
1183:       }
1184:     } else {
1185:       if (ul_FullPowerTransmission && *ul_FullPowerTransmission == NR_PUSCH_Config__ext1__ul_FullPowerTransmission_r16_fullpowerMode1) {
1186:         if (max_rank == 2) {
1187:           if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1188:             max_tpmi = *nrOfLayers == 1 ? 3 : 6;
1189:             if (*nrOfLayers == 1) {
1190:               *additional_max_tpmi = 13;
1191:             }
1192:           } else {
1193:             max_tpmi = *nrOfLayers == 1 ? 15 : 13;
1194:           }
1195:         } else {
1196:           if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1197:             switch (*nrOfLayers) {
1198:               case 1:
1199:                 max_tpmi = 3;
1200:                 *additional_max_tpmi = 13;
1201:                 break;
1202:               case 2:
1203:                 max_tpmi = 6;
1204:                 break;
1205:               case 3:
1206:                 max_tpmi = 1;
1207:                 break;
1208:               case 4:
1209:                 max_tpmi = 0;
1210:                 break;
1211:               default:
1212:                 LOG_E(NR_MAC,"Number of layers %d is invalid!\n", *nrOfLayers);
1213:             }
1214:           } else {
1215:             switch (*nrOfLayers) {
1216:               case 1:
1217:                 max_tpmi = 15;
1218:                 break;
1219:               case 2:
1220:                 max_tpmi = 13;
1221:                 break;
1222:               case 3:
1223:               case 4:
1224:                 max_tpmi = 2;
1225:                 break;
1226:               default:
1227:                 LOG_E(NR_MAC,"Number of layers %d is invalid!\n", *nrOfLayers);
1228:             }
1229:           }
1230:         }
1231:       } else {
1232:         if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_nonCoherent) {
1233:           switch (*nrOfLayers) {
1234:             case 1:
1235:               max_tpmi = 3;
1236:               break;
1237:             case 2:
1238:               max_tpmi = 5;
1239:               break;
1240:             case 3:
1241:             case 4:
1242:               max_tpmi = 0;
1243:               break;
1244:             default:
1245:               LOG_E(NR_MAC,"Number of layers %d is invalid!\n", *nrOfLayers);
1246:           }
1247:         } else if (codebookSubset && *codebookSubset == NR_PUSCH_Config__codebookSubset_partialAndNonCoherent) {
1248:           switch (*nrOfLayers) {
1249:             case 1:
1250:               max_tpmi = 11;
1251:               break;
1252:             case 2:
1253:               max_tpmi = 13;
1254:               break;
1255:             case 3:
1256:             case 4:
1257:               max_tpmi = 2;
1258:               break;
1259:             default:
1260:               LOG_E(NR_MAC,"Number of layers %d is invalid!\n", *nrOfLayers);
1261:           }
1262:         } else {
1263:           switch (*nrOfLayers) {
1264:             case 1:
1265:               max_tpmi = 28;
1266:               break;
1267:             case 2:
1268:               max_tpmi = 22;
1269:               break;
1270:             case 3:
1271:               max_tpmi = 7;
1272:               break;
1273:             case 4:
1274:               max_tpmi = 5;
1275:               break;
1276:             default:
1277:               LOG_E(NR_MAC,"Number of layers %d is invalid!\n", *nrOfLayers);
1278:           }
1279:         }
1280:       }
1281:     }
1282: 
1283:   }
1284: 
1285:   return max_tpmi;
1286: }
1287: 
1288: static void get_precoder_matrix_coef(char *w,
1289:                                      const uint8_t ul_ri,
1290:                                      const uint16_t num_ue_srs_ports,
1291:                                      const long transform_precoding,
1292:                                      const uint8_t tpmi,
1293:                                      const uint8_t uI,
1294:                                      int layer_idx)
1295: {
1296:   if (ul_ri == 0) {
1297:     if (num_ue_srs_ports == 2) {
1298:       *w = table_38211_6_3_1_5_1[tpmi][uI][layer_idx];
1299:     } else {
1300:       if (transform_precoding == NR_PUSCH_Config__transformPrecoder_enabled) {
1301:         *w = table_38211_6_3_1_5_2[tpmi][uI][layer_idx];
1302:       } else {
1303:         *w = table_38211_6_3_1_5_3[tpmi][uI][layer_idx];
1304:       }
1305:     }
1306:   } else if (ul_ri == 1) {
1307:     if (num_ue_srs_ports == 2) {
1308:       *w = table_38211_6_3_1_5_4[tpmi][uI][layer_idx];
1309:     } else {
1310:       *w = table_38211_6_3_1_5_5[tpmi][uI][layer_idx];
1311:     }
1312:   } else {
1313:     AssertFatal(1 == 0, "Function get_precoder_matrix_coef() does not support %i layers yet!\n", ul_ri + 1);
1314:   }
1315: }
1316: 
1317: static int nr_srs_tpmi_estimation(const NR_PUSCH_Config_t *pusch_Config,
1318:                                   const long transform_precoding,
1319:                                   const uint8_t *channel_matrix,
1320:                                   const uint8_t normalized_iq_representation,
1321:                                   const uint16_t num_gnb_antenna_elements,
1322:                                   const uint16_t num_ue_srs_ports,
1323:                                   const uint16_t prg_size,
1324:                                   const uint16_t num_prgs,
1325:                                   const uint8_t ul_ri)
1326: {
1327:   if (ul_ri > 1) {
1328:     LOG_D(NR_MAC, "TPMI computation for ul_ri %i is not implemented yet!\n", ul_ri);
1329:     return 0;
1330:   }
1331: 
1332:   uint8_t tpmi_sel = 0;
1333:   const uint8_t nrOfLayers = ul_ri + 1;
1334:   int16_t precoded_channel_matrix_re[num_prgs * num_gnb_antenna_elements];
1335:   int16_t precoded_channel_matrix_im[num_prgs * num_gnb_antenna_elements];
1336:   c16_t *channel_matrix16 = (c16_t *)channel_matrix;
1337:   uint32_t max_precoded_signal_power = 0;
1338:   int additional_max_tpmi = -1;
1339:   char w;
1340: 
1341:   uint8_t max_tpmi = get_max_tpmi(pusch_Config, num_ue_srs_ports, &nrOfLayers, &additional_max_tpmi);
1342:   uint8_t end_tpmi_loop = additional_max_tpmi > max_tpmi ? additional_max_tpmi : max_tpmi;
1343: 
1344:   //                      channel_matrix                          x   precoder_matrix
1345:   // [ (gI=0,uI=0) (gI=0,uI=1) ... (gI=0,uI=num_ue_srs_ports-1) ] x   [uI=0]
1346:   // [ (gI=1,uI=0) (gI=1,uI=1) ... (gI=1,uI=num_ue_srs_ports-1) ]     [uI=1]
1347:   // [ (gI=2,uI=0) (gI=2,uI=1) ... (gI=2,uI=num_ue_srs_ports-1) ]     [uI=2]
1348:   //                           ...                                     ...
1349: 
1350:   for (uint8_t tpmi = 0; tpmi <= end_tpmi_loop && end_tpmi_loop > 0; tpmi++) {
1351:     if (tpmi > max_tpmi) {
1352:       tpmi = end_tpmi_loop;
1353:     }
1354: 
1355:     for (int pI = 0; pI < num_prgs; pI++) {
1356:       for (int gI = 0; gI < num_gnb_antenna_elements; gI++) {
1357:         uint16_t index_gI_pI = gI * num_prgs + pI;
1358:         precoded_channel_matrix_re[index_gI_pI] = 0;
1359:         precoded_channel_matrix_im[index_gI_pI] = 0;
1360: 
1361:         for (int uI = 0; uI < num_ue_srs_ports; uI++) {
1362:           for (int layer_idx = 0; layer_idx < nrOfLayers; layer_idx++) {
1363:             uint16_t index = uI * num_gnb_antenna_elements * num_prgs + index_gI_pI;
1364:             get_precoder_matrix_coef(&w, ul_ri, num_ue_srs_ports, transform_precoding, tpmi, uI, layer_idx);
1365:             c16_t h_times_w = nr_h_times_w(channel_matrix16[index], w);
1366: 
1367:             precoded_channel_matrix_re[index_gI_pI] += h_times_w.r;
1368:             precoded_channel_matrix_im[index_gI_pI] += h_times_w.i;
1369: 
1370: #ifdef SRS_IND_DEBUG
1371:             LOG_I(NR_MAC, "(pI %i, gI %i,  uI %i, layer_idx %i) w = %c, channel_matrix --> real %i, imag %i\n",
1372:                   pI, gI, uI, layer_idx, w, channel_matrix16[index].r, channel_matrix16[index].i);
1373: #endif
1374:           }
1375:         }
1376: 
1377: #ifdef SRS_IND_DEBUG
1378:         LOG_I(NR_MAC, "(pI %i, gI %i) precoded_channel_coef --> real %i, imag %i\n",
1379:               pI, gI, precoded_channel_matrix_re[index_gI_pI], precoded_channel_matrix_im[index_gI_pI]);
1380: #endif
1381:       }
1382:     }
1383: 
1384:     uint32_t precoded_signal_power = calc_power_complex(precoded_channel_matrix_re,
1385:                                                         precoded_channel_matrix_im,
1386:                                                         num_prgs * num_gnb_antenna_elements);
1387: 
1388: #ifdef SRS_IND_DEBUG

(Output capped at 50 KB. Showing lines 1-1388. Use offset=1389 to continue.)
</content>
```

---

## Assistant (Plan · glm-5 · 44.0s)

_Thinking:_

让我继续读取文件的剩余部分，看看是否有手动替换 RB 遍历的代码。

**Tool: grep**

**Input:**
```json
{
  "pattern": "rb.*replace|replace.*rb|手动|遍历.*RB|RB.*遍历|traverse|manual",
  "path": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB"
}
```

**Output:**
```
No files found
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 1389
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
1389:     LOG_I(NR_MAC, "(tpmi %i) precoded_signal_power = %i\n", tpmi, precoded_signal_power);
1390: #endif
1391: 
1392:     if (precoded_signal_power > max_precoded_signal_power) {
1393:       max_precoded_signal_power = precoded_signal_power;
1394:       tpmi_sel = tpmi;
1395:     }
1396:   }
1397: 
1398:   return tpmi_sel;
1399: }
1400: 
1401: void handle_nr_srs_measurements(const module_id_t module_id,
1402:                                 const frame_t frame,
1403:                                 const sub_frame_t slot,
1404:                                 nfapi_nr_srs_indication_pdu_t *srs_ind)
1405: {
1406:   gNB_MAC_INST *nrmac = RC.nrmac[module_id];
1407:   NR_SCHED_LOCK(&nrmac->sched_lock);
1408:   LOG_D(NR_MAC, "(%d.%d) Received SRS indication for UE %04x\n", frame, slot, srs_ind->rnti);
1409: 
1410: #ifdef SRS_IND_DEBUG
1411:   LOG_I(NR_MAC, "frame = %i\n", frame);
1412:   LOG_I(NR_MAC, "slot = %i\n", slot);
1413:   LOG_I(NR_MAC, "srs_ind->rnti = %04x\n", srs_ind->rnti);
1414:   LOG_I(NR_MAC, "srs_ind->timing_advance_offset = %i\n", srs_ind->timing_advance_offset);
1415:   LOG_I(NR_MAC, "srs_ind->timing_advance_offset_nsec = %i\n", srs_ind->timing_advance_offset_nsec);
1416:   LOG_I(NR_MAC, "srs_ind->srs_usage = %i\n", srs_ind->srs_usage);
1417:   LOG_I(NR_MAC, "srs_ind->report_type = %i\n", srs_ind->report_type);
1418: #endif
1419: 
1420:   NR_UE_info_t *UE = find_nr_UE(&RC.nrmac[module_id]->UE_info, srs_ind->rnti);
1421:   if (!UE) {
1422:     LOG_W(NR_MAC, "Could not find UE for RNTI %04x\n", srs_ind->rnti);
1423:     NR_SCHED_UNLOCK(&nrmac->sched_lock);
1424:     return;
1425:   }
1426: 
1427:   if (srs_ind->timing_advance_offset == 0xFFFF) {
1428:     LOG_W(NR_MAC, "Invalid timing advance offset for RNTI %04x\n", srs_ind->rnti);
1429:     NR_SCHED_UNLOCK(&nrmac->sched_lock);
1430:     return;
1431:   }
1432: 
1433:   gNB_MAC_INST *nr_mac = RC.nrmac[module_id];
1434:   NR_mac_stats_t *stats = &UE->mac_stats;
1435:   nfapi_srs_report_tlv_t *report_tlv = &srs_ind->report_tlv;
1436: 
1437:   switch (srs_ind->srs_usage) {
1438:     case NR_SRS_ResourceSet__usage_beamManagement: {
1439:       nfapi_nr_srs_beamforming_report_t nr_srs_bf_report;
1440:       unpack_nr_srs_beamforming_report(report_tlv->value,
1441:                                        report_tlv->length,
1442:                                        &nr_srs_bf_report,
1443:                                        sizeof(nfapi_nr_srs_beamforming_report_t));
1444: 
1445:       if (nr_srs_bf_report.wide_band_snr == 0xFF) {
1446:         LOG_W(NR_MAC, "Invalid wide_band_snr for RNTI %04x\n", srs_ind->rnti);
1447:         NR_SCHED_UNLOCK(&nrmac->sched_lock);
1448:         return;
1449:       }
1450: 
1451:       int wide_band_snr_dB = (nr_srs_bf_report.wide_band_snr >> 1) - 64;
1452: 
1453: #ifdef SRS_IND_DEBUG
1454:       LOG_I(NR_MAC, "nr_srs_bf_report.prg_size = %i\n", nr_srs_bf_report.prg_size);
1455:       LOG_I(NR_MAC, "nr_srs_bf_report.num_symbols = %i\n", nr_srs_bf_report.num_symbols);
1456:       LOG_I(NR_MAC, "nr_srs_bf_report.wide_band_snr = %i (%i dB)\n", nr_srs_bf_report.wide_band_snr, wide_band_snr_dB);
1457:       LOG_I(NR_MAC, "nr_srs_bf_report.num_reported_symbols = %i\n", nr_srs_bf_report.num_reported_symbols);
1458:       LOG_I(NR_MAC, "nr_srs_bf_report.prgs[0].num_prgs = %i\n", nr_srs_bf_report.prgs[0].num_prgs);
1459:       for (int prg_idx = 0; prg_idx < nr_srs_bf_report.prgs[0].num_prgs; prg_idx++) {
1460:         LOG_I(NR_MAC,
1461:               "nr_srs_bf_report.prgs[0].prg_list[%3i].rb_snr = %i (%i dB)\n",
1462:               prg_idx,
1463:               nr_srs_bf_report.prgs[0].prg_list[prg_idx].rb_snr,
1464:               (nr_srs_bf_report.prgs[0].prg_list[prg_idx].rb_snr >> 1) - 64);
1465:       }
1466: #endif
1467: 
1468:       sprintf(stats->srs_stats, "UL-SNR %i dB", wide_band_snr_dB);
1469: 
1470:       const int ul_prbblack_SNR_threshold = nr_mac->ul_prbblack_SNR_threshold;
1471:       uint16_t *ulprbbl = nr_mac->ulprbbl;
1472: 
1473:       uint16_t num_rbs = nr_srs_bf_report.prg_size * nr_srs_bf_report.reported_symbol_list[0].num_prgs;
1474:       memset(ulprbbl, 0, num_rbs * sizeof(uint16_t));
1475:       for (int rb = 0; rb < num_rbs; rb++) {
1476:         int snr = (nr_srs_bf_report.reported_symbol_list[0].prg_list[rb / nr_srs_bf_report.prg_size].rb_snr >> 1) - 64;
1477:         if (snr < wide_band_snr_dB - ul_prbblack_SNR_threshold) {
1478:           ulprbbl[rb] = 0x3FFF; // all symbols taken
1479:         }
1480:         LOG_D(NR_MAC, "ulprbbl[%3i] = 0x%x\n", rb, ulprbbl[rb]);
1481:       }
1482: 
1483:       break;
1484:     }
1485: 
1486:     case NR_SRS_ResourceSet__usage_codebook: {
1487:       nfapi_nr_srs_normalized_channel_iq_matrix_t nr_srs_channel_iq_matrix;
1488:       unpack_nr_srs_normalized_channel_iq_matrix(report_tlv->value,
1489:                                                  report_tlv->length,
1490:                                                  &nr_srs_channel_iq_matrix,
1491:                                                  sizeof(nfapi_nr_srs_normalized_channel_iq_matrix_t));
1492: 
1493: #ifdef SRS_IND_DEBUG
1494:       LOG_I(NR_MAC, "nr_srs_channel_iq_matrix.normalized_iq_representation = %i\n", nr_srs_channel_iq_matrix.normalized_iq_representation);
1495:       LOG_I(NR_MAC, "nr_srs_channel_iq_matrix.num_gnb_antenna_elements = %i\n", nr_srs_channel_iq_matrix.num_gnb_antenna_elements);
1496:       LOG_I(NR_MAC, "nr_srs_channel_iq_matrix.num_ue_srs_ports = %i\n", nr_srs_channel_iq_matrix.num_ue_srs_ports);
1497:       LOG_I(NR_MAC, "nr_srs_channel_iq_matrix.prg_size = %i\n", nr_srs_channel_iq_matrix.prg_size);
1498:       LOG_I(NR_MAC, "nr_srs_channel_iq_matrix.num_prgs = %i\n", nr_srs_channel_iq_matrix.num_prgs);
1499:       c16_t *channel_matrix16 = (c16_t *)nr_srs_channel_iq_matrix.channel_matrix;
1500:       c8_t *channel_matrix8 = (c8_t *)nr_srs_channel_iq_matrix.channel_matrix;
1501:       for (int uI = 0; uI < nr_srs_channel_iq_matrix.num_ue_srs_ports; uI++) {
1502:         for (int gI = 0; gI < nr_srs_channel_iq_matrix.num_gnb_antenna_elements; gI++) {
1503:           for (int pI = 0; pI < nr_srs_channel_iq_matrix.num_prgs; pI++) {
1504:             uint16_t index = uI * nr_srs_channel_iq_matrix.num_gnb_antenna_elements * nr_srs_channel_iq_matrix.num_prgs + gI * nr_srs_channel_iq_matrix.num_prgs + pI;
1505:             LOG_I(NR_MAC,
1506:                   "(uI %i, gI %i, pI %i) channel_matrix --> real %i, imag %i\n",
1507:                   uI,
1508:                   gI,
1509:                   pI,
1510:                   nr_srs_channel_iq_matrix.normalized_iq_representation == 0 ? channel_matrix8[index].r : channel_matrix16[index].r,
1511:                   nr_srs_channel_iq_matrix.normalized_iq_representation == 0 ? channel_matrix8[index].i : channel_matrix16[index].i);
1512:           }
1513:         }
1514:       }
1515: #endif
1516: 
1517:       NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
1518:       NR_UE_UL_BWP_t *current_BWP = &UE->current_UL_BWP;
1519:       sched_ctrl->srs_feedback.sri = NR_SRS_SRI_0;
1520: 
1521:       start_meas(&nr_mac->nr_srs_ri_computation_timer);
1522:       nr_srs_ri_computation(&nr_srs_channel_iq_matrix, current_BWP, &sched_ctrl->srs_feedback.ul_ri);
1523:       stop_meas(&nr_mac->nr_srs_ri_computation_timer);
1524: 
1525:       start_meas(&nr_mac->nr_srs_tpmi_computation_timer);
1526:       sched_ctrl->srs_feedback.tpmi = nr_srs_tpmi_estimation(current_BWP->pusch_Config,
1527:                                                              current_BWP->transform_precoding,
1528:                                                              nr_srs_channel_iq_matrix.channel_matrix,
1529:                                                              nr_srs_channel_iq_matrix.normalized_iq_representation,
1530:                                                              nr_srs_channel_iq_matrix.num_gnb_antenna_elements,
1531:                                                              nr_srs_channel_iq_matrix.num_ue_srs_ports,
1532:                                                              nr_srs_channel_iq_matrix.prg_size,
1533:                                                              nr_srs_channel_iq_matrix.num_prgs,
1534:                                                              sched_ctrl->srs_feedback.ul_ri);
1535:       stop_meas(&nr_mac->nr_srs_tpmi_computation_timer);
1536: 
1537:       sprintf(stats->srs_stats, "UL-RI %d, TPMI %d", sched_ctrl->srs_feedback.ul_ri + 1, sched_ctrl->srs_feedback.tpmi);
1538: 
1539:       break;
1540:     }
1541: 
1542:     case NR_SRS_ResourceSet__usage_nonCodebook:
1543:     case NR_SRS_ResourceSet__usage_antennaSwitching:
1544:       LOG_W(NR_MAC, "MAC procedures for this SRS usage are not implemented yet!\n");
1545:       break;
1546: 
1547:     default:
1548:       AssertFatal(1 == 0, "Invalid SRS usage\n");
1549:   }
1550:   NR_SCHED_UNLOCK(&nrmac->sched_lock);
1551: }
1552: 
1553: long get_K2(NR_PUSCH_TimeDomainResourceAllocationList_t *tdaList,
1554:             int time_domain_assignment,
1555:             int mu,
1556:             const NR_ServingCellConfigCommon_t *scc)
1557: {
1558:   /* we assume that this function is mutex-protected from outside */
1559:   NR_PUSCH_TimeDomainResourceAllocation_t *tda = tdaList->list.array[time_domain_assignment];
1560:   const int NTN_gNB_Koffset = get_NTN_Koffset(scc);
1561: 
1562:   if (tda->k2)
1563:     return *tda->k2 + NTN_gNB_Koffset;
1564:   else if (mu < 2)
1565:     return 1 + NTN_gNB_Koffset;
1566:   else if (mu == 2)
1567:     return 2 + NTN_gNB_Koffset;
1568:   else
1569:     return 3 + NTN_gNB_Koffset;
1570: }
1571: 
1572: static bool nr_UE_is_to_be_scheduled(const frame_structure_t *fs,
1573:                                      NR_UE_info_t *UE,
1574:                                      frame_t frame,
1575:                                      sub_frame_t slot,
1576:                                      uint32_t ulsch_max_frame_inactivity)
1577: {
1578:   const int n = fs->numb_slots_frame;
1579:   const int now = frame * n + slot;
1580: 
1581:   const NR_UE_sched_ctrl_t *sched_ctrl =&UE->UE_sched_ctrl;
1582:   /**
1583:    * Force the default transmission in a full slot as early
1584:    * as possible in the UL portion of TDD period (last_ul_slot) */
1585:   int num_slots_per_period = fs->numb_slots_period;
1586:   int last_ul_slot = fs->frame_type == TDD ? get_first_ul_slot(fs, false) : sched_ctrl->last_ul_slot;
1587:   const int last_ul_sched = sched_ctrl->last_ul_frame * n + last_ul_slot;
1588:   const int diff = (now - last_ul_sched + 1024 * n) % (1024 * n);
1589:   /* UE is to be scheduled if
1590:    * (1) we think the UE has more bytes awaiting than what we scheduled
1591:    * (2) there is a scheduling request
1592:    * (3) or we did not schedule it in more than 10 frames */
1593:   const bool has_data = sched_ctrl->estimated_ul_buffer > sched_ctrl->sched_ul_bytes;
1594:   const bool high_inactivity = diff >= (ulsch_max_frame_inactivity > 0 ? ulsch_max_frame_inactivity * n : num_slots_per_period);
1595:   LOG_D(NR_MAC,
1596:         "%4d.%2d UL inactivity %d slots has_data %d SR %d\n",
1597:         frame,
1598:         slot,
1599:         diff,
1600:         has_data,
1601:         sched_ctrl->SR);
1602:   return has_data || sched_ctrl->SR || high_inactivity;
1603: }
1604: 
1605: static void update_ul_ue_R_Qm(int mcs, int mcs_table, const NR_PUSCH_Config_t *pusch_Config, uint16_t *R, uint8_t *Qm)
1606: {
1607:   *R = nr_get_code_rate_ul(mcs, mcs_table);
1608:   *Qm = nr_get_Qm_ul(mcs, mcs_table);
1609: 
1610:   if (pusch_Config && pusch_Config->tp_pi2BPSK && ((mcs_table == 3 && mcs < 2) || (mcs_table == 4 && mcs < 6))) {
1611:     *R >>= 1;
1612:     *Qm <<= 1;
1613:   }
1614: }
1615: 
1616: static void nr_ue_max_mcs_min_rb(int mu,
1617:                                  int ph_limit,
1618:                                  NR_sched_pusch_t *sched_pusch,
1619:                                  NR_UE_UL_BWP_t *ul_bwp,
1620:                                  uint16_t minRb,
1621:                                  uint32_t tbs,
1622:                                  uint16_t *Rb,
1623:                                  uint8_t *mcs)
1624: {
1625:   AssertFatal(*Rb >= minRb, "illegal Rb %d < minRb %d\n", *Rb, minRb);
1626:   AssertFatal(*mcs >= 0 && *mcs <= 28, "illegal MCS %d\n", *mcs);
1627: 
1628:   int tbs_bits = tbs << 3;
1629:   uint16_t R;
1630:   uint8_t Qm;
1631:   update_ul_ue_R_Qm(*mcs, ul_bwp->mcs_table, ul_bwp->pusch_Config, &R, &Qm);
1632: 
1633:   long *deltaMCS = ul_bwp->pusch_Config ? ul_bwp->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
1634:   tbs_bits = nr_compute_tbs(Qm, R, *Rb,
1635:                               sched_pusch->tda_info.nrOfSymbols,
1636:                               sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1637:                               0, // nb_rb_oh
1638:                               0,
1639:                               sched_pusch->nrOfLayers);
1640: 
1641:   int tx_power = compute_ph_factor(mu,
1642:                                    tbs_bits,
1643:                                    *Rb,
1644:                                    sched_pusch->nrOfLayers,
1645:                                    sched_pusch->tda_info.nrOfSymbols,
1646:                                    sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1647:                                    deltaMCS,
1648:                                    true);
1649: 
1650:   while (ph_limit < tx_power && *Rb > minRb) {
1651:     (*Rb)--;
1652:     tbs_bits = nr_compute_tbs(Qm, R, *Rb,
1653:                               sched_pusch->tda_info.nrOfSymbols,
1654:                               sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1655:                               0, // nb_rb_oh
1656:                               0,
1657:                               sched_pusch->nrOfLayers);
1658:     tx_power = compute_ph_factor(mu,
1659:                                  tbs_bits,
1660:                                  *Rb,
1661:                                  sched_pusch->nrOfLayers,
1662:                                  sched_pusch->tda_info.nrOfSymbols,
1663:                                  sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1664:                                  deltaMCS,
1665:                                  true);
1666:     LOG_D(NR_MAC, "Checking %d RBs, MCS %d, ph_limit %d, tx_power %d\n",*Rb,*mcs,ph_limit,tx_power);
1667:   }
1668: 
1669:   while (ph_limit < tx_power && *mcs > 0) {
1670:     (*mcs)--;
1671:     update_ul_ue_R_Qm(*mcs, ul_bwp->mcs_table, ul_bwp->pusch_Config, &R, &Qm);
1672:     tbs_bits = nr_compute_tbs(Qm, R, *Rb,
1673:                               sched_pusch->tda_info.nrOfSymbols,
1674:                               sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1675:                               0, // nb_rb_oh
1676:                               0,
1677:                               sched_pusch->nrOfLayers);
1678:     tx_power = compute_ph_factor(mu,
1679:                                  tbs_bits,
1680:                                  *Rb,
1681:                                  sched_pusch->nrOfLayers,
1682:                                  sched_pusch->tda_info.nrOfSymbols,
1683:                                  sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
1684:                                  deltaMCS,
1685:                                  true);
1686:     LOG_D(NR_MAC, "Checking %d RBs, MCS %d, ph_limit %d, tx_power %d\n",*Rb,*mcs,ph_limit,tx_power);
1687:   }
1688: 
1689:   if (ph_limit < tx_power)
1690:     LOG_D(NR_MAC, "Normalized power %d based on current resources (RBs %d, MCS %d) exceed reported PHR %d (normalized value)\n",
1691:           tx_power, *Rb, *mcs, ph_limit);
1692: }
1693: 
1694: static bool allocate_ul_retransmission(gNB_MAC_INST *nrmac,
1695: 				       frame_t frame,
1696: 				       sub_frame_t slot,
1697: 				       uint16_t *rballoc_mask,
1698: 				       int *n_rb_sched,
1699: 				       int dci_beam_idx,
1700: 				       NR_UE_info_t* UE,
1701: 				       int harq_pid,
1702: 				       const NR_ServingCellConfigCommon_t *scc,
1703: 				       const int tda)
1704: {
1705:   const int CC_id = 0;
1706:   NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
1707:   NR_sched_pusch_t *retInfo = &sched_ctrl->ul_harq_processes[harq_pid].sched_pusch;
1708:   NR_UE_UL_BWP_t *ul_bwp = &UE->current_UL_BWP;
1709: 
1710:   int rbStart = 0; // wrt BWP start
1711:   const uint32_t bwpSize = ul_bwp->BWPSize;
1712:   const uint32_t bwpStart = ul_bwp->BWPStart;
1713:   const uint8_t nrOfLayers = retInfo->nrOfLayers;
1714:   LOG_D(NR_MAC,"retInfo->time_domain_allocation = %d, tda = %d\n", retInfo->time_domain_allocation, tda);
1715:   LOG_D(NR_MAC,"tbs %d\n",retInfo->tb_size);
1716:   NR_tda_info_t tda_info = get_ul_tda_info(ul_bwp,
1717:                                            sched_ctrl->coreset->controlResourceSetId,
1718:                                            sched_ctrl->search_space->searchSpaceType->present,
1719:                                            TYPE_C_RNTI_,
1720:                                            tda);
1721:   if (!tda_info.valid_tda)
1722:     return false;
1723: 
1724:   bool reuse_old_tda = (retInfo->tda_info.startSymbolIndex == tda_info.startSymbolIndex) && (retInfo->tda_info.nrOfSymbols <= tda_info.nrOfSymbols);
1725:   if (reuse_old_tda && nrOfLayers == retInfo->nrOfLayers) {
1726:     /* Check the resource is enough for retransmission */
1727:     const uint16_t slbitmap = SL_to_bitmap(retInfo->tda_info.startSymbolIndex, retInfo->tda_info.nrOfSymbols);
1728:     while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
1729:       rbStart++;
1730:     if (rbStart + retInfo->rbSize > bwpSize) {
1731:       LOG_W(NR_MAC, "[UE %04x][%4d.%2d] could not allocate UL retransmission: no resources (rbStart %d, retInfo->rbSize %d, bwpSize %d) \n",
1732:             UE->rnti,
1733:             frame,
1734:             slot,
1735:             rbStart,
1736:             retInfo->rbSize,
1737:             bwpSize);
1738:       return false;
1739:     }
1740:     LOG_D(NR_MAC, "Retransmission keeping TDA %d and TBS %d\n", tda, retInfo->tb_size);
1741:   } 
1742:   else {
1743:     NR_pusch_dmrs_t dmrs_info = get_ul_dmrs_params(scc, ul_bwp, &tda_info, nrOfLayers);
1744:     /* the retransmission will use a different time domain allocation, check
1745:      * that we have enough resources */
1746:     const uint16_t slbitmap = SL_to_bitmap(tda_info.startSymbolIndex, tda_info.nrOfSymbols);
1747:     while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
1748:       rbStart++;
1749:     int rbSize = 0;
1750:     while (rbStart + rbSize < bwpSize && !(rballoc_mask[rbStart + bwpStart + rbSize] & slbitmap))
1751:       rbSize++;
1752:     uint32_t new_tbs;
1753:     uint16_t new_rbSize;
1754:     bool success = nr_find_nb_rb(retInfo->Qm,
1755:                                  retInfo->R,
1756:                                  UE->current_UL_BWP.transform_precoding,
1757:                                  nrOfLayers,
1758:                                  tda_info.nrOfSymbols,
1759:                                  dmrs_info.N_PRB_DMRS * dmrs_info.num_dmrs_symb,
1760:                                  retInfo->tb_size,
1761:                                  1, /* minimum of 1RB: need to find exact TBS, don't preclude any number */
1762:                                  rbSize,
1763:                                  &new_tbs,
1764:                                  &new_rbSize);
1765:     if (!success || new_tbs != retInfo->tb_size) {
1766:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] allocation of UL retransmission failed: new TBsize %d of new TDA does not match old TBS %d \n",
1767:             UE->rnti,
1768:             frame,
1769:             slot,
1770:             new_tbs,
1771:             retInfo->tb_size);
1772:       return false; /* the maximum TBsize we might have is smaller than what we need */
1773:     }
1774:     LOG_D(NR_MAC, "Retransmission with TDA %d->%d and TBS %d -> %d\n", retInfo->time_domain_allocation, tda, retInfo->tb_size, new_tbs);
1775:     /* we can allocate it. Overwrite the time_domain_allocation, the number
1776:      * of RBs, and the new TB size. The rest is done below */
1777:     retInfo->tb_size = new_tbs;
1778:     retInfo->rbSize = new_rbSize;
1779:     retInfo->time_domain_allocation = tda;
1780:     retInfo->dmrs_info = dmrs_info;
1781:     retInfo->tda_info = tda_info;
1782:   }
1783: 
1784:   /* Find a free CCE */
1785:   int CCEIndex = get_cce_index(nrmac,
1786:                                CC_id,
1787:                                slot,
1788:                                UE->rnti,
1789:                                &sched_ctrl->aggregation_level,
1790:                                dci_beam_idx,
1791:                                sched_ctrl->search_space,
1792:                                sched_ctrl->coreset,
1793:                                &sched_ctrl->sched_pdcch,
1794:                                false,
1795:                                sched_ctrl->pdcch_cl_adjust);
1796:   if (CCEIndex<0) {
1797:     LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for retransmission UL DCI UE\n", UE->rnti, frame, slot);
1798:     return false;
1799:   }
1800: 
1801:   sched_ctrl->cce_index = CCEIndex;
1802:   fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam_idx);
1803:   int slots_frame = nrmac->frame_structure.numb_slots_frame;
1804:   retInfo->frame = (frame + (slot + tda_info.k2) / slots_frame) % MAX_FRAME_NUMBER;
1805:   retInfo->slot = (slot + tda_info.k2) % slots_frame;
1806:   /* Get previous PSUCH field info */
1807:   sched_ctrl->sched_pusch = *retInfo;
1808:   NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
1809: 
1810:   LOG_W(NR_MAC,
1811:         "%4d.%2d Allocate UL retransmission RNTI %04x sched %4d.%2d (%d RBs)\n",
1812:         frame,
1813:         slot,
1814:         UE->rnti,
1815:         sched_pusch->frame,
1816:         sched_pusch->slot,
1817:         sched_pusch->rbSize);
1818: 
1819:   sched_pusch->rbStart = rbStart;
1820:   /* no need to recompute the TBS, it will be the same */
1821: 
1822:   /* Mark the corresponding RBs as used */
1823:   n_rb_sched -= sched_pusch->rbSize;
1824:   for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
1825:     rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= SL_to_bitmap(sched_pusch->tda_info.startSymbolIndex, sched_pusch->tda_info.nrOfSymbols);
1826:   return true;
1827: }
1828: 
1829: static uint32_t ul_pf_tbs[5][29]; // pre-computed, approximate TBS values for PF coefficient
1830: typedef struct UEsched_s {
1831:   float coef;
1832:   NR_UE_info_t * UE;
1833: } UEsched_t;
1834: 
1835: static int comparator(const void *p, const void *q) {
1836:   return ((UEsched_t*)p)->coef < ((UEsched_t*)q)->coef;
1837: }
1838: 
1839: static void pf_ul(module_id_t module_id,
1840:                   frame_t frame,
1841:                   int slot,
1842:                   frame_t sched_frame,
1843:                   int sched_slot,
1844:                   NR_UE_info_t *UE_list[],
1845:                   int max_num_ue,
1846:                   int num_beams,
1847:                   int n_rb_sched[num_beams])
1848: {
1849:   const int CC_id = 0;
1850:   gNB_MAC_INST *nrmac = RC.nrmac[module_id];
1851:   NR_ServingCellConfigCommon_t *scc = nrmac->common_channels[CC_id].ServingCellConfigCommon;
1852:   int slots_per_frame = nrmac->frame_structure.numb_slots_frame;
1853:   const int min_rb = nrmac->min_grant_prb;
1854:   // min_rb = 5
1855:   // LOG_W(PHY,"min_rb = %d",min_rb);
1856:   // UEs that could be scheduled
1857:   UEsched_t UE_sched[MAX_MOBILES_PER_GNB + 1] = {0};
1858:   int remainUEs[num_beams];
1859:   for (int i = 0; i < num_beams; i++)
1860:     remainUEs[i] = max_num_ue;
1861:   int curUE = 0;
1862: 
1863:   /* Loop UE_list to calculate throughput and coeff */
1864:   UE_iterator(UE_list, UE) {
1865: 
1866:     NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
1867:     if (!UE->Msg4_MsgB_ACKed || sched_ctrl->ul_failure)
1868:       continue;
1869: 
1870:     LOG_D(NR_MAC,"pf_ul: preparing UL scheduling for UE %04x\n",UE->rnti);
1871:     NR_UE_UL_BWP_t *current_BWP = &UE->current_UL_BWP;
1872: 
1873:     NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
1874:     const NR_mac_dir_stats_t *stats = &UE->mac_stats.ul;
1875: 
1876:     /* Calculate throughput */
1877:     const float a = 0.01f;
1878:     const uint32_t b = stats->current_bytes;
1879:     UE->ul_thr_ue = (1 - a) * UE->ul_thr_ue + a * b;
1880: 
1881:     int total_rem_ues = 0;
1882:     for (int i = 0; i < num_beams; i++)
1883:       total_rem_ues += remainUEs[i];
1884:     if (total_rem_ues == 0)
1885:       continue;
1886: 
1887:     NR_beam_alloc_t dci_beam = beam_allocation_procedure(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame);
1888:     if (dci_beam.idx < 0) {
1889:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", UE->rnti, frame, slot);
1890:       continue;
1891:     }
1892: 
1893:     NR_beam_alloc_t beam = beam_allocation_procedure(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame);
1894:     if (beam.idx < 0) {
1895:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", UE->rnti, frame, slot);
1896:       reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1897:       continue;
1898:     }
1899:     const int index = ul_buffer_index(sched_frame, sched_slot, slots_per_frame, nrmac->vrb_map_UL_size);
1900:     uint16_t *rballoc_mask = &nrmac->common_channels[CC_id].vrb_map_UL[beam.idx][index * MAX_BWP_SIZE];
1901: 
1902:     /* Check if retransmission is necessary */
1903:     sched_pusch->ul_harq_pid = sched_ctrl->retrans_ul_harq.head;
1904:     LOG_D(NR_MAC,"pf_ul: UE %04x harq_pid %d\n", UE->rnti, sched_pusch->ul_harq_pid);
1905:     if (sched_pusch->ul_harq_pid >= 0) {
1906:       /* Allocate retransmission*/
1907:       const int tda = get_ul_tda(nrmac, sched_frame, sched_slot);
1908:       bool r = allocate_ul_retransmission(nrmac,
1909:                                           frame,
1910:                                           slot,
1911:                                           rballoc_mask,
1912:                                           &n_rb_sched[beam.idx],
1913:                                           dci_beam.idx,
1914:                                           UE,
1915:                                           sched_pusch->ul_harq_pid,
1916:                                           scc,
1917:                                           tda);
1918:       if (!r) {
1919:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] UL retransmission could not be allocated\n", UE->rnti, frame, slot);
1920:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1921:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1922:         continue;
1923:       }
1924:       else
1925:         LOG_D(NR_MAC,"%4d.%2d UL Retransmission UE RNTI %04x to be allocated, max_num_ue %d\n", frame, slot, UE->rnti,max_num_ue);
1926: 
1927:       /* reduce max_num_ue once we are sure UE can be allocated, i.e., has CCE */
1928:       remainUEs[beam.idx]--;
1929:       continue;
1930:     }
1931: 
1932:     /* skip this UE if there are no free HARQ processes. This can happen e.g.
1933:      * if the UE disconnected in L2sim, in which case the gNB is not notified
1934:      * (this can be considered a design flaw) */
1935:     if (sched_ctrl->available_ul_harq.head < 0) {
1936:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1937:       reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1938:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] has no free UL HARQ process, skipping\n", UE->rnti, frame, slot);
1939:       continue;
1940:     }
1941: 
1942:     const int B = max(0, sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes);
1943:     /* preprocessor computed sched_frame/sched_slot */
1944:     const bool do_sched = nr_UE_is_to_be_scheduled(&nrmac->frame_structure,
1945:                                                    UE,
1946:                                                    sched_frame,
1947:                                                    sched_slot,
1948:                                                    nrmac->ulsch_max_frame_inactivity);
1949: 
1950:     LOG_D(NR_MAC,"pf_ul: do_sched UE %04x => %s\n", UE->rnti, do_sched ? "yes" : "no");
1951:     if ((B == 0 && !do_sched) || nr_timer_is_active(&sched_ctrl->transm_interrupt)) {
1952:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1953:       reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1954:       continue;
1955:     }
1956: 
1957:     const NR_bler_options_t *bo = &nrmac->ul_bler;
1958:     const int max_mcs_table = (current_BWP->mcs_table == 0 || current_BWP->mcs_table == 2) ? 28 : 27;
1959:     const int max_mcs = min(bo->max_mcs, max_mcs_table);
1960:     if (nrmac->ul_mcs_scan_enabled) {
1961:       uint8_t target_mcs;
1962:       if (nrmac->ul_mcs_scan_auto_sweep) {
1963:         uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;
1964:         uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);
1965:         uint8_t scan_start = nrmac->ul_mcs_scan_start;
1966:         if (scan_start < scan_min) scan_start = scan_min;
1967:         if (scan_start > scan_max) scan_start = scan_max;
1968:         int mcs_range = scan_max - scan_min + 1;
1969:         uint32_t period = nrmac->ul_mcs_scan_period;
1970:         uint32_t cb_period = nrmac->ul_mcs_scan_cb_period;
1971:         
1972:         if (nrmac->ul_mcs_scan_last_frame != frame) {
1973:           nrmac->ul_mcs_scan_last_frame = frame;
1974:           
1975:           int mcs_index = nrmac->ul_mcs_scan_current_index;
1976:           int upper_range = scan_max - scan_start + 1;
1977:           uint8_t current_mcs;
1978:           if (mcs_index < upper_range) {
1979:             current_mcs = scan_start + mcs_index;
1980:           } else {
1981:             current_mcs = scan_min + (mcs_index - upper_range);
1982:           }
1983:           
1984:           nrmac->ul_mcs_scan_accum_frames++;
1985:           nrmac->ul_mcs_scan_cb_accum_frames++;
1986:           
1987:           if (nrmac->ul_mcs_scan_accum_frames >= period) {
1988:             nrmac->ul_mcs_scan_accum_frames = 0;
1989:             nrmac->ul_mcs_scan_cb_progress[current_mcs] = nrmac->ul_mcs_scan_current_cb_index;
1990:             nrmac->ul_mcs_scan_current_index++;
1991:             if (nrmac->ul_mcs_scan_current_index >= mcs_range) {
1992:               nrmac->ul_mcs_scan_current_index = 0;
1993:             }
1994:             nrmac->ul_mcs_scan_cb_accum_frames = 0;
1995:           }
1996:         }
1997:         
1998:         int mcs_index = nrmac->ul_mcs_scan_current_index;
1999:         int upper_range = scan_max - scan_start + 1;
2000:         if (mcs_index < upper_range) {
2001:           target_mcs = scan_start + mcs_index;
2002:         } else {
2003:           target_mcs = scan_min + (mcs_index - upper_range);
2004:         }
2005:         
2006:         if (nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs] == 0) {
2007:           uint16_t R;
2008:           uint8_t Qm;
2009:           update_ul_ue_R_Qm(target_mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &R, &Qm);
2010:           compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,
2011:                                          nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],
2012:                                          &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);
2013:           nrmac->ul_mcs_scan_cb_progress[target_mcs] = 0;
2014:         }
2015:         
2016:         nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];
2017:         nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];
2018:         memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 
2019:                sizeof(nrmac->ul_mcs_scan_rb_values));
2020:         
2021:         if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {
2022:           nrmac->ul_mcs_scan_cb_accum_frames = 0;
2023:           if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {
2024:             nrmac->ul_mcs_scan_current_cb_index++;
2025:             nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;
2026:           }
2027:         }
2028:         
2029:         uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2030:         uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2031:         LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, cb_idx=%d/%d, rb=%d\n",
2032:               frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);
2033:       } else {
2034:         target_mcs = nrmac->ul_mcs_scan_ref;
2035:       }
2036:       sched_pusch->mcs = min(target_mcs, max_mcs);
2037:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2038:     } else if (bo->harq_round_max == 1) {
2039:       sched_pusch->mcs = max_mcs;
2040:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2041:     } else {
2042:       sched_pusch->mcs = get_mcs_from_bler(bo, stats, &sched_ctrl->ul_bler_stats, max_mcs, frame);
2043:       LOG_W(NR_MAC,"%d.%d starting mcs %d bleri %f,bo->max_mcs = %d\n", frame, slot, sched_pusch->mcs, sched_ctrl->ul_bler_stats.bler,bo->max_mcs);
2044:     }
2045:     // LOG_W(NR_MAC,"sched_pusch->mcs = %d",sched_pusch->mcs);
2046:     /* Schedule UE on SR or UL inactivity and no data (otherwise, will be scheduled
2047:      * based on data to transmit) */
2048:     if (B == 0 && do_sched) {
2049:       /* if no data, pre-allocate 5RB */
2050:       /* Find a free CCE */
2051:       int CCEIndex = get_cce_index(nrmac,
2052:                                    CC_id, slot, UE->rnti,
2053:                                    &sched_ctrl->aggregation_level,
2054:                                    dci_beam.idx,
2055:                                    sched_ctrl->search_space,
2056:                                    sched_ctrl->coreset,
2057:                                    &sched_ctrl->sched_pdcch,
2058:                                    false,
2059:                                    sched_ctrl->pdcch_cl_adjust);
2060:       if (CCEIndex < 0) {
2061:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI (BSR 0)\n", UE->rnti, frame, slot);
2062:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2063:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2064:         continue;
2065:       }
2066: 
2067:       sched_pusch->nrOfLayers = sched_ctrl->srs_feedback.ul_ri + 1;
2068:       sched_pusch->time_domain_allocation = get_ul_tda(nrmac, sched_frame, sched_slot);
2069:       sched_pusch->tda_info = get_ul_tda_info(current_BWP,
2070:                                               sched_ctrl->coreset->controlResourceSetId,
2071:                                               sched_ctrl->search_space->searchSpaceType->present,
2072:                                               TYPE_C_RNTI_,
2073:                                               sched_pusch->time_domain_allocation);
2074:       AssertFatal(sched_pusch->tda_info.valid_tda, "Invalid TDA from get_ul_tda_info\n");
2075:       sched_pusch->dmrs_info = get_ul_dmrs_params(scc, current_BWP, &sched_pusch->tda_info, sched_pusch->nrOfLayers);
2076: 
2077:       int rbStart = 0; // wrt BWP start
2078:       LOG_D(NR_MAC,
2079:             "Looking for min_rb %d RBs, starting at %d num_dmrs_cdm_grps_no_data %d\n",
2080:             min_rb,
2081:             rbStart,
2082:             sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data);
2083:       const uint32_t bwpSize = current_BWP->BWPSize;
2084:       const uint32_t bwpStart = current_BWP->BWPStart;
2085:       const uint16_t slbitmap = SL_to_bitmap(sched_pusch->tda_info.startSymbolIndex, sched_pusch->tda_info.nrOfSymbols);
2086:       while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
2087:         rbStart++;
2088:       if (rbStart + min_rb >= bwpSize) {
2089:         LOG_D(NR_MAC,
2090:               "[UE %04x][%4d.%2d] could not allocate continuous UL data: no resources (rbStart %d, min_rb %d, bwpSize %d)\n",
2091:               UE->rnti,
2092:               frame,
2093:               slot,
2094:               rbStart,
2095:               min_rb,
2096:               bwpSize);
2097:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2098:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2099:         continue;
2100:       }
2101: 
2102:       sched_ctrl->cce_index = CCEIndex;
2103:       fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam.idx);
2104: 
2105:       NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2106:       sched_pusch->mcs = min(nrmac->min_grant_mcs, sched_pusch->mcs);
2107:       update_ul_ue_R_Qm(sched_pusch->mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &sched_pusch->R, &sched_pusch->Qm);
2108:       sched_pusch->rbStart = rbStart;
2109:       sched_pusch->rbSize = min_rb;
2110:       sched_pusch->frame = sched_frame;
2111:       sched_pusch->slot = sched_slot;
2112:       sched_pusch->tb_size = nr_compute_tbs(sched_pusch->Qm,
2113:                                             sched_pusch->R,
2114:                                             sched_pusch->rbSize,
2115:                                             sched_pusch->tda_info.nrOfSymbols,
2116:                                             sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2117:                                             0, // nb_rb_oh
2118:                                             0,
2119:                                             sched_pusch->nrOfLayers) >> 3;
2120:       long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2121: 
2122:       sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2123:                                                         sched_pusch->tb_size << 3,
2124:                                                         sched_pusch->rbSize,
2125:                                                         sched_pusch->nrOfLayers,
2126:                                                         sched_pusch->tda_info.nrOfSymbols,
2127:                                                         sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2128:                                                         deltaMCS,
2129:                                                         false);
2130:       LOG_D(NR_MAC,
2131:             "pf_ul %d.%d UE %x Scheduling PUSCH (no data) nrb %d mcs %d tbs %d bits phr_txpower %d\n",
2132:             frame,
2133:             slot,
2134:             UE->rnti,
2135:             sched_pusch->rbSize,
2136:             sched_pusch->mcs,
2137:             sched_pusch->tb_size << 3,
2138:             sched_pusch->phr_txpower_calc);
2139: 
2140:       /* Mark the corresponding RBs as used */
2141:       n_rb_sched[beam.idx] -= sched_pusch->rbSize;
2142:       for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
2143:         rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= slbitmap;
2144: 
2145:       remainUEs[beam.idx]--;
2146:       continue;
2147:     }
2148: 
2149:     /* Create UE_sched for UEs eligibale for new data transmission*/
2150:     /* Calculate coefficient*/
2151:     const uint32_t tbs = ul_pf_tbs[current_BWP->mcs_table][sched_pusch->mcs];
2152:     float coeff_ue = (float) tbs / UE->ul_thr_ue;
2153:     LOG_D(NR_MAC, "[UE %04x][%4d.%2d] b %d, ul_thr_ue %f, tbs %d, coeff_ue %f\n",
2154:           UE->rnti,
2155:           frame,
2156:           slot,
2157:           b,
2158:           UE->ul_thr_ue,
2159:           tbs,
2160:           coeff_ue);
2161:     UE_sched[curUE].coef = coeff_ue;
2162:     UE_sched[curUE].UE = UE;
2163:     curUE++;
2164:   }
2165: 
2166:   qsort(UE_sched, sizeofArray(UE_sched), sizeof(UEsched_t), comparator);
2167:   UEsched_t *iterator=UE_sched;
2168: 
2169:   /* Loop UE_sched to find max coeff and allocate transmission */
2170:   while (iterator->UE != NULL) {
2171:     NR_UE_UL_BWP_t *current_BWP = &iterator->UE->current_UL_BWP;
2172:     NR_UE_sched_ctrl_t *sched_ctrl = &iterator->UE->UE_sched_ctrl;
2173:     NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2174: 
2175:     NR_beam_alloc_t beam = beam_allocation_procedure(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame);
2176:     if (beam.idx < 0) {
2177:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", iterator->UE->rnti, frame, slot);
2178:       iterator++;
2179:       continue;
2180:     }
2181: 
2182:     if (remainUEs[beam.idx] == 0 || n_rb_sched[beam.idx] < min_rb) {
2183:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2184:       iterator++;
2185:       continue;
2186:     }
2187: 
2188:     NR_beam_alloc_t dci_beam = beam_allocation_procedure(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame);
2189:     if (dci_beam.idx < 0) {
2190:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", iterator->UE->rnti, frame, slot);
2191:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2192:       iterator++;
2193:       continue;
2194:     }
2195: 
2196:     int CCEIndex = get_cce_index(nrmac,
2197:                                  CC_id, slot, iterator->UE->rnti,
2198:                                  &sched_ctrl->aggregation_level,
2199:                                  dci_beam.idx,
2200:                                  sched_ctrl->search_space,
2201:                                  sched_ctrl->coreset,
2202:                                  &sched_ctrl->sched_pdcch,
2203:                                  false,
2204:                                  sched_ctrl->pdcch_cl_adjust);
2205: 
2206:     if (CCEIndex < 0) {
2207:       reset_beam_status(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2208:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2209:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI\n", iterator->UE->rnti, frame, slot);
2210:       iterator++;
2211:       continue;
2212:     }
2213:     else
2214:       LOG_D(NR_MAC, "%4d.%2d free CCE for UL DCI UE %04x\n", frame, slot, iterator->UE->rnti);
2215: 
2216: 
2217: 
2218:     sched_pusch->nrOfLayers = sched_ctrl->srs_feedback.ul_ri + 1;
2219:     sched_pusch->time_domain_allocation = get_ul_tda(nrmac, sched_frame, sched_slot);
2220:     sched_pusch->tda_info = get_ul_tda_info(current_BWP,
2221:                                             sched_ctrl->coreset->controlResourceSetId,
2222:                                             sched_ctrl->search_space->searchSpaceType->present,
2223:                                             TYPE_C_RNTI_,
2224:                                             sched_pusch->time_domain_allocation);
2225:     AssertFatal(sched_pusch->tda_info.valid_tda, "Invalid TDA from get_ul_tda_info\n");
2226:     sched_pusch->dmrs_info = get_ul_dmrs_params(scc, current_BWP, &sched_pusch->tda_info, sched_pusch->nrOfLayers);
2227: 
2228:     const int index = ul_buffer_index(sched_frame, sched_slot, slots_per_frame, nrmac->vrb_map_UL_size);
2229:     uint16_t *rballoc_mask = &nrmac->common_channels[CC_id].vrb_map_UL[beam.idx][index * MAX_BWP_SIZE];
2230: 
2231:     int rbStart = 0;
2232:     const uint16_t slbitmap = SL_to_bitmap(sched_pusch->tda_info.startSymbolIndex, sched_pusch->tda_info.nrOfSymbols);
2233:     const uint32_t bwpSize = current_BWP->BWPSize;
2234:     const uint32_t bwpStart = current_BWP->BWPStart;
2235:     // LOG_W(PHY,"bwpsize = %d,bwpstart = %d",bwpSize,bwpStart);
2236:     while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
2237:       rbStart++;
2238:   
2239:     sched_pusch->rbStart = rbStart;
2240:     uint16_t max_rbSize = 1;
2241:     uint16_t max_hcs_rb_size;
2242:     if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {
2243:       uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2244:       max_hcs_rb_size = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2245:       if (max_hcs_rb_size < 5) max_hcs_rb_size = 5;
2246:       if (max_hcs_rb_size > 273) max_hcs_rb_size = 273;
2247:     } else {
2248:       max_hcs_rb_size = rand_in_range(10, 273);
2249:     }
2250:     // uint16_t max_hcs_rb_size = 150;
2251:     while (rbStart + max_rbSize < bwpSize && !(rballoc_mask[rbStart + bwpStart + max_rbSize] & slbitmap)){
2252:             max_rbSize++;
2253:     }
2254:     max_rbSize = min(max_rbSize, max_hcs_rb_size);
2255:     
2256:     // double prediction =  LeafModelExported_predict_runtime_cost_p70(sched_pusch->mcs, sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2257:     // int best_prb = select_prb(sched_pusch->mcs,sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2258:     LOG_W(PHY,"max_rbSize = %hd\n",max_rbSize);
2259:     // LOG_W(PHY,"max_rbSize = %hd,prediction = %f\n",max_rbSize,prediction);
2260:     // max_rbSize = best_prb;
2261:       //by Luhan
2262:     // LOG_W(MAC,"---------------by Luhan, max_rbSize is %d, slot is %d, sched_slot is %d \n",max_rbSize, slot,sched_slot);
2263:     
2264:     if (rbStart + min_rb >= bwpSize || max_rbSize < min_rb) {
2265:       reset_beam_status(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2266:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2267:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] could not allocate UL data: no resources (rbStart %d, min_rb %d, bwpSize %d)\n",
2268:             iterator->UE->rnti,
2269:             frame,
2270:             slot,
2271:             rbStart,
2272:             min_rb,
2273:             bwpSize);
2274:       iterator++;
2275:       continue;
2276:     } else
2277:       LOG_D(NR_MAC,
2278:             "allocating UL data for RNTI %04x (rbStart %d, min_rb %d, max_rbSize %d, bwpSize %d)\n",
2279:             iterator->UE->rnti,
2280:             rbStart,
2281:             min_rb,
2282:             max_rbSize,
2283:             bwpSize);
2284: 
2285:     /* Calculate the current scheduling bytes */
2286:     const int B = cmax(sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes, 0);
2287:     /* adjust rbSize and MCS according to PHR and BPRE */
2288:     if(sched_ctrl->pcmax != 0 || sched_ctrl->ph != 0) // verify if the PHR related parameter have been initialized
2289:       nr_ue_max_mcs_min_rb(current_BWP->scs, sched_ctrl->ph, sched_pusch, current_BWP, min_rb, B, &max_rbSize, &sched_pusch->mcs);
2290:     
2291:     if (sched_pusch->mcs < sched_ctrl->ul_bler_stats.mcs)
2292:     sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs; /* force estimated MCS down */
2293: 
2294:     update_ul_ue_R_Qm(sched_pusch->mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &sched_pusch->R, &sched_pusch->Qm);
2295:     uint16_t rbSize = 0;
2296:     uint32_t TBS = 0;
2297:     nr_find_nb_rb(sched_pusch->Qm,
2298:                   sched_pusch->R,
2299:                   current_BWP->transform_precoding,
2300:                   sched_pusch->nrOfLayers,
2301:                   sched_pusch->tda_info.nrOfSymbols,
2302:                   sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2303:                   B,
2304:                   min_rb,
2305:                   max_rbSize,
2306:                   &TBS,
2307:                   &rbSize);
2308: 
2309:     // Calacualte the normalized tx_power for PHR
2310:     long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2311:     int tbs_bits = TBS << 3;
2312: 
2313:     sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2314:                                                       tbs_bits,
2315:                                                       rbSize,
2316:                                                       sched_pusch->nrOfLayers,
2317:                                                       sched_pusch->tda_info.nrOfSymbols,
2318:                                                       sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2319:                                                       deltaMCS,
2320:                                                       false);
2321: 
2322:     sched_pusch->rbSize = rbSize;
2323:     sched_pusch->tb_size = TBS;
2324:     sched_pusch->frame = sched_frame;
2325:     sched_pusch->slot = sched_slot;
2326:     uint32_t B_bits = sched_pusch->tb_size << 3;
2327:     uint8_t BG = get_BG(B_bits, sched_pusch->R);
2328:     uint32_t Kcb = (BG == 1) ? 8448 : 3840;
2329:     uint32_t num_cb;
2330:     if (B_bits <= Kcb) {
2331:       num_cb = 1;
2332:     } else {
2333:       num_cb = B_bits / (Kcb - 24);
2334:       if ((Kcb - 24) * num_cb < B_bits)
2335:         num_cb++;
2336:     }
2337:     LOG_W(NR_MAC,
2338:           "rbSize %d (max_rbSize %d), TBS %d, est buf %d, sched_ul %d, B %d, CCE %d, num_dmrs_symb %d, N_PRB_DMRS %d, BG=%d, num_cb=%d\n",
2339:           rbSize,
2340:           max_rbSize,
2341:           sched_pusch->tb_size,
2342:           sched_ctrl->estimated_ul_buffer,
2343:           sched_ctrl->sched_ul_bytes,
2344:           B,
2345:           sched_ctrl->cce_index,
2346:           sched_pusch->dmrs_info.num_dmrs_symb,
2347:           sched_pusch->dmrs_info.N_PRB_DMRS,
2348:           BG,
2349:           num_cb);
2350: 
2351:     /* Mark the corresponding RBs as used */
2352: 
2353:     sched_ctrl->cce_index = CCEIndex;
2354:     fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam.idx);
2355: 
2356:     n_rb_sched[beam.idx] -= sched_pusch->rbSize;
2357:     for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
2358:       rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= slbitmap;
2359: 
2360:     /* reduce max_num_ue once we are sure UE can be allocated, i.e., has CCE */
2361:     remainUEs[beam.idx]--;
2362:     iterator++;
2363:   }
2364: }
2365: 
2366: static bool nr_ulsch_preprocessor(module_id_t module_id, frame_t frame, sub_frame_t slot)
2367: {
2368:   gNB_MAC_INST *nr_mac = RC.nrmac[module_id];
2369:   // no UEs
2370:   if (nr_mac->UE_info.list[0] == NULL)
2371:     return false;
2372: 
2373:   NR_COMMON_channels_t *cc = nr_mac->common_channels;
2374:   NR_ServingCellConfigCommon_t *scc = cc->ServingCellConfigCommon;
2375:   const NR_SIB1_t *sib1 = nr_mac->common_channels[0].sib1 ? nr_mac->common_channels[0].sib1->message.choice.c1->choice.systemInformationBlockType1 : NULL;
2376:   NR_ServingCellConfigCommonSIB_t *scc_sib1 = sib1 ? sib1->servingCellConfigCommon : NULL;
2377:   AssertFatal(scc || scc_sib1, "We need one serving cell config common\n");
2378:   const int slots_frame = nr_mac->frame_structure.numb_slots_frame;
2379:   // TODO we assume the same K2 for all UEs
2380:   const int K2 = nr_mac->radio_config.minRXTXTIME + get_NTN_Koffset(scc);
2381:   const int sched_frame = (frame + (slot + K2) / slots_frame) % MAX_FRAME_NUMBER;
2382:   const int sched_slot = (slot + K2) % slots_frame;
2383:   //by Luhan
2384:   // LOG_W(MAC, "----in nr_ulsch_preprossor, frame is %d, sched_slot is %d , K2 is %d, slot is %d \n", frame, sched_slot, K2,slot);
2385: 
2386:   if (!is_ul_slot(sched_slot, &nr_mac->frame_structure))
2387:   {
2388:     //  LOG_W(MAC, "----in nr_ulsch_preprossor, sched_slot is %d , IS NOT UL \n",sched_slot);
2389:     return false;
2390:   }
2391:     
2392: 
2393:   int num_beams = nr_mac->beam_info.beam_allocation ? nr_mac->beam_info.beams_per_period : 1;
2394:   int bw = scc->uplinkConfigCommon->frequencyInfoUL->scs_SpecificCarrierList.list.array[0]->carrierBandwidth;
2395:   int len[num_beams];
2396:   for (int i = 0; i < num_beams; i++)
2397:     len[i] = bw;
2398: 
2399:   int average_agg_level = 4; // TODO find a better estimation
2400:   int max_sched_ues = bw / (average_agg_level * NR_NB_REG_PER_CCE);
2401: 
2402:   // FAPI cannot handle more than MAX_DCI_CORESET DCIs
2403:   max_sched_ues = min(max_sched_ues, MAX_DCI_CORESET);
2404: 
2405:   /* proportional fair scheduling algorithm */
2406:   pf_ul(module_id, frame, slot, sched_frame, sched_slot, nr_mac->UE_info.list, max_sched_ues, num_beams, len);
2407:   return true;
2408: }
2409: 
2410: nr_pp_impl_ul nr_init_ulsch_preprocessor(int CC_id)
2411: {
2412:   /* during initialization: no mutex needed */
2413:   /* in the PF algorithm, we have to use the TBsize to compute the coefficient.
2414:    * This would include the number of DMRS symbols, which in turn depends on
2415:    * the time domain allocation. In case we are in a mixed slot, we do not want
2416:    * to recalculate all these values, and therefore we provide a look-up table
2417:    * which should approximately(!) give us the TBsize. In particular, the
2418:    * number of symbols, the number of DMRS symbols, and the exact Qm and R, are
2419:    * not correct*/
2420:   for (int mcsTableIdx = 0; mcsTableIdx < 5; ++mcsTableIdx) {
2421:     for (int mcs = 0; mcs < 29; ++mcs) {
2422:       if (mcs > 27 && (mcsTableIdx == 1 || mcsTableIdx == 3 || mcsTableIdx == 4))
2423:         continue;
2424:       const uint8_t Qm = nr_get_Qm_ul(mcs, mcsTableIdx);
2425:       const uint16_t R = nr_get_code_rate_ul(mcs, mcsTableIdx);
2426:       /* note: we do not update R/Qm based on low MCS or pi2BPSK */
2427:       ul_pf_tbs[mcsTableIdx][mcs] = nr_compute_tbs(Qm,
2428:                                                    R,
2429:                                                    1, /* rbSize */
2430:                                                    10, /* hypothetical number of slots */
2431:                                                    0, /* N_PRB_DMRS * N_DMRS_SLOT */
2432:                                                    0 /* N_PRB_oh, 0 for initialBWP */,
2433:                                                    0 /* tb_scaling */,
2434:                                                    1 /* nrOfLayers */)
2435:                                     >> 3;
2436:     }
2437:   }
2438:   return nr_ulsch_preprocessor;
2439: }
2440: 
2441: void nr_schedule_ulsch(module_id_t module_id, frame_t frame, sub_frame_t slot, nfapi_nr_ul_dci_request_t *ul_dci_req)
2442: {
2443:   gNB_MAC_INST *nr_mac = RC.nrmac[module_id];
2444:   /* already mutex protected: held in gNB_dlsch_ulsch_scheduler() */
2445:   NR_SCHED_ENSURE_LOCKED(&nr_mac->sched_lock);
2446: 
2447:   /* Uplink data ONLY can be scheduled when the current slot is downlink slot,
2448:    * because we have to schedule the DCI0 first before schedule uplink data */
2449:   //by Luhan
2450:   // LOG_W(NR_MAC, "!!!!!!Current slot %d is slot\n",slot);
2451:   if (!is_dl_slot(slot, &nr_mac->frame_structure)) {
2452:     // LOG_W(NR_MAC, "!!!!!!Current slot %d is NOT DL slot, cannot schedule DCI0 for UL data\n", slot);
2453:     return;
2454:   }
2455:   bool do_sched = nr_mac->pre_processor_ul(module_id, frame, slot);
2456:   if (!do_sched)
2457:   {
2458:     // LOG_W(NR_MAC, "!!!!!!Cannot schedule uplink, current dl slot is %d\n",slot);
2459:     return;
2460:   }
2461:     
2462: 
2463:   ul_dci_req->SFN = frame;
2464:   ul_dci_req->Slot = slot;
2465:   /* a PDCCH PDU groups DCIs per BWP and CORESET. Save a pointer to each
2466:    * allocated PDCCH so we can easily allocate UE's DCIs independent of any
2467:    * CORESET order */
2468:   nfapi_nr_dl_tti_pdcch_pdu_rel15_t *pdcch_pdu_coreset[MAX_NUM_CORESET] = {0};
2469: 
2470: 
2471:   NR_ServingCellConfigCommon_t *scc = nr_mac->common_channels[0].ServingCellConfigCommon;
2472:   NR_UEs_t *UE_info = &nr_mac->UE_info;
2473:   UE_iterator( UE_info->list, UE) {
2474:     NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
2475:     if (sched_ctrl->ul_failure && !get_softmodem_params()->phy_test)
2476:       continue;
2477: 

(Output capped at 50 KB. Showing lines 1389-2477. Use offset=2478 to continue.)
</content>
```

---

## Assistant (Plan · glm-5 · 68.9s)

_Thinking:_

从文件内容来看，我找到了一些相关的功能：

1. 在第 43-74 行有一个函数 `compute_rb_boundaries_for_mcs`，这个函数是用于计算不同 MCS 对应的 RB 边界值，用于遍历足够的 RB。

2. 在第 2242-2255 行，有关于 `ul_mcs_scan_enabled` 和 `ul_mcs_scan_auto_sweep` 的逻辑，这里用到了 `max_hcs_rb_size` 的计算，这看起来是用于自动扫描 MCS 和 CB (code block) 的 RB 遍历功能。

让我继续查看文件后面的内容，看看是否有更多关于 RB 替换的代码。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 2478
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
2478:     NR_UE_UL_BWP_t *current_BWP = &UE->current_UL_BWP;
2479: 
2480:     UE->mac_stats.ul.current_bytes = 0;
2481:     UE->mac_stats.ul.current_rbs = 0;
2482: 
2483:     /* dynamic PUSCH values (RB alloc, MCS, hence R, Qm, TBS) that change in
2484:      * every TTI are pre-populated by the preprocessor and used below */
2485:     NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2486:     LOG_D(NR_MAC,"UE %04x : sched_pusch->rbSize %d\n",UE->rnti,sched_pusch->rbSize);
2487:     if (sched_pusch->rbSize <= 0)
2488:       continue;
2489: 
2490:     uint16_t rnti = UE->rnti;
2491:     sched_ctrl->SR = false;
2492:     int *tpmi = NULL;
2493: 
2494:     int8_t harq_id = sched_pusch->ul_harq_pid;
2495:     if (harq_id < 0) {
2496:       /* PP has not selected a specific HARQ Process, get a new one */
2497:       harq_id = sched_ctrl->available_ul_harq.head;
2498:       AssertFatal(harq_id >= 0,
2499:                   "no free HARQ process available for UE %04x\n",
2500:                   UE->rnti);
2501:       remove_front_nr_list(&sched_ctrl->available_ul_harq);
2502:       sched_pusch->ul_harq_pid = harq_id;
2503:     } else {
2504:       /* PP selected a specific HARQ process. Check whether it will be a new
2505:        * transmission or a retransmission, and remove from the corresponding
2506:        * list */
2507:       if (sched_ctrl->ul_harq_processes[harq_id].round == 0)
2508:         remove_nr_list(&sched_ctrl->available_ul_harq, harq_id);
2509:       else
2510:         remove_nr_list(&sched_ctrl->retrans_ul_harq, harq_id);
2511:     }
2512:     NR_UE_ul_harq_t *cur_harq = &sched_ctrl->ul_harq_processes[harq_id];
2513:     DevAssert(!cur_harq->is_waiting);
2514:     if (nr_mac->radio_config.disable_harq) {
2515:       finish_nr_ul_harq(sched_ctrl, harq_id);
2516:     } else {
2517:       add_tail_nr_list(&sched_ctrl->feedback_ul_harq, harq_id);
2518:       cur_harq->feedback_slot = sched_pusch->slot;
2519:       cur_harq->is_waiting = true;
2520:     }
2521: 
2522:     /* Statistics */
2523:     AssertFatal(cur_harq->round < nr_mac->ul_bler.harq_round_max, "Indexing ulsch_rounds[%d] is out of bounds\n", cur_harq->round);
2524:     UE->mac_stats.ul.rounds[cur_harq->round]++;
2525:     if (cur_harq->round == 0) {
2526:       UE->mac_stats.ulsch_total_bytes_scheduled += sched_pusch->tb_size;
2527:       /* Save information on MCS, TBS etc for the current initial transmission
2528:        * so we have access to it when retransmitting */
2529:       cur_harq->sched_pusch = *sched_pusch;
2530:       /* save which time allocation and nrOfLayers have been used, to be used on
2531:        * retransmissions */
2532:       cur_harq->sched_pusch.time_domain_allocation = sched_pusch->time_domain_allocation;
2533:       cur_harq->sched_pusch.nrOfLayers = sched_pusch->nrOfLayers;
2534:       cur_harq->sched_pusch.tpmi = sched_pusch->tpmi;
2535:       sched_ctrl->sched_ul_bytes += sched_pusch->tb_size;
2536:       UE->mac_stats.ul.total_rbs += sched_pusch->rbSize;
2537: 
2538:     } else {
2539:       LOG_D(NR_MAC,
2540:             "%d.%2d UL retransmission RNTI %04x sched %d.%2d HARQ PID %d round %d NDI %d\n",
2541:             frame,
2542:             slot,
2543:             rnti,
2544:             sched_pusch->frame,
2545:             sched_pusch->slot,
2546:             harq_id,
2547:             cur_harq->round,
2548:             cur_harq->ndi);
2549:       UE->mac_stats.ul.total_rbs_retx += sched_pusch->rbSize;
2550:     }
2551:     UE->mac_stats.ul.current_bytes = sched_pusch->tb_size;
2552:     UE->mac_stats.ul.current_rbs = sched_pusch->rbSize;
2553:     sched_ctrl->last_ul_frame = sched_pusch->frame;
2554:     sched_ctrl->last_ul_slot = sched_pusch->slot;
2555: 
2556:     LOG_W(NR_MAC,
2557:           "ULSCH/PUSCH: %4d.%2d RNTI %04x UL sched %4d.%2d DCI L %d start %2d RBS %3d startSymbol %2d nb_symbol %2d dmrs_pos %x MCS Table %2d MCS %2d nrOfLayers %2d num_dmrs_cdm_grps_no_data %2d TBS %4d HARQ PID %2d round %d RV %d NDI %d est %6d sched %6d est BSR %6d TPC %d\n",
2558:           frame,
2559:           slot,
2560:           rnti,
2561:           sched_pusch->frame,
2562:           sched_pusch->slot,
2563:           sched_ctrl->aggregation_level,
2564:           sched_pusch->rbStart,
2565:           sched_pusch->rbSize,
2566:           sched_pusch->tda_info.startSymbolIndex,
2567:           sched_pusch->tda_info.nrOfSymbols,
2568:           sched_pusch->dmrs_info.ul_dmrs_symb_pos,
2569:           current_BWP->mcs_table,
2570:           sched_pusch->mcs,
2571:           sched_pusch->nrOfLayers,
2572:           sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data,
2573:           sched_pusch->tb_size,
2574:           harq_id,
2575:           cur_harq->round,
2576:           nr_rv_round_map[cur_harq->round%4],
2577:           cur_harq->ndi,
2578:           sched_ctrl->estimated_ul_buffer,
2579:           sched_ctrl->sched_ul_bytes,
2580:           sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes,
2581:           sched_ctrl->tpc0);
2582: 
2583:     /* PUSCH in a later slot, but corresponding DCI now! */
2584:     const int index = ul_buffer_index(sched_pusch->frame,
2585:                                       sched_pusch->slot,
2586:                                       nr_mac->frame_structure.numb_slots_frame,
2587:                                       nr_mac->UL_tti_req_ahead_size);
2588:     nfapi_nr_ul_tti_request_t *future_ul_tti_req = &nr_mac->UL_tti_req_ahead[0][index];
2589:     if (future_ul_tti_req->SFN != sched_pusch->frame || future_ul_tti_req->Slot != sched_pusch->slot)
2590:       LOG_W(NR_MAC,
2591:             "%d.%d future UL_tti_req's frame.slot %d.%d does not match PUSCH %d.%d\n",
2592:             frame, slot,
2593:             future_ul_tti_req->SFN,
2594:             future_ul_tti_req->Slot,
2595:             sched_pusch->frame,
2596:             sched_pusch->slot);
2597:     AssertFatal(future_ul_tti_req->n_pdus <
2598:                 sizeof(future_ul_tti_req->pdus_list) / sizeof(future_ul_tti_req->pdus_list[0]),
2599:                 "Invalid future_ul_tti_req->n_pdus %d\n", future_ul_tti_req->n_pdus);
2600: 
2601:     future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pdu_type = NFAPI_NR_UL_CONFIG_PUSCH_PDU_TYPE;
2602:     future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pdu_size = sizeof(nfapi_nr_pusch_pdu_t);
2603:     nfapi_nr_pusch_pdu_t *pusch_pdu = &future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pusch_pdu;
2604:     memset(pusch_pdu, 0, sizeof(nfapi_nr_pusch_pdu_t));
2605:     future_ul_tti_req->n_pdus += 1;
2606: 
2607:     LOG_D(NR_MAC,
2608:           "%4d.%2d Scheduling UE specific PUSCH for sched %d.%d, ul_tti_req %d.%d\n",
2609:           frame,
2610:           slot,
2611:           sched_pusch->frame,
2612:           sched_pusch->slot,
2613:           future_ul_tti_req->SFN,
2614:           future_ul_tti_req->Slot);
2615: 
2616:     pusch_pdu->pdu_bit_map = PUSCH_PDU_BITMAP_PUSCH_DATA;
2617:     pusch_pdu->rnti = rnti;
2618:     pusch_pdu->handle = 0; //not yet used
2619: 
2620:     /* FAPI: BWP */
2621: 
2622:     pusch_pdu->bwp_size  = current_BWP->BWPSize;
2623:     pusch_pdu->bwp_start = current_BWP->BWPStart;
2624:     pusch_pdu->subcarrier_spacing = current_BWP->scs;
2625:     pusch_pdu->cyclic_prefix = 0;
2626: 
2627:     /* FAPI: PUSCH information always included */
2628:     pusch_pdu->target_code_rate = sched_pusch->R;
2629:     pusch_pdu->qam_mod_order = sched_pusch->Qm;
2630:     pusch_pdu->mcs_index = sched_pusch->mcs;
2631:     pusch_pdu->mcs_table = current_BWP->mcs_table;
2632:     pusch_pdu->transform_precoding = current_BWP->transform_precoding;
2633:     if (current_BWP->pusch_Config && current_BWP->pusch_Config->dataScramblingIdentityPUSCH)
2634:       pusch_pdu->data_scrambling_id = *current_BWP->pusch_Config->dataScramblingIdentityPUSCH;
2635:     else
2636:       pusch_pdu->data_scrambling_id = *scc->physCellId;
2637:     pusch_pdu->nrOfLayers = sched_pusch->nrOfLayers;
2638:     // If nrOfLayers is the same as in srs_feedback, we use the best TPMI, i.e. the one in srs_feedback.
2639:     // Otherwise, we use the valid TPMI that we saved in the first transmission.
2640:     if (pusch_pdu->nrOfLayers != (sched_ctrl->srs_feedback.ul_ri + 1))
2641:       tpmi = &sched_pusch->tpmi;
2642:     pusch_pdu->num_dmrs_cdm_grps_no_data = sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data;
2643: 
2644:     /* FAPI: DMRS */
2645:     pusch_pdu->num_dmrs_cdm_grps_no_data = sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data;
2646:     pusch_pdu->dmrs_ports = ((1<<sched_pusch->nrOfLayers) - 1);
2647:     pusch_pdu->ul_dmrs_symb_pos = sched_pusch->dmrs_info.ul_dmrs_symb_pos;
2648:     pusch_pdu->dmrs_config_type = sched_pusch->dmrs_info.dmrs_config_type;
2649:     pusch_pdu->scid = 0;      // DMRS sequence initialization [TS38.211, sec 6.4.1.1.1]
2650:     const NR_DMRS_UplinkConfig_t *NR_DMRS_UplinkConfig = get_DMRS_UplinkConfig(current_BWP->pusch_Config, &sched_pusch->tda_info);
2651:     if (pusch_pdu->transform_precoding) { // transform precoding disabled
2652:       long *scramblingid=NULL;
2653:       pusch_pdu->pusch_identity = *scc->physCellId;
2654:       if (NR_DMRS_UplinkConfig && pusch_pdu->scid == 0)
2655:         scramblingid = NR_DMRS_UplinkConfig->transformPrecodingDisabled->scramblingID0;
2656:       else if (NR_DMRS_UplinkConfig)
2657:         scramblingid = NR_DMRS_UplinkConfig->transformPrecodingDisabled->scramblingID1;
2658:       if (scramblingid == NULL)
2659:         pusch_pdu->ul_dmrs_scrambling_id = *scc->physCellId;
2660:       else
2661:         pusch_pdu->ul_dmrs_scrambling_id = *scramblingid;
2662:     }
2663:     else {
2664:       pusch_pdu->ul_dmrs_scrambling_id = *scc->physCellId;
2665:       if (NR_DMRS_UplinkConfig &&
2666:           NR_DMRS_UplinkConfig->transformPrecodingEnabled &&
2667:           NR_DMRS_UplinkConfig->transformPrecodingEnabled->nPUSCH_Identity != NULL)
2668:         pusch_pdu->pusch_identity = *NR_DMRS_UplinkConfig->transformPrecodingEnabled->nPUSCH_Identity;
2669:       else if (NR_DMRS_UplinkConfig)
2670:         pusch_pdu->pusch_identity = *scc->physCellId;
2671:     }
2672:     pusch_pdu->scid = 0;      // DMRS sequence initialization [TS38.211, sec 6.4.1.1.1]
2673:     pusch_pdu->dmrs_ports = ((1<<sched_pusch->nrOfLayers) - 1);
2674: 
2675:     /* FAPI: Pusch Allocation in frequency domain */
2676:     pusch_pdu->resource_alloc = 1; //type 1
2677:     pusch_pdu->rb_start = sched_pusch->rbStart;
2678:     pusch_pdu->rb_size = sched_pusch->rbSize;
2679:     // by Luhan
2680:     // LOG_W(MAC,
2681:     //       "-----------pusch_pdu->rnti is %d, pusch_pdu->bwp_size is %d, pusch_pdu->rb_size is %d \n",
2682:     //       pusch_pdu->rnti,
2683:     //       pusch_pdu->bwp_size,
2684:     //       pusch_pdu->rb_size);
2685:     pusch_pdu->vrb_to_prb_mapping = 0;
2686:     if (current_BWP->pusch_Config==NULL || current_BWP->pusch_Config->frequencyHopping==NULL)
2687:       pusch_pdu->frequency_hopping = 0;
2688:     else
2689:       pusch_pdu->frequency_hopping = 1;
2690: 
2691:     /* FAPI: Resource Allocation in time domain */
2692:     pusch_pdu->start_symbol_index = sched_pusch->tda_info.startSymbolIndex;
2693:     pusch_pdu->nr_of_symbols = sched_pusch->tda_info.nrOfSymbols;
2694: 
2695:     /* PUSCH PDU */
2696:     AssertFatal(cur_harq->round < nr_mac->ul_bler.harq_round_max, "Indexing nr_rv_round_map[%d] is out of bounds\n", cur_harq->round%4);
2697:     pusch_pdu->pusch_data.rv_index = nr_rv_round_map[cur_harq->round%4];
2698:     pusch_pdu->pusch_data.harq_process_id = harq_id;
2699:     pusch_pdu->pusch_data.new_data_indicator = (cur_harq->round == 0) ? 1 : 0;  // not NDI but indicator for new transmission
2700:     pusch_pdu->pusch_data.tb_size = sched_pusch->tb_size;
2701:     pusch_pdu->pusch_data.num_cb = 0; //CBG not supported
2702: 
2703:     // Beamforming
2704:     pusch_pdu->beamforming.num_prgs = 0;
2705:     pusch_pdu->beamforming.prg_size = 0; // bwp_size;
2706:     pusch_pdu->beamforming.dig_bf_interface = 1;
2707:     pusch_pdu->beamforming.prgs_list[0].dig_bf_interface_list[0].beam_idx = UE->UE_beam_index;
2708: 
2709:     pusch_pdu->maintenance_parms_v3.ldpcBaseGraph = get_BG(sched_pusch->tb_size<<3,sched_pusch->R);
2710: 
2711:     // Calacualte the normalized tx_power for PHR
2712:     long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2713:     int tbs_bits = pusch_pdu->pusch_data.tb_size << 3;
2714: 
2715:     sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2716:                                                       tbs_bits,
2717:                                                       sched_pusch->rbSize,
2718:                                                       sched_pusch->nrOfLayers,
2719:                                                       sched_pusch->tda_info.nrOfSymbols,
2720:                                                       sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2721:                                                       deltaMCS,
2722:                                                       false);
2723: 
2724:     NR_UE_ServingCell_Info_t *sc_info = &UE->sc_info;
2725:     if (sc_info->rateMatching_PUSCH) {
2726:       // TBS_LBRM according to section 5.4.2.1 of 38.212
2727:       long *maxMIMO_Layers = sc_info->maxMIMO_Layers_PUSCH;
2728:       if (!maxMIMO_Layers)
2729:         maxMIMO_Layers = current_BWP->pusch_Config->maxRank;
2730:       AssertFatal (maxMIMO_Layers != NULL,"Option with max MIMO layers not configured is not supported\n");
2731:       pusch_pdu->maintenance_parms_v3.tbSizeLbrmBytes =
2732:           nr_compute_tbslbrm(current_BWP->mcs_table, sc_info->ul_bw_tbslbrm, *maxMIMO_Layers);
2733:     } else
2734:       pusch_pdu->maintenance_parms_v3.tbSizeLbrmBytes = 0;
2735: 
2736:     LOG_D(NR_MAC,"PUSCH PDU : data_scrambling_identity %x, dmrs_scrambling_id %x\n",pusch_pdu->data_scrambling_id,pusch_pdu->ul_dmrs_scrambling_id);
2737:     /* TRANSFORM PRECODING --------------------------------------------------------*/
2738: 
2739:     if (pusch_pdu->transform_precoding == NR_PUSCH_Config__transformPrecoder_enabled){
2740: 
2741:       // U as specified in section 6.4.1.1.1.2 in 38.211, if sequence hopping and group hopping are disabled
2742:       pusch_pdu->dfts_ofdm.low_papr_group_number = pusch_pdu->pusch_identity % 30;
2743: 
2744:       // V as specified in section 6.4.1.1.1.2 in 38.211 V = 0 if sequence hopping and group hopping are disabled
2745:       if ((!NR_DMRS_UplinkConfig ||
2746:           !NR_DMRS_UplinkConfig->transformPrecodingEnabled ||
2747:           (!NR_DMRS_UplinkConfig->transformPrecodingEnabled->sequenceGroupHopping && !NR_DMRS_UplinkConfig->transformPrecodingEnabled->sequenceHopping)) &&
2748:           !scc->uplinkConfigCommon->initialUplinkBWP->pusch_ConfigCommon->choice.setup->groupHoppingEnabledTransformPrecoding)
2749:         pusch_pdu->dfts_ofdm.low_papr_sequence_number = 0;
2750:       else
2751:         AssertFatal(1==0,"Hopping mode is not supported in transform precoding\n");
2752: 
2753:       LOG_D(NR_MAC,"TRANSFORM PRECODING IS ENABLED. CDM groups: %d, U: %d MCS table: %d\n", pusch_pdu->num_dmrs_cdm_grps_no_data, pusch_pdu->dfts_ofdm.low_papr_group_number, current_BWP->mcs_table);
2754:     }
2755: 
2756:     /*-----------------------------------------------------------------------------*/
2757: 
2758:     /* PUSCH PTRS */
2759:     if (NR_DMRS_UplinkConfig && NR_DMRS_UplinkConfig->phaseTrackingRS != NULL) {
2760:       bool valid_ptrs_setup = false;
2761:       pusch_pdu->pusch_ptrs.ptrs_ports_list   = (nfapi_nr_ptrs_ports_t *) malloc(2*sizeof(nfapi_nr_ptrs_ports_t));
2762:       valid_ptrs_setup = set_ul_ptrs_values(NR_DMRS_UplinkConfig->phaseTrackingRS->choice.setup,
2763:                                             pusch_pdu->rb_size, pusch_pdu->mcs_index, pusch_pdu->mcs_table,
2764:                                             &pusch_pdu->pusch_ptrs.ptrs_freq_density,&pusch_pdu->pusch_ptrs.ptrs_time_density,
2765:                                             &pusch_pdu->pusch_ptrs.ptrs_ports_list->ptrs_re_offset,&pusch_pdu->pusch_ptrs.num_ptrs_ports,
2766:                                             &pusch_pdu->pusch_ptrs.ul_ptrs_power, pusch_pdu->nr_of_symbols);
2767:       if (valid_ptrs_setup==true) {
2768:         pusch_pdu->pdu_bit_map |= PUSCH_PDU_BITMAP_PUSCH_PTRS; // enable PUSCH PTRS
2769:       }
2770:     }
2771:     else{
2772:       pusch_pdu->pdu_bit_map &= ~PUSCH_PDU_BITMAP_PUSCH_PTRS; // disable PUSCH PTRS
2773:     }
2774: 
2775:     /* look up the PDCCH PDU for this BWP and CORESET. If it does not exist,
2776:      * create it */
2777:     NR_SearchSpace_t *ss = sched_ctrl->search_space;
2778:     NR_ControlResourceSet_t *coreset = sched_ctrl->coreset;
2779:     const int coresetid = coreset->controlResourceSetId;
2780:     nfapi_nr_dl_tti_pdcch_pdu_rel15_t *pdcch_pdu = pdcch_pdu_coreset[coresetid];
2781:     if (!pdcch_pdu) {
2782:       nfapi_nr_ul_dci_request_pdus_t *ul_dci_request_pdu = &ul_dci_req->ul_dci_pdu_list[ul_dci_req->numPdus];
2783:       memset(ul_dci_request_pdu, 0, sizeof(nfapi_nr_ul_dci_request_pdus_t));
2784:       ul_dci_request_pdu->PDUType = NFAPI_NR_DL_TTI_PDCCH_PDU_TYPE;
2785:       ul_dci_request_pdu->PDUSize = (uint8_t)(4+sizeof(nfapi_nr_dl_tti_pdcch_pdu));
2786:       pdcch_pdu = &ul_dci_request_pdu->pdcch_pdu.pdcch_pdu_rel15;
2787:       ul_dci_req->numPdus += 1;
2788:       nr_configure_pdcch(pdcch_pdu, coreset, &sched_ctrl->sched_pdcch, false);
2789:       pdcch_pdu_coreset[coresetid] = pdcch_pdu;
2790:     }
2791: 
2792:     LOG_D(NR_MAC,"Configuring ULDCI/PDCCH in %d.%d at CCE %d, rnti %04x\n", frame,slot,sched_ctrl->cce_index,rnti);
2793: 
2794:     /* Fill PDCCH DL DCI PDU */
2795:     nfapi_nr_dl_dci_pdu_t *dci_pdu = &pdcch_pdu->dci_pdu[pdcch_pdu->numDlDci];
2796:     pdcch_pdu->numDlDci++;
2797:     dci_pdu->RNTI = rnti;
2798:     if (coreset->pdcch_DMRS_ScramblingID &&
2799:         ss->searchSpaceType->present == NR_SearchSpace__searchSpaceType_PR_ue_Specific) {
2800:       dci_pdu->ScramblingId = *coreset->pdcch_DMRS_ScramblingID;
2801:       dci_pdu->ScramblingRNTI = rnti;
2802:     } else {
2803:       dci_pdu->ScramblingId = *scc->physCellId;
2804:       dci_pdu->ScramblingRNTI = 0;
2805:     }
2806:     dci_pdu->AggregationLevel = sched_ctrl->aggregation_level;
2807:     dci_pdu->CceIndex = sched_ctrl->cce_index;
2808:     dci_pdu->beta_PDCCH_1_0 = 0;
2809:     dci_pdu->powerControlOffsetSS = 1;
2810:     dci_pdu->precodingAndBeamforming.num_prgs = 0;
2811:     dci_pdu->precodingAndBeamforming.prg_size = 0;
2812:     dci_pdu->precodingAndBeamforming.dig_bf_interfaces = 1;
2813:     dci_pdu->precodingAndBeamforming.prgs_list[0].pm_idx = 0;
2814:     dci_pdu->precodingAndBeamforming.prgs_list[0].dig_bf_interface_list[0].beam_idx = UE->UE_beam_index;
2815: 
2816:     dci_pdu_rel15_t uldci_payload;
2817:     memset(&uldci_payload, 0, sizeof(uldci_payload));
2818:     if (current_BWP->dci_format == NR_UL_DCI_FORMAT_0_1)
2819:       LOG_D(NR_MAC_DCI,
2820:             "add ul dci harq %d for %d.%d %d.%d round %d\n",
2821:             harq_id,
2822:             frame,
2823:             slot,
2824:             sched_pusch->frame,
2825:             sched_pusch->slot,
2826:             sched_ctrl->ul_harq_processes[harq_id].round);
2827:     config_uldci(&UE->sc_info,
2828:                  pusch_pdu,
2829:                  &uldci_payload,
2830:                  &sched_ctrl->srs_feedback,
2831:                  tpmi,
2832:                  sched_pusch->time_domain_allocation,
2833:                  UE->UE_sched_ctrl.tpc0,
2834:                  cur_harq->ndi,
2835:                  current_BWP);
2836: 
2837:     // Reset TPC to 0 dB to not request new gain multiple times before computing new value for SNR
2838:     UE->UE_sched_ctrl.tpc0 = 1;
2839: 
2840:     fill_dci_pdu_rel15(&UE->sc_info,
2841:                        &UE->current_DL_BWP,
2842:                        current_BWP,
2843:                        dci_pdu,
2844:                        &uldci_payload,
2845:                        current_BWP->dci_format,
2846:                        TYPE_C_RNTI_,
2847:                        current_BWP->bwp_id,
2848:                        ss,
2849:                        coreset,
2850:                        UE->pdsch_HARQ_ACK_Codebook,
2851:                        nr_mac->cset0_bwp_size);
2852: 
2853:     memset(sched_pusch, 0, sizeof(*sched_pusch));
2854:   }
2855: }

(End of file - total 2855 lines)
</content>
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "ul_mcs_scan|rb_values|max_hcs",
  "path": "/home/bupt/wlh/ran"
}
```

**Output:**
```
Found 98 matches
/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c:
  Line 45:                                           uint8_t layers, uint16_t *rb_values,

  Line 68:       rb_values[num_values] = rb;

  Line 1960:     if (nrmac->ul_mcs_scan_enabled) {

  Line 1962:       if (nrmac->ul_mcs_scan_auto_sweep) {

  Line 1963:         uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;

  Line 1964:         uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);

  Line 1965:         uint8_t scan_start = nrmac->ul_mcs_scan_start;

  Line 1969:         uint32_t period = nrmac->ul_mcs_scan_period;

  Line 1970:         uint32_t cb_period = nrmac->ul_mcs_scan_cb_period;

  Line 1972:         if (nrmac->ul_mcs_scan_last_frame != frame) {

  Line 1973:           nrmac->ul_mcs_scan_last_frame = frame;

  Line 1975:           int mcs_index = nrmac->ul_mcs_scan_current_index;

  Line 1984:           nrmac->ul_mcs_scan_accum_frames++;

  Line 1985:           nrmac->ul_mcs_scan_cb_accum_frames++;

  Line 1987:           if (nrmac->ul_mcs_scan_accum_frames >= period) {

  Line 1988:             nrmac->ul_mcs_scan_accum_frames = 0;

  Line 1989:             nrmac->ul_mcs_scan_cb_progress[current_mcs] = nrmac->ul_mcs_scan_current_cb_index;

  Line 1990:             nrmac->ul_mcs_scan_current_index++;

  Line 1991:             if (nrmac->ul_mcs_scan_current_index >= mcs_range) {

  Line 1992:               nrmac->ul_mcs_scan_current_index = 0;

  Line 1994:             nrmac->ul_mcs_scan_cb_accum_frames = 0;

  Line 1998:         int mcs_index = nrmac->ul_mcs_scan_current_index;

  Line 2006:         if (nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs] == 0) {

  Line 2011:                                          nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],

  Line 2012:                                          &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);

  Line 2013:           nrmac->ul_mcs_scan_cb_progress[target_mcs] = 0;

  Line 2016:         nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];

  Line 2017:         nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];

  Line 2018:         memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 

  Line 2019:                sizeof(nrmac->ul_mcs_scan_rb_values));

  Line 2021:         if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {

  Line 2022:           nrmac->ul_mcs_scan_cb_accum_frames = 0;

  Line 2023:           if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {

  Line 2024:             nrmac->ul_mcs_scan_current_cb_index++;

  Line 2025:             nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;

  Line 2029:         uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;

  Line 2030:         uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;

  Line 2032:               frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);

  Line 2034:         target_mcs = nrmac->ul_mcs_scan_ref;

  Line 2241:     uint16_t max_hcs_rb_size;

  Line 2242:     if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {

  Line 2243:       uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;

  Line 2244:       max_hcs_rb_size = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;

  Line 2245:       if (max_hcs_rb_size < 5) max_hcs_rb_size = 5;

  Line 2246:       if (max_hcs_rb_size > 273) max_hcs_rb_size = 273;

  Line 2248:       max_hcs_rb_size = rand_in_range(10, 273);

  Line 2250:     // uint16_t max_hcs_rb_size = 150;

  Line 2254:     max_rbSize = min(max_rbSize, max_hcs_rb_size);


/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c:
  Line 1636:       RC.nrmac[j]->ul_mcs_scan_enabled = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_ENABLED_IDX].u8ptr);

  Line 1637:       RC.nrmac[j]->ul_mcs_scan_ref = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_REF_IDX].u8ptr);

  Line 1638:       RC.nrmac[j]->ul_mcs_scan_auto_sweep = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_AUTO_SWEEP_IDX].u8ptr);

  Line 1639:       RC.nrmac[j]->ul_mcs_scan_min_mcs = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_MIN_MCS_IDX].u8ptr);

  Line 1640:       RC.nrmac[j]->ul_mcs_scan_max_mcs = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_MAX_MCS_IDX].u8ptr);

  Line 1641:       RC.nrmac[j]->ul_mcs_scan_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_PERIOD_IDX].uptr);

  Line 1642:       RC.nrmac[j]->ul_mcs_scan_start = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_START_IDX].u8ptr);

  Line 1643:       RC.nrmac[j]->ul_mcs_scan_cb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX].uptr);

  Line 1644:       RC.nrmac[j]->ul_mcs_scan_current_cb_index = 0;

  Line 1645:       RC.nrmac[j]->ul_mcs_scan_cb_accum_frames = 0;

  Line 1646:       RC.nrmac[j]->ul_mcs_scan_max_cb = 0;

  Line 1647:       memset(RC.nrmac[j]->ul_mcs_scan_cb_progress, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_cb_progress));

  Line 1648:       memset(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs));

  Line 1649:       memset(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs));

  Line 1651:             RC.nrmac[j]->ul_mcs_scan_enabled, RC.nrmac[j]->ul_mcs_scan_ref, 

  Line 1652:             RC.nrmac[j]->ul_mcs_scan_auto_sweep, RC.nrmac[j]->ul_mcs_scan_min_mcs,

  Line 1653:             RC.nrmac[j]->ul_mcs_scan_max_mcs, RC.nrmac[j]->ul_mcs_scan_period,

  Line 1654:             RC.nrmac[j]->ul_mcs_scan_start, RC.nrmac[j]->ul_mcs_scan_cb_period);


/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h:
  Line 935:   bool ul_mcs_scan_enabled;

  Line 936:   uint8_t ul_mcs_scan_ref;

  Line 937:   bool ul_mcs_scan_auto_sweep;

  Line 938:   uint8_t ul_mcs_scan_min_mcs;

  Line 939:   uint8_t ul_mcs_scan_max_mcs;

  Line 940:   uint32_t ul_mcs_scan_period;

  Line 941:   uint8_t ul_mcs_scan_start;

  Line 942:   uint32_t ul_mcs_scan_accum_frames;

  Line 943:   uint8_t ul_mcs_scan_current_index;

  Line 944:   uint16_t ul_mcs_scan_last_frame;

  Line 945:   uint32_t ul_mcs_scan_cb_period;

  Line 946:   uint32_t ul_mcs_scan_cb_accum_frames;

  Line 947:   uint8_t ul_mcs_scan_current_cb_index;

  Line 948:   uint8_t ul_mcs_scan_max_cb;

  Line 949:   uint16_t ul_mcs_scan_rb_values[32];

  Line 950:   uint8_t ul_mcs_scan_cb_progress[29];

  Line 951:   uint8_t ul_mcs_scan_max_cb_per_mcs[29];

  Line 952:   uint16_t ul_mcs_scan_rb_values_per_mcs[29][32];


/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h:
  Line 80: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_ENABLED           "ul_mcs_scan_enabled"

  Line 81: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_REF               "ul_mcs_scan_ref"

  Line 82: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_AUTO_SWEEP        "ul_mcs_scan_auto_sweep"

  Line 83: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_MIN_MCS           "ul_mcs_scan_min_mcs"

  Line 84: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_MAX_MCS           "ul_mcs_scan_max_mcs"

  Line 85: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_PERIOD            "ul_mcs_scan_period"

  Line 86: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_START             "ul_mcs_scan_start"

  Line 87: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD         "ul_mcs_scan_cb_period"


/home/bupt/wlh/ran/gnb.sa.band78.fr1.273PRB.oxgrf.conf:
  Line 205:   ul_mcs_scan_enabled    = 1;    # 0=正常模式, 1=扫描模式

  Line 206:   # ul_mcs_scan_ref        = 15;   # 目标 MCS (0-28)

  Line 207:   ul_mcs_scan_auto_sweep = 1;    # 自动遍历

  Line 209:   ul_mcs_scan_min_mcs    = 5;    # 扫描最小MCS（默认0）

  Line 210:   ul_mcs_scan_max_mcs    = 28;   # 扫描最大MCS（默认28）

  Line 211:   ul_mcs_scan_period     = 1; # 每个MCS保持帧数（默认1000）


(Some paths were inaccessible and skipped)
```

---

## Assistant (Plan · glm-5 · 71.7s)

_Thinking:_

根据搜索结果，我找到了相关的功能代码。代码库中已经有了一个 MCS 扫描功能（ul_mcs_scan），这个功能通过配置参数来控制 RB 的遍历。

让我看看配置文件中的相关配置：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/gnb.sa.band78.fr1.273PRB.oxgrf.conf",
  "offset": 200,
  "limit": 30
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/gnb.sa.band78.fr1.273PRB.oxgrf.conf</path>
<type>file</type>
<content>
200:   pucch_TargetSNRx10          = 200;
201:   pusch_FailureThres          = 1000;
202:   ul_max_mcs                  = 28;
203:   ulsch_max_frame_inactivity  = 0;
204:    # === 新增扫描参数 ===
205:   ul_mcs_scan_enabled    = 1;    # 0=正常模式, 1=扫描模式
206:   # ul_mcs_scan_ref        = 15;   # 目标 MCS (0-28)
207:   ul_mcs_scan_auto_sweep = 1;    # 自动遍历
208:   # === 自动扫描范围参数 ===
209:   ul_mcs_scan_min_mcs    = 5;    # 扫描最小MCS（默认0）
210:   ul_mcs_scan_max_mcs    = 28;   # 扫描最大MCS（默认28）
211:   ul_mcs_scan_period     = 1; # 每个MCS保持帧数（默认1000）
212: }
213: );
214: 
215: L1s = (
216: {
217:   num_cc = 1;
218:   tr_n_preference = "local_mac";
219:   prach_dtx_threshold = 120;
220:   pucch0_dtx_threshold = 80;
221: }
222: );
223: 
224: RUs = (
225: {
226:   local_rf       = "yes"
227:   nb_tx          = 1
228:   nb_rx          = 1
229:   att_tx         = 0;

(Showing lines 200-229 of 291. Use offset=230 to continue.)
</content>
```

---

## Assistant (Plan · glm-5 · 67.8s)

_Thinking:_

现在我对代码有了清晰的了解。让我总结一下：

代码库中已经有一个完整的 MCS 扫描功能（`ul_mcs_scan`），这个功能包括：

1. **自动遍历功能 (`ul_mcs_scan_auto_sweep`)**：
   - 在 `gNB_scheduler_ulsch.c` 中第 1960-2033 行实现
   - 通过 `compute_rb_boundaries_for_mcs` 函数（第 43-74 行）计算不同 MCS 对应的 RB 边界值
   - 根据不同的 Code Block (CB) 数量来确定 RB 的边界值
   - 使用 `ul_mcs_scan_rb_values_per_mcs[29][32]` 存储每个 MCS 对应的 32 个 RB 边界值

2. **RB 替换逻辑**：
   - 在第 2242-2254 行，通过 `max_hcs_rb_size` 控制 RB 分配大小
   - 当 `ul_mcs_scan_enabled` 和 `ul_mcs_scan_auto_sweep` 启用时，会使用预先计算的 RB 边界值
   - 否则使用 `rand_in_range(10, 273)` 来随机选择 RB 大小

3. **配置参数**：
   - `ul_mcs_scan_enabled`: 启用扫描模式
   - `ul_mcs_scan_auto_sweep`: 自动遍历模式
   - `ul_mcs_scan_min_mcs`: 最小 MCS
   - `ul_mcs_scan_max_mcs`: 最大 MCS
   - `ul_mcs_scan_period`: 每个 MCS 保持的帧数
   - `ul_mcs_scan_start`: 开始 MCS
   - `ul_mcs_scan_cb_period`: CB 遍历周期

从配置文件 `gnb.sa.band78.fr1.273PRB.oxgrf.conf` 中可以看到，这个功能已经启用：
- `ul_mcs_scan_enabled = 1`
- `ul_mcs_scan_auto_sweep = 1`
- `ul_mcs_scan_min_mcs = 5`
- `ul_mcs_scan_max_mcs = 28`
- `ul_mcs_scan_period = 1` (每个 MCS 保持 1 帧)

所以，关于"手动替换 RB 用于遍历足够多的 RB"的代码已经写好了，有完整的功能实现。

是的，**代码已经写好了，有完整的功能实现**。

在 `gNB_scheduler_ulsch.c` 中实现了 `ul_mcs_scan` 自动扫描功能：

**核心实现位置：**
- **RB 边界计算函数**：`compute_rb_boundaries_for_mcs()` (第 43-74 行) — 根据 Code Block (CB) 数量计算 RB 边界值
- **MCS 扫描逻辑**：第 1960-2033 行 — 自动遍历不同 MCS 和 CB 组合
- **RB 分配控制**：第 2242-2254 行 — 使用 `max_hcs_rb_size` 控制分配的 RB 数量

**当前配置 (`gnb.sa.band78.fr1.273PRB.oxgrf.conf`)：**
```
ul_mcs_scan_enabled    = 1    # 启用扫描模式
ul_mcs_scan_auto_sweep = 1    # 自动遍历
ul_mcs_scan_min_mcs    = 5    # 最小 MCS
ul_mcs_scan_max_mcs    = 28   # 最大 MCS
ul_mcs_scan_period     = 1    # 每帧切换
```

功能会遍历 MCS 5-28，并根据 `compute_rb_boundaries_for_mcs()` 计算的 RB 边界值（对应不同 CB 数量）来分配 RB，覆盖从 5 到 273 的范围。

---

## User

nrmac->ul_mcs_scan_rb_values是一个静态数组吗？这是怎么设定里面值的？

---

## Assistant (Plan · glm-5 · 67.1s)

_Thinking:_

用户问的是 `nrmac->ul_mcs_scan_rb_values` 是不是静态数组，以及里面的值是怎么设定的。

让我分析一下代码：

1. 在 `nr_mac_gNB.h` 中定义：
```c
uint16_t ul_mcs_scan_rb_values[32];
```

这是一个大小为32的 uint16_t 数组，存储在 gNB_MAC_INST 结构体中，所以它不是静态数组，而是动态分配的结构体成员。

2. 值是如何设定的：
- 在 `gNB_scheduler_ulsch.c` 中，有一个函数 `compute_rb_boundaries_for_mcs()` (第43-74行)
- 这个函数遍历 RB 从 min_rb (5) 到 max_rb (273)，计算每个 RB 对应的 TBS 和 Code Block 数量
- 当 Code Block 数量变化时，记录该 RB 值到 `rb_values` 数组中
- 在第 2010-2012 行调用：
```c
compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,
                               nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],
                               &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);
```

3. 还有 `ul_mcs_scan_rb_values_per_mcs[29][32]` - 这是一个二维数组，为每个 MCS (0-28) 存储 RB 边界值

4. 在第 2018-2019 行：
```c
memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 
       sizeof(nrmac->ul_mcs_scan_rb_values));
```
这会把当前目标 MCS 对应的 RB 值复制到 `ul_mcs_scan_rb_values` 数组中。

所以总结：
- `ul_mcs_scan_rb_values` 是结构体中的数组成员（不是静态数组）
- 值通过 `compute_rb_boundaries_for_mcs()` 函数动态计算
- 基于 MCS、码率 R、调制阶数 Qm 等参数计算 TBS 和 CB 数量
- 当 CB 数量发生变化时记录 RB 边界值

让我查看相关代码来详细解释这个数组的工作机制：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h",
  "offset": 930,
  "limit": 30
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h</path>
<type>file</type>
<content>
930:   NR_Type0_PDCCH_CSS_config_t type0_PDCCH_CSS_config[64];
931: 
932:   bool first_MIB;
933:   NR_bler_options_t dl_bler;
934:   NR_bler_options_t ul_bler;
935:   bool ul_mcs_scan_enabled;
936:   uint8_t ul_mcs_scan_ref;
937:   bool ul_mcs_scan_auto_sweep;
938:   uint8_t ul_mcs_scan_min_mcs;
939:   uint8_t ul_mcs_scan_max_mcs;
940:   uint32_t ul_mcs_scan_period;
941:   uint8_t ul_mcs_scan_start;
942:   uint32_t ul_mcs_scan_accum_frames;
943:   uint8_t ul_mcs_scan_current_index;
944:   uint16_t ul_mcs_scan_last_frame;
945:   uint32_t ul_mcs_scan_cb_period;
946:   uint32_t ul_mcs_scan_cb_accum_frames;
947:   uint8_t ul_mcs_scan_current_cb_index;
948:   uint8_t ul_mcs_scan_max_cb;
949:   uint16_t ul_mcs_scan_rb_values[32];
950:   uint8_t ul_mcs_scan_cb_progress[29];
951:   uint8_t ul_mcs_scan_max_cb_per_mcs[29];
952:   uint16_t ul_mcs_scan_rb_values_per_mcs[29][32];
953:   uint8_t min_grant_prb;
954:   uint8_t min_grant_mcs;
955:   bool identity_pm;
956:   int precoding_matrix_size[NR_MAX_NB_LAYERS];
957:   int fapi_beam_index[MAX_NUM_OF_SSB];
958:   nr_mac_rrc_ul_if_t mac_rrc;
959:   f1_config_t f1_config;

(Showing lines 930-959 of 969. Use offset=960 to continue.)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 43,
  "limit": 35
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
43: static void compute_rb_boundaries_for_mcs(uint8_t mcs, uint16_t R, uint8_t Qm,
44:                                           uint16_t symbols, uint16_t dmrs,
45:                                           uint8_t layers, uint16_t *rb_values,
46:                                           uint8_t *max_cb)
47: {
48:   uint32_t Kcb_1 = 8448;
49:   uint32_t Kcb_2 = 3840;
50:   uint8_t num_values = 0;
51:   uint8_t last_cb = 0;
52:   uint16_t min_rb = 5;
53:   uint16_t max_rb = 273;
54:   
55:   for (uint16_t rb = min_rb; rb <= max_rb && num_values < 32; rb++) {
56:     uint32_t tbs_bits = nr_compute_tbs(Qm, R, rb, symbols, dmrs, 0, 0, layers);
57:     uint8_t BG = get_BG(tbs_bits, R);
58:     uint32_t Kcb = (BG == 1) ? Kcb_1 : Kcb_2;
59:     uint8_t num_cb;
60:     if (tbs_bits <= Kcb) {
61:       num_cb = 1;
62:     } else {
63:       num_cb = tbs_bits / (Kcb - 24);
64:       if ((Kcb - 24) * num_cb < tbs_bits)
65:         num_cb++;
66:     }
67:     if (num_cb != last_cb) {
68:       rb_values[num_values] = rb;
69:       num_values++;
70:       last_cb = num_cb;
71:     }
72:   }
73:   *max_cb = last_cb;
74: }
75: #include "LAYER2/NR_MAC_gNB/leaf_model_exported.h"
76: #include "LAYER2/NR_MAC_gNB/leaf_model_wrapper.h"
77: //#define SRS_IND_DEBUG

(Showing lines 43-77 of 2855. Use offset=78 to continue.)
</content>
```

---

## Assistant (Plan · glm-5 · 86.2s)

_Thinking:_

现在我清楚了整个机制。让我给用户解释：

1. `ul_mcs_scan_rb_values` 不是静态数组，它是 `gNB_MAC_INST` 结构体的成员，定义为 `uint16_t ul_mcs_scan_rb_values[32]`

2. 还有两个相关数组：
   - `ul_mcs_scan_rb_values_per_mcs[29][32]` - 二维数组，为每个 MCS 存储 RB 边界值
   - `ul_mcs_scan_max_cb_per_mcs[29]` - 每个 MCS 对应的最大 CB 数量

3. 值的设定方式：
   - 通过 `compute_rb_boundaries_for_mcs()` 函数动态计算
   - 遍历 RB 5-273，计算每个 RB 对应的 TBS 和 Code Block 数量
   - 当 CB 数量变化时，记录该 RB 值

4. 在调度时：
   - 首次遇到某个 MCS 时，调用 compute_rb_boundaries_for_mcs 计算并存储到 `ul_mcs_scan_rb_values_per_mcs[target_mcs]`
   - 然后通过 memcpy 复制到 `ul_mcs_scan_rb_values`
   - 根据 `ul_mcs_scan_current_cb_index` 选择对应的 RB 值

## 数组结构说明

**不是静态数组**，而是 `gNB_MAC_INST` 结构体的成员：

```c
// nr_mac_gNB.h 第 949-952 行
uint16_t ul_mcs_scan_rb_values[32];            // 当前使用的 RB 边界值
uint16_t ul_mcs_scan_rb_values_per_mcs[29][32]; // 每个MCS对应的RB边界值（预计算）
uint8_t  ul_mcs_scan_max_cb_per_mcs[29];        // 每个MCS对应的最大CB数量
```

---

## 值的设定流程

### 1. **动态计算** - `compute_rb_boundaries_for_mcs()` 函数（第43-74行）

核心逻辑：
```c
for (rb = 5; rb <= 273; rb++) {
    tbs_bits = nr_compute_tbs(Qm, R, rb, symbols, dmrs, ...);  // 计算TBS
    num_cb = 计算Code Block数量;  // 根据 Kcb (8448或3840)
    
    if (num_cb != last_cb) {      // 当CB数量变化时
        rb_values[num_values] = rb;  // 记录RB边界
        num_values++;
    }
}
```

**原理**：LDPC 编码时，TBS 会被分割成多个 Code Block。当 RB 增加时，TBS 增大，CB 数量随之变化。该函数记录每次 CB 数量变化时的 RB 值，这样就能覆盖不同的 CB 配置。

---

### 2. **首次使用时预计算**（第2006-2013行）

```c
if (nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs] == 0) {  // 还没计算过
    compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,
        nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],  // 存到per_mcs数组
        &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);
}
```

---

### 3. **复制到当前使用数组**（第2018-2019行）

```c
memcpy(nrmac->ul_mcs_scan_rb_values, 
       nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],
       sizeof(nrmac->ul_mcs_scan_rb_values));
```

---

### 4. **实际使用**（第2243-2244行）

```c
uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
max_hcs_rb_size = nrmac->ul_mcs_scan_rb_values[cb_idx];  // 取对应的RB值
```

---

## 示例（假设 MCS=10）

计算后 `ul_mcs_scan_rb_values` 可能包含：
| cb_idx | RB值 | CB数量 |
|--------|------|--------|
| 0 | 5 | 1 |
| 1 | ~15 | 2 |
| 2 | ~30 | 3 |
| ... | ... | ... |
| N | ~270 | max |

通过 `ul_mcs_scan_cb_period` 控制每隔多少帧切换下一个 CB 配置，从而遍历足够多的 RB 范围。

---

## User

ul_mcs_scan_cb_period也是需要在配置文件中指定的吗？

---

## Assistant (Plan · glm-5 · 99.8s)

_Thinking:_

用户问的是 `ul_mcs_scan_cb_period` 是否需要在配置文件中指定。让我查看一下配置文件和相关代码。

**Tool: grep**

**Input:**
```json
{
  "pattern": "ul_mcs_scan_cb_period"
}
```

**Output:**
```
Found 5 matches
/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c:
  Line 1970:         uint32_t cb_period = nrmac->ul_mcs_scan_cb_period;


/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c:
  Line 1643:       RC.nrmac[j]->ul_mcs_scan_cb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX].uptr);

  Line 1654:             RC.nrmac[j]->ul_mcs_scan_start, RC.nrmac[j]->ul_mcs_scan_cb_period);


/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h:
  Line 945:   uint32_t ul_mcs_scan_cb_period;


/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h:
  Line 87: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD         "ul_mcs_scan_cb_period"


(Some paths were inaccessible and skipped)
```

---

## Assistant (Plan · glm-5 · 44.0s)

_Thinking:_

是的，`ul_mcs_scan_cb_period` 也是在配置文件中指定的。让我看看参数定义。


**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "limit": 50,
  "offset": 70
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h</path>
<type>file</type>
<content>
70: #define CONFIG_STRING_MACRLC_DL_HARQ_ROUND_MAX             "dl_harq_round_max"
71: #define CONFIG_STRING_MACRLC_UL_HARQ_ROUND_MAX             "ul_harq_round_max"
72: #define CONFIG_STRING_MACRLC_MIN_GRANT_PRB                 "min_grant_prb"
73: #define CONFIG_STRING_MACRLC_MIN_GRANT_MCS                 "min_grant_mcs"
74: #define CONFIG_STRING_MACRLC_IDENTITY_PM                   "identity_precoding_matrix"
75: #define CONFIG_STRING_MACRLC_ANALOG_BEAMFORMING            "set_analog_beamforming"
76: #define CONFIG_STRING_MACRLC_BEAM_DURATION                 "beam_duration"
77: #define CONFIG_STRING_MACRLC_BEAMS_PERIOD                  "beams_per_period"
78: #define CONFIG_STRING_MACRLC_PUSCH_RSSI_THRESHOLD          "pusch_RSSI_Threshold"
79: #define CONFIG_STRING_MACRLC_PUCCH_RSSI_THRESHOLD          "pucch_RSSI_Threshold"
80: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_ENABLED           "ul_mcs_scan_enabled"
81: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_REF               "ul_mcs_scan_ref"
82: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_AUTO_SWEEP        "ul_mcs_scan_auto_sweep"
83: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_MIN_MCS           "ul_mcs_scan_min_mcs"
84: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_MAX_MCS           "ul_mcs_scan_max_mcs"
85: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_PERIOD            "ul_mcs_scan_period"
86: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_START             "ul_mcs_scan_start"
87: #define CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD         "ul_mcs_scan_cb_period"
88: 
89: #define HLP_MACRLC_UL_PRBBLACK "SNR threshold to decide whether a PRB will be blacklisted or not"
90: #define HLP_MACRLC_DL_BLER_UP "Upper threshold of BLER to decrease DL MCS"
91: #define HLP_MACRLC_DL_BLER_LO "Lower threshold of BLER to increase DL MCS"
92: #define HLP_MACRLC_DL_MAX_MCS "Maximum DL MCS that should be used"
93: #define HLP_MACRLC_UL_BLER_UP "Upper threshold of BLER to decrease UL MCS"
94: #define HLP_MACRLC_UL_BLER_LO "Lower threshold of BLER to increase UL MCS"
95: #define HLP_MACRLC_UL_MAX_MCS "Maximum UL MCS that should be used"
96: #define HLP_MACRLC_DL_HARQ_MAX "Maximum number of DL HARQ rounds"
97: #define HLP_MACRLC_UL_HARQ_MAX "Maximum number of UL HARQ rounds"
98: #define HLP_MACRLC_MIN_GRANT_PRB "Minimal Periodic ULSCH Grant PRBs"
99: #define HLP_MACRLC_MIN_GRANT_MCS "Minimal Periodic ULSCH Grant MCS"
100: #define HLP_MACRLC_IDENTITY_PM "Flag to use only identity matrix in DL precoding"
101: #define HLP_MACRLC_AB "Flag to enable analog beamforming"
102: #define HLP_MACRLC_BEAM_DURATION "number of consecutive slots for a given set of beams"
103: #define HLP_MACRLC_BEAMS_PERIOD "set of beams that can be simultaneously allocated in a period"
104: #define HLP_MACRLC_PUSCH_RSSI_THRESHOLD "Limits PUSCH TPC commands based on RSSI to prevent ADC railing. Value range [-1280, 0], unit 0.1 dBm/dBFS"
105: #define HLP_MACRLC_PUCCH_RSSI_THRESHOLD "Limits PUCCH TPC commands based on RSSI to prevent ADC railing. Value range [-1280, 0], unit 0.1 dBm/dBFS"
106: #define HLP_MACRLC_UL_MCS_SCAN_EN "Enable UL MCS scan mode: bypass BLER adaptive MCS, use fixed mcs_ref"
107: #define HLP_MACRLC_UL_MCS_SCAN_REF "Target MCS for UL scan mode (0-28) when auto_sweep=0"
108: #define HLP_MACRLC_UL_MCS_SCAN_SWEEP "Enable auto sweep: cycle through all MCS values periodically"
109: #define HLP_MACRLC_UL_MCS_SCAN_MIN "Minimum MCS for auto sweep (default 5)"
110: #define HLP_MACRLC_UL_MCS_SCAN_MAX "Maximum MCS for auto sweep (default 28)"
111: #define HLP_MACRLC_UL_MCS_SCAN_PERIOD "Number of frames to hold each MCS value in auto sweep (default 100)"
112: #define HLP_MACRLC_UL_MCS_SCAN_START "Starting MCS for auto sweep (default 9, scan from this value upward)"
113: #define HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD "Number of frames to hold each codeblock count before switching RB (default 20)"
114: 
115: /*-------------------------------------------------------------------------------------------------------------------------------------------------------*/
116: /*                                            MacRLC  configuration parameters                                                                           */
117: /*   optname                                            helpstr   paramflags    XXXptr              defXXXval                  type           numelt     */
118: /*-------------------------------------------------------------------------------------------------------------------------------------------------------*/
119: // clang-format off

(Showing lines 70-119 of 275. Use offset=120 to continue.)
</content>
```

---

## Assistant (Plan · glm-5 · 74.2s)

_Thinking:_

是的，`ul_mcs_scan_cb_period` 是需要在配置文件中指定的参数。从第113行可以看到帮助说明：
`HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD "Number of frames to hold each codeblock count before switching RB (default 20)"`
意思是"每个 Code Block 数量保持多少帧后才切换 RB（默认 20）"

我来看看配置文件是否已经有这个参数。

**是的，`ul_mcs_scan_cb_period` 需要在配置文件中指定**。

从参数定义可以看到（`MACRLC_nr_paramdef.h` 第87、113行）：
- 参数名：`ul_mcs_scan_cb_period`
- 含义：**每个 Code Block 数量保持多少帧后切换 RB**（默认值 20）

---

## 当前配置文件中未指定该参数

你的配置文件（第205-211行）只有：
```
ul_mcs_scan_enabled    = 1;
ul_mcs_scan_auto_sweep = 1;
ul_mcs_scan_min_mcs    = 5;
ul_mcs_scan_max_mcs    = 28;
ul_mcs_scan_period     = 1;
```

**缺少 `ul_mcs_scan_cb_period`**，会使用默认值（可能为 0 或未初始化）。

---

## 建议补充配置

如果你想让 RB 也快速遍历，可以在配置文件中添加：

```
ul_mcs_scan_cb_period  = 1;    # 每帧切换一次 CB 配置（即切换 RB）
```

这样配合 `ul_mcs_scan_period = 1`，就能每帧同时切换 MCS 和 CB/RB，实现密集采样。

---

## 扫描机制总结

| 参数 | 作用 | 你的配置 |
|------|------|---------|
| `ul_mcs_scan_period` | 每多少帧切换下一个 MCS | 1 |
| `ul_mcs_scan_cb_period` | 每多少帧切换下一个 CB/RB 边界 | **未配置（需添加）** |

两层遍历：
1. 外层：MCS 遍历（5→28）
2. 内层：每个 MCS 对应的不同 RB 边界（CB 数量变化点）

---

