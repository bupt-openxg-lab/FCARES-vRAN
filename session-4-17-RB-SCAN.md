# gNB_scheduler_ulsch RB遍历替换代码状态恢复

**Session ID:** ses_266d7b938ffePEtVeEu2wXBlB2
**Created:** 4/16/2026, 9:57:26 PM
**Updated:** 4/16/2026, 11:05:13 PM

---

## User

@session-ses_2697.md 从上次的对话中恢复记忆

---

## Assistant (Build · glm-5 · 34.0s)

_Thinking:_

用户要求从上次的对话中恢复记忆。让我查看这个session文件的内容，了解之前讨论的内容。

从文件内容可以看到，这是一个关于 `gNB_scheduler_ulsch` 中手动替换 RB 用于遍历足够多的 RB 的代码的讨论。文件显示：

1. 用户询问关于 `gNB_scheduler_ulsch` 中手动替换 RB 用于遍历足够多的 RB 的代码是否已经写好了
2. 助手搜索了相关代码，找到了 `gNB_scheduler_ulsch.c` 文件
3. 文件被读取但内容被截断了（显示到第1268行）

文件内容显示了该C文件的部分内容，包括：
- 文件头和许可证信息
- `compute_rb_boundaries_for_mcs` 函数（第43-74行）
- `rand_in_range` 函数（第82-87行）
- 其他多个函数如 `get_ul_tda`, `compute_ph_factor`, `nr_process_mac_pdu` 等

但是文件被截断了，我需要继续读取来了解完整的内容，特别是是否有手动替换RB的相关代码。

让我继续读取文件的剩余部分。

我看到了上次的对话记录。让我继续读取文件的剩余部分，了解完整情况。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 1269
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
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
2015:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
2016:         for(int i=0;i<nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];i++){
2017:           LOG_W(NR_MAC,"MCS %d CB %d RB %d\n", target_mcs, i, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs][i]);
2018:         }
2019:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
2020:         nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];
2021:         nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];
2022:         memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 
2023:                sizeof(nrmac->ul_mcs_scan_rb_values));
2024:         
2025:         if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {
2026:           nrmac->ul_mcs_scan_cb_accum_frames = 0;
2027:           if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {
2028:             nrmac->ul_mcs_scan_current_cb_index++;
2029:             nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;
2030:           }
2031:         }
2032:         
2033:         uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2034:         uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2035:         LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, cb_idx=%d/%d, rb=%d\n",
2036:               frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);
2037:       } else {
2038:         target_mcs = nrmac->ul_mcs_scan_ref;
2039:       }
2040:       sched_pusch->mcs = min(target_mcs, max_mcs);
2041:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2042:     } else if (bo->harq_round_max == 1) {
2043:       sched_pusch->mcs = max_mcs;
2044:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2045:     } else {
2046:       sched_pusch->mcs = get_mcs_from_bler(bo, stats, &sched_ctrl->ul_bler_stats, max_mcs, frame);
2047:       LOG_W(NR_MAC,"%d.%d starting mcs %d bleri %f,bo->max_mcs = %d\n", frame, slot, sched_pusch->mcs, sched_ctrl->ul_bler_stats.bler,bo->max_mcs);
2048:     }
2049:     // LOG_W(NR_MAC,"sched_pusch->mcs = %d",sched_pusch->mcs);
2050:     /* Schedule UE on SR or UL inactivity and no data (otherwise, will be scheduled
2051:      * based on data to transmit) */
2052:     if (B == 0 && do_sched) {
2053:       /* if no data, pre-allocate 5RB */
2054:       /* Find a free CCE */
2055:       int CCEIndex = get_cce_index(nrmac,
2056:                                    CC_id, slot, UE->rnti,
2057:                                    &sched_ctrl->aggregation_level,
2058:                                    dci_beam.idx,
2059:                                    sched_ctrl->search_space,
2060:                                    sched_ctrl->coreset,
2061:                                    &sched_ctrl->sched_pdcch,
2062:                                    false,
2063:                                    sched_ctrl->pdcch_cl_adjust);
2064:       if (CCEIndex < 0) {
2065:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI (BSR 0)\n", UE->rnti, frame, slot);
2066:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2067:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2068:         continue;
2069:       }
2070: 
2071:       sched_pusch->nrOfLayers = sched_ctrl->srs_feedback.ul_ri + 1;
2072:       sched_pusch->time_domain_allocation = get_ul_tda(nrmac, sched_frame, sched_slot);
2073:       sched_pusch->tda_info = get_ul_tda_info(current_BWP,
2074:                                               sched_ctrl->coreset->controlResourceSetId,
2075:                                               sched_ctrl->search_space->searchSpaceType->present,
2076:                                               TYPE_C_RNTI_,
2077:                                               sched_pusch->time_domain_allocation);
2078:       AssertFatal(sched_pusch->tda_info.valid_tda, "Invalid TDA from get_ul_tda_info\n");
2079:       sched_pusch->dmrs_info = get_ul_dmrs_params(scc, current_BWP, &sched_pusch->tda_info, sched_pusch->nrOfLayers);
2080: 
2081:       int rbStart = 0; // wrt BWP start
2082:       LOG_D(NR_MAC,
2083:             "Looking for min_rb %d RBs, starting at %d num_dmrs_cdm_grps_no_data %d\n",
2084:             min_rb,
2085:             rbStart,
2086:             sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data);
2087:       const uint32_t bwpSize = current_BWP->BWPSize;
2088:       const uint32_t bwpStart = current_BWP->BWPStart;
2089:       const uint16_t slbitmap = SL_to_bitmap(sched_pusch->tda_info.startSymbolIndex, sched_pusch->tda_info.nrOfSymbols);
2090:       while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
2091:         rbStart++;
2092:       if (rbStart + min_rb >= bwpSize) {
2093:         LOG_D(NR_MAC,
2094:               "[UE %04x][%4d.%2d] could not allocate continuous UL data: no resources (rbStart %d, min_rb %d, bwpSize %d)\n",
2095:               UE->rnti,
2096:               frame,
2097:               slot,
2098:               rbStart,
2099:               min_rb,
2100:               bwpSize);
2101:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2102:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2103:         continue;
2104:       }
2105: 
2106:       sched_ctrl->cce_index = CCEIndex;
2107:       fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam.idx);
2108: 
2109:       NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2110:       sched_pusch->mcs = min(nrmac->min_grant_mcs, sched_pusch->mcs);
2111:       update_ul_ue_R_Qm(sched_pusch->mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &sched_pusch->R, &sched_pusch->Qm);
2112:       sched_pusch->rbStart = rbStart;
2113:       sched_pusch->rbSize = min_rb;
2114:       sched_pusch->frame = sched_frame;
2115:       sched_pusch->slot = sched_slot;
2116:       sched_pusch->tb_size = nr_compute_tbs(sched_pusch->Qm,
2117:                                             sched_pusch->R,
2118:                                             sched_pusch->rbSize,
2119:                                             sched_pusch->tda_info.nrOfSymbols,
2120:                                             sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2121:                                             0, // nb_rb_oh
2122:                                             0,
2123:                                             sched_pusch->nrOfLayers) >> 3;
2124:       long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2125: 
2126:       sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2127:                                                         sched_pusch->tb_size << 3,
2128:                                                         sched_pusch->rbSize,
2129:                                                         sched_pusch->nrOfLayers,
2130:                                                         sched_pusch->tda_info.nrOfSymbols,
2131:                                                         sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2132:                                                         deltaMCS,
2133:                                                         false);
2134:       LOG_D(NR_MAC,
2135:             "pf_ul %d.%d UE %x Scheduling PUSCH (no data) nrb %d mcs %d tbs %d bits phr_txpower %d\n",
2136:             frame,
2137:             slot,
2138:             UE->rnti,
2139:             sched_pusch->rbSize,
2140:             sched_pusch->mcs,
2141:             sched_pusch->tb_size << 3,
2142:             sched_pusch->phr_txpower_calc);
2143: 
2144:       /* Mark the corresponding RBs as used */
2145:       n_rb_sched[beam.idx] -= sched_pusch->rbSize;
2146:       for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
2147:         rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= slbitmap;
2148: 
2149:       remainUEs[beam.idx]--;
2150:       continue;
2151:     }
2152: 
2153:     /* Create UE_sched for UEs eligibale for new data transmission*/
2154:     /* Calculate coefficient*/
2155:     const uint32_t tbs = ul_pf_tbs[current_BWP->mcs_table][sched_pusch->mcs];
2156:     float coeff_ue = (float) tbs / UE->ul_thr_ue;
2157:     LOG_D(NR_MAC, "[UE %04x][%4d.%2d] b %d, ul_thr_ue %f, tbs %d, coeff_ue %f\n",
2158:           UE->rnti,
2159:           frame,
2160:           slot,
2161:           b,
2162:           UE->ul_thr_ue,
2163:           tbs,
2164:           coeff_ue);
2165:     UE_sched[curUE].coef = coeff_ue;
2166:     UE_sched[curUE].UE = UE;
2167:     curUE++;
2168:   }
2169: 
2170:   qsort(UE_sched, sizeofArray(UE_sched), sizeof(UEsched_t), comparator);
2171:   UEsched_t *iterator=UE_sched;
2172: 
2173:   /* Loop UE_sched to find max coeff and allocate transmission */
2174:   while (iterator->UE != NULL) {
2175:     NR_UE_UL_BWP_t *current_BWP = &iterator->UE->current_UL_BWP;
2176:     NR_UE_sched_ctrl_t *sched_ctrl = &iterator->UE->UE_sched_ctrl;
2177:     NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2178: 
2179:     NR_beam_alloc_t beam = beam_allocation_procedure(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame);
2180:     if (beam.idx < 0) {
2181:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", iterator->UE->rnti, frame, slot);
2182:       iterator++;
2183:       continue;
2184:     }
2185: 
2186:     if (remainUEs[beam.idx] == 0 || n_rb_sched[beam.idx] < min_rb) {
2187:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2188:       iterator++;
2189:       continue;
2190:     }
2191: 
2192:     NR_beam_alloc_t dci_beam = beam_allocation_procedure(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame);
2193:     if (dci_beam.idx < 0) {
2194:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] Beam could not be allocated\n", iterator->UE->rnti, frame, slot);
2195:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2196:       iterator++;
2197:       continue;
2198:     }
2199: 
2200:     int CCEIndex = get_cce_index(nrmac,
2201:                                  CC_id, slot, iterator->UE->rnti,
2202:                                  &sched_ctrl->aggregation_level,
2203:                                  dci_beam.idx,
2204:                                  sched_ctrl->search_space,
2205:                                  sched_ctrl->coreset,
2206:                                  &sched_ctrl->sched_pdcch,
2207:                                  false,
2208:                                  sched_ctrl->pdcch_cl_adjust);
2209: 
2210:     if (CCEIndex < 0) {
2211:       reset_beam_status(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2212:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2213:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI\n", iterator->UE->rnti, frame, slot);
2214:       iterator++;
2215:       continue;
2216:     }
2217:     else
2218:       LOG_D(NR_MAC, "%4d.%2d free CCE for UL DCI UE %04x\n", frame, slot, iterator->UE->rnti);
2219: 
2220: 
2221: 
2222:     sched_pusch->nrOfLayers = sched_ctrl->srs_feedback.ul_ri + 1;
2223:     sched_pusch->time_domain_allocation = get_ul_tda(nrmac, sched_frame, sched_slot);
2224:     sched_pusch->tda_info = get_ul_tda_info(current_BWP,
2225:                                             sched_ctrl->coreset->controlResourceSetId,
2226:                                             sched_ctrl->search_space->searchSpaceType->present,
2227:                                             TYPE_C_RNTI_,
2228:                                             sched_pusch->time_domain_allocation);
2229:     AssertFatal(sched_pusch->tda_info.valid_tda, "Invalid TDA from get_ul_tda_info\n");
2230:     sched_pusch->dmrs_info = get_ul_dmrs_params(scc, current_BWP, &sched_pusch->tda_info, sched_pusch->nrOfLayers);
2231: 
2232:     const int index = ul_buffer_index(sched_frame, sched_slot, slots_per_frame, nrmac->vrb_map_UL_size);
2233:     uint16_t *rballoc_mask = &nrmac->common_channels[CC_id].vrb_map_UL[beam.idx][index * MAX_BWP_SIZE];
2234: 
2235:     int rbStart = 0;
2236:     const uint16_t slbitmap = SL_to_bitmap(sched_pusch->tda_info.startSymbolIndex, sched_pusch->tda_info.nrOfSymbols);
2237:     const uint32_t bwpSize = current_BWP->BWPSize;
2238:     const uint32_t bwpStart = current_BWP->BWPStart;
2239:     // LOG_W(PHY,"bwpsize = %d,bwpstart = %d",bwpSize,bwpStart);
2240:     while (rbStart < bwpSize && (rballoc_mask[rbStart + bwpStart] & slbitmap))
2241:       rbStart++;
2242:   
2243:     sched_pusch->rbStart = rbStart;
2244:     uint16_t max_rbSize = 1;
2245:     uint16_t max_hcs_rb_size;
2246:     if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {
2247:       uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2248:       max_hcs_rb_size = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2249:       if (max_hcs_rb_size < 5) max_hcs_rb_size = 5;
2250:       if (max_hcs_rb_size > 273) max_hcs_rb_size = 273;
2251:     } else {
2252:       max_hcs_rb_size = rand_in_range(10, 273);
2253:     }
2254:     // uint16_t max_hcs_rb_size = 150;
2255:     while (rbStart + max_rbSize < bwpSize && !(rballoc_mask[rbStart + bwpStart + max_rbSize] & slbitmap)){
2256:             max_rbSize++;
2257:     }
2258:     max_rbSize = min(max_rbSize, max_hcs_rb_size);
2259:     
2260:     // double prediction =  LeafModelExported_predict_runtime_cost_p70(sched_pusch->mcs, sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2261:     // int best_prb = select_prb(sched_pusch->mcs,sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2262:     LOG_W(PHY,"max_rbSize = %hd\n",max_rbSize);
2263:     // LOG_W(PHY,"max_rbSize = %hd,prediction = %f\n",max_rbSize,prediction);
2264:     // max_rbSize = best_prb;
2265:       //by Luhan
2266:     // LOG_W(MAC,"---------------by Luhan, max_rbSize is %d, slot is %d, sched_slot is %d \n",max_rbSize, slot,sched_slot);
2267:     
2268:     if (rbStart + min_rb >= bwpSize || max_rbSize < min_rb) {
2269:       reset_beam_status(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2270:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2271:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] could not allocate UL data: no resources (rbStart %d, min_rb %d, bwpSize %d)\n",
2272:             iterator->UE->rnti,
2273:             frame,
2274:             slot,
2275:             rbStart,
2276:             min_rb,
2277:             bwpSize);
2278:       iterator++;
2279:       continue;
2280:     } else
2281:       LOG_D(NR_MAC,
2282:             "allocating UL data for RNTI %04x (rbStart %d, min_rb %d, max_rbSize %d, bwpSize %d)\n",
2283:             iterator->UE->rnti,
2284:             rbStart,
2285:             min_rb,
2286:             max_rbSize,
2287:             bwpSize);
2288: 
2289:     /* Calculate the current scheduling bytes */
2290:     const int B = cmax(sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes, 0);
2291:     /* adjust rbSize and MCS according to PHR and BPRE */
2292:     if(sched_ctrl->pcmax != 0 || sched_ctrl->ph != 0) // verify if the PHR related parameter have been initialized
2293:       nr_ue_max_mcs_min_rb(current_BWP->scs, sched_ctrl->ph, sched_pusch, current_BWP, min_rb, B, &max_rbSize, &sched_pusch->mcs);
2294:     
2295:     if (sched_pusch->mcs < sched_ctrl->ul_bler_stats.mcs)
2296:     sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs; /* force estimated MCS down */
2297: 
2298:     update_ul_ue_R_Qm(sched_pusch->mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &sched_pusch->R, &sched_pusch->Qm);
2299:     uint16_t rbSize = 0;
2300:     uint32_t TBS = 0;
2301:     nr_find_nb_rb(sched_pusch->Qm,
2302:                   sched_pusch->R,
2303:                   current_BWP->transform_precoding,
2304:                   sched_pusch->nrOfLayers,
2305:                   sched_pusch->tda_info.nrOfSymbols,
2306:                   sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2307:                   B,
2308:                   min_rb,
2309:                   max_rbSize,
2310:                   &TBS,
2311:                   &rbSize);
2312: 
2313:     // Calacualte the normalized tx_power for PHR
2314:     long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2315:     int tbs_bits = TBS << 3;
2316: 
2317:     sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2318:                                                       tbs_bits,
2319:                                                       rbSize,
2320:                                                       sched_pusch->nrOfLayers,
2321:                                                       sched_pusch->tda_info.nrOfSymbols,
2322:                                                       sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2323:                                                       deltaMCS,
2324:                                                       false);
2325: 
2326:     sched_pusch->rbSize = rbSize;
2327:     sched_pusch->tb_size = TBS;
2328:     sched_pusch->frame = sched_frame;
2329:     sched_pusch->slot = sched_slot;
2330:     uint32_t B_bits = sched_pusch->tb_size << 3;
2331:     uint8_t BG = get_BG(B_bits, sched_pusch->R);
2332:     uint32_t Kcb = (BG == 1) ? 8448 : 3840;
2333:     uint32_t num_cb;
2334:     if (B_bits <= Kcb) {
2335:       num_cb = 1;
2336:     } else {
2337:       num_cb = B_bits / (Kcb - 24);
2338:       if ((Kcb - 24) * num_cb < B_bits)
2339:         num_cb++;
2340:     }
2341:     LOG_W(NR_MAC,
2342:           "rbSize %d (max_rbSize %d), TBS %d, est buf %d, sched_ul %d, B %d, CCE %d, num_dmrs_symb %d, N_PRB_DMRS %d, BG=%d, num_cb=%d\n",
2343:           rbSize,
2344:           max_rbSize,
2345:           sched_pusch->tb_size,
2346:           sched_ctrl->estimated_ul_buffer,
2347:           sched_ctrl->sched_ul_bytes,
2348:           B,
2349:           sched_ctrl->cce_index,
2350:           sched_pusch->dmrs_info.num_dmrs_symb,
2351:           sched_pusch->dmrs_info.N_PRB_DMRS,
2352:           BG,
2353:           num_cb);
2354: 
2355:     /* Mark the corresponding RBs as used */
2356: 
2357:     sched_ctrl->cce_index = CCEIndex;
2358:     fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam.idx);
2359: 
2360:     n_rb_sched[beam.idx] -= sched_pusch->rbSize;
2361:     for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
2362:       rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= slbitmap;
2363: 
2364:     /* reduce max_num_ue once we are sure UE can be allocated, i.e., has CCE */
2365:     remainUEs[beam.idx]--;
2366:     iterator++;
2367:   }
2368: }
2369: 
2370: static bool nr_ulsch_preprocessor(module_id_t module_id, frame_t frame, sub_frame_t slot)
2371: {

(Output capped at 50 KB. Showing lines 1269-2371. Use offset=2372 to continue.)
</content>
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "手动|替换|RB.*遍历|rb.*replace|manual.*rb",
  "path": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB",
  "include": "*.c"
}
```

**Output:**
```
No files found
```

---

## Assistant (Build · glm-5 · 27.8s)

_Thinking:_

我现在看到了更多的代码内容。让我继续查看文件的剩余部分，并且搜索是否有关于手动替换RB的相关配置参数或功能。

从代码中我可以看到：

1. 有 `ul_mcs_scan_enabled` 和 `ul_mcs_scan_auto_sweep` 相关的逻辑
2. `compute_rb_boundaries_for_mcs` 函数用于计算每个MCS对应的RB边界值
3. 有 `ul_mcs_scan_rb_values_per_mcs` 存储每个MCS的RB值
4. `ul_mcs_scan_current_cb_index` 用于跟踪当前的CB索引

这看起来是已经实现了一个MCS扫描系统，会自动遍历不同的MCS和对应的RB值。让我继续查看文件的剩余部分，以及查看gNB_MAC_INST结构体定义来了解这些参数。

让我继续查看文件剩余部分和相关结构体定义：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 2372
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
2372:   gNB_MAC_INST *nr_mac = RC.nrmac[module_id];
2373:   // no UEs
2374:   if (nr_mac->UE_info.list[0] == NULL)
2375:     return false;
2376: 
2377:   NR_COMMON_channels_t *cc = nr_mac->common_channels;
2378:   NR_ServingCellConfigCommon_t *scc = cc->ServingCellConfigCommon;
2379:   const NR_SIB1_t *sib1 = nr_mac->common_channels[0].sib1 ? nr_mac->common_channels[0].sib1->message.choice.c1->choice.systemInformationBlockType1 : NULL;
2380:   NR_ServingCellConfigCommonSIB_t *scc_sib1 = sib1 ? sib1->servingCellConfigCommon : NULL;
2381:   AssertFatal(scc || scc_sib1, "We need one serving cell config common\n");
2382:   const int slots_frame = nr_mac->frame_structure.numb_slots_frame;
2383:   // TODO we assume the same K2 for all UEs
2384:   const int K2 = nr_mac->radio_config.minRXTXTIME + get_NTN_Koffset(scc);
2385:   const int sched_frame = (frame + (slot + K2) / slots_frame) % MAX_FRAME_NUMBER;
2386:   const int sched_slot = (slot + K2) % slots_frame;
2387:   //by Luhan
2388:   // LOG_W(MAC, "----in nr_ulsch_preprossor, frame is %d, sched_slot is %d , K2 is %d, slot is %d \n", frame, sched_slot, K2,slot);
2389: 
2390:   if (!is_ul_slot(sched_slot, &nr_mac->frame_structure))
2391:   {
2392:     //  LOG_W(MAC, "----in nr_ulsch_preprossor, sched_slot is %d , IS NOT UL \n",sched_slot);
2393:     return false;
2394:   }
2395:     
2396: 
2397:   int num_beams = nr_mac->beam_info.beam_allocation ? nr_mac->beam_info.beams_per_period : 1;
2398:   int bw = scc->uplinkConfigCommon->frequencyInfoUL->scs_SpecificCarrierList.list.array[0]->carrierBandwidth;
2399:   int len[num_beams];
2400:   for (int i = 0; i < num_beams; i++)
2401:     len[i] = bw;
2402: 
2403:   int average_agg_level = 4; // TODO find a better estimation
2404:   int max_sched_ues = bw / (average_agg_level * NR_NB_REG_PER_CCE);
2405: 
2406:   // FAPI cannot handle more than MAX_DCI_CORESET DCIs
2407:   max_sched_ues = min(max_sched_ues, MAX_DCI_CORESET);
2408: 
2409:   /* proportional fair scheduling algorithm */
2410:   pf_ul(module_id, frame, slot, sched_frame, sched_slot, nr_mac->UE_info.list, max_sched_ues, num_beams, len);
2411:   return true;
2412: }
2413: 
2414: nr_pp_impl_ul nr_init_ulsch_preprocessor(int CC_id)
2415: {
2416:   /* during initialization: no mutex needed */
2417:   /* in the PF algorithm, we have to use the TBsize to compute the coefficient.
2418:    * This would include the number of DMRS symbols, which in turn depends on
2419:    * the time domain allocation. In case we are in a mixed slot, we do not want
2420:    * to recalculate all these values, and therefore we provide a look-up table
2421:    * which should approximately(!) give us the TBsize. In particular, the
2422:    * number of symbols, the number of DMRS symbols, and the exact Qm and R, are
2423:    * not correct*/
2424:   for (int mcsTableIdx = 0; mcsTableIdx < 5; ++mcsTableIdx) {
2425:     for (int mcs = 0; mcs < 29; ++mcs) {
2426:       if (mcs > 27 && (mcsTableIdx == 1 || mcsTableIdx == 3 || mcsTableIdx == 4))
2427:         continue;
2428:       const uint8_t Qm = nr_get_Qm_ul(mcs, mcsTableIdx);
2429:       const uint16_t R = nr_get_code_rate_ul(mcs, mcsTableIdx);
2430:       /* note: we do not update R/Qm based on low MCS or pi2BPSK */
2431:       ul_pf_tbs[mcsTableIdx][mcs] = nr_compute_tbs(Qm,
2432:                                                    R,
2433:                                                    1, /* rbSize */
2434:                                                    10, /* hypothetical number of slots */
2435:                                                    0, /* N_PRB_DMRS * N_DMRS_SLOT */
2436:                                                    0 /* N_PRB_oh, 0 for initialBWP */,
2437:                                                    0 /* tb_scaling */,
2438:                                                    1 /* nrOfLayers */)
2439:                                     >> 3;
2440:     }
2441:   }
2442:   return nr_ulsch_preprocessor;
2443: }
2444: 
2445: void nr_schedule_ulsch(module_id_t module_id, frame_t frame, sub_frame_t slot, nfapi_nr_ul_dci_request_t *ul_dci_req)
2446: {
2447:   gNB_MAC_INST *nr_mac = RC.nrmac[module_id];
2448:   /* already mutex protected: held in gNB_dlsch_ulsch_scheduler() */
2449:   NR_SCHED_ENSURE_LOCKED(&nr_mac->sched_lock);
2450: 
2451:   /* Uplink data ONLY can be scheduled when the current slot is downlink slot,
2452:    * because we have to schedule the DCI0 first before schedule uplink data */
2453:   //by Luhan
2454:   // LOG_W(NR_MAC, "!!!!!!Current slot %d is slot\n",slot);
2455:   if (!is_dl_slot(slot, &nr_mac->frame_structure)) {
2456:     // LOG_W(NR_MAC, "!!!!!!Current slot %d is NOT DL slot, cannot schedule DCI0 for UL data\n", slot);
2457:     return;
2458:   }
2459:   bool do_sched = nr_mac->pre_processor_ul(module_id, frame, slot);
2460:   if (!do_sched)
2461:   {
2462:     // LOG_W(NR_MAC, "!!!!!!Cannot schedule uplink, current dl slot is %d\n",slot);
2463:     return;
2464:   }
2465:     
2466: 
2467:   ul_dci_req->SFN = frame;
2468:   ul_dci_req->Slot = slot;
2469:   /* a PDCCH PDU groups DCIs per BWP and CORESET. Save a pointer to each
2470:    * allocated PDCCH so we can easily allocate UE's DCIs independent of any
2471:    * CORESET order */
2472:   nfapi_nr_dl_tti_pdcch_pdu_rel15_t *pdcch_pdu_coreset[MAX_NUM_CORESET] = {0};
2473: 
2474: 
2475:   NR_ServingCellConfigCommon_t *scc = nr_mac->common_channels[0].ServingCellConfigCommon;
2476:   NR_UEs_t *UE_info = &nr_mac->UE_info;
2477:   UE_iterator( UE_info->list, UE) {
2478:     NR_UE_sched_ctrl_t *sched_ctrl = &UE->UE_sched_ctrl;
2479:     if (sched_ctrl->ul_failure && !get_softmodem_params()->phy_test)
2480:       continue;
2481: 
2482:     NR_UE_UL_BWP_t *current_BWP = &UE->current_UL_BWP;
2483: 
2484:     UE->mac_stats.ul.current_bytes = 0;
2485:     UE->mac_stats.ul.current_rbs = 0;
2486: 
2487:     /* dynamic PUSCH values (RB alloc, MCS, hence R, Qm, TBS) that change in
2488:      * every TTI are pre-populated by the preprocessor and used below */
2489:     NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2490:     LOG_D(NR_MAC,"UE %04x : sched_pusch->rbSize %d\n",UE->rnti,sched_pusch->rbSize);
2491:     if (sched_pusch->rbSize <= 0)
2492:       continue;
2493: 
2494:     uint16_t rnti = UE->rnti;
2495:     sched_ctrl->SR = false;
2496:     int *tpmi = NULL;
2497: 
2498:     int8_t harq_id = sched_pusch->ul_harq_pid;
2499:     if (harq_id < 0) {
2500:       /* PP has not selected a specific HARQ Process, get a new one */
2501:       harq_id = sched_ctrl->available_ul_harq.head;
2502:       AssertFatal(harq_id >= 0,
2503:                   "no free HARQ process available for UE %04x\n",
2504:                   UE->rnti);
2505:       remove_front_nr_list(&sched_ctrl->available_ul_harq);
2506:       sched_pusch->ul_harq_pid = harq_id;
2507:     } else {
2508:       /* PP selected a specific HARQ process. Check whether it will be a new
2509:        * transmission or a retransmission, and remove from the corresponding
2510:        * list */
2511:       if (sched_ctrl->ul_harq_processes[harq_id].round == 0)
2512:         remove_nr_list(&sched_ctrl->available_ul_harq, harq_id);
2513:       else
2514:         remove_nr_list(&sched_ctrl->retrans_ul_harq, harq_id);
2515:     }
2516:     NR_UE_ul_harq_t *cur_harq = &sched_ctrl->ul_harq_processes[harq_id];
2517:     DevAssert(!cur_harq->is_waiting);
2518:     if (nr_mac->radio_config.disable_harq) {
2519:       finish_nr_ul_harq(sched_ctrl, harq_id);
2520:     } else {
2521:       add_tail_nr_list(&sched_ctrl->feedback_ul_harq, harq_id);
2522:       cur_harq->feedback_slot = sched_pusch->slot;
2523:       cur_harq->is_waiting = true;
2524:     }
2525: 
2526:     /* Statistics */
2527:     AssertFatal(cur_harq->round < nr_mac->ul_bler.harq_round_max, "Indexing ulsch_rounds[%d] is out of bounds\n", cur_harq->round);
2528:     UE->mac_stats.ul.rounds[cur_harq->round]++;
2529:     if (cur_harq->round == 0) {
2530:       UE->mac_stats.ulsch_total_bytes_scheduled += sched_pusch->tb_size;
2531:       /* Save information on MCS, TBS etc for the current initial transmission
2532:        * so we have access to it when retransmitting */
2533:       cur_harq->sched_pusch = *sched_pusch;
2534:       /* save which time allocation and nrOfLayers have been used, to be used on
2535:        * retransmissions */
2536:       cur_harq->sched_pusch.time_domain_allocation = sched_pusch->time_domain_allocation;
2537:       cur_harq->sched_pusch.nrOfLayers = sched_pusch->nrOfLayers;
2538:       cur_harq->sched_pusch.tpmi = sched_pusch->tpmi;
2539:       sched_ctrl->sched_ul_bytes += sched_pusch->tb_size;
2540:       UE->mac_stats.ul.total_rbs += sched_pusch->rbSize;
2541: 
2542:     } else {
2543:       LOG_D(NR_MAC,
2544:             "%d.%2d UL retransmission RNTI %04x sched %d.%2d HARQ PID %d round %d NDI %d\n",
2545:             frame,
2546:             slot,
2547:             rnti,
2548:             sched_pusch->frame,
2549:             sched_pusch->slot,
2550:             harq_id,
2551:             cur_harq->round,
2552:             cur_harq->ndi);
2553:       UE->mac_stats.ul.total_rbs_retx += sched_pusch->rbSize;
2554:     }
2555:     UE->mac_stats.ul.current_bytes = sched_pusch->tb_size;
2556:     UE->mac_stats.ul.current_rbs = sched_pusch->rbSize;
2557:     sched_ctrl->last_ul_frame = sched_pusch->frame;
2558:     sched_ctrl->last_ul_slot = sched_pusch->slot;
2559: 
2560:     LOG_W(NR_MAC,
2561:           "ULSCH/PUSCH: %4d.%2d RNTI %04x UL sched %4d.%2d DCI L %d start %2d RBS %3d startSymbol %2d nb_symbol %2d dmrs_pos %x MCS Table %2d MCS %2d nrOfLayers %2d num_dmrs_cdm_grps_no_data %2d TBS %4d HARQ PID %2d round %d RV %d NDI %d est %6d sched %6d est BSR %6d TPC %d\n",
2562:           frame,
2563:           slot,
2564:           rnti,
2565:           sched_pusch->frame,
2566:           sched_pusch->slot,
2567:           sched_ctrl->aggregation_level,
2568:           sched_pusch->rbStart,
2569:           sched_pusch->rbSize,
2570:           sched_pusch->tda_info.startSymbolIndex,
2571:           sched_pusch->tda_info.nrOfSymbols,
2572:           sched_pusch->dmrs_info.ul_dmrs_symb_pos,
2573:           current_BWP->mcs_table,
2574:           sched_pusch->mcs,
2575:           sched_pusch->nrOfLayers,
2576:           sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data,
2577:           sched_pusch->tb_size,
2578:           harq_id,
2579:           cur_harq->round,
2580:           nr_rv_round_map[cur_harq->round%4],
2581:           cur_harq->ndi,
2582:           sched_ctrl->estimated_ul_buffer,
2583:           sched_ctrl->sched_ul_bytes,
2584:           sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes,
2585:           sched_ctrl->tpc0);
2586: 
2587:     /* PUSCH in a later slot, but corresponding DCI now! */
2588:     const int index = ul_buffer_index(sched_pusch->frame,
2589:                                       sched_pusch->slot,
2590:                                       nr_mac->frame_structure.numb_slots_frame,
2591:                                       nr_mac->UL_tti_req_ahead_size);
2592:     nfapi_nr_ul_tti_request_t *future_ul_tti_req = &nr_mac->UL_tti_req_ahead[0][index];
2593:     if (future_ul_tti_req->SFN != sched_pusch->frame || future_ul_tti_req->Slot != sched_pusch->slot)
2594:       LOG_W(NR_MAC,
2595:             "%d.%d future UL_tti_req's frame.slot %d.%d does not match PUSCH %d.%d\n",
2596:             frame, slot,
2597:             future_ul_tti_req->SFN,
2598:             future_ul_tti_req->Slot,
2599:             sched_pusch->frame,
2600:             sched_pusch->slot);
2601:     AssertFatal(future_ul_tti_req->n_pdus <
2602:                 sizeof(future_ul_tti_req->pdus_list) / sizeof(future_ul_tti_req->pdus_list[0]),
2603:                 "Invalid future_ul_tti_req->n_pdus %d\n", future_ul_tti_req->n_pdus);
2604: 
2605:     future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pdu_type = NFAPI_NR_UL_CONFIG_PUSCH_PDU_TYPE;
2606:     future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pdu_size = sizeof(nfapi_nr_pusch_pdu_t);
2607:     nfapi_nr_pusch_pdu_t *pusch_pdu = &future_ul_tti_req->pdus_list[future_ul_tti_req->n_pdus].pusch_pdu;
2608:     memset(pusch_pdu, 0, sizeof(nfapi_nr_pusch_pdu_t));
2609:     future_ul_tti_req->n_pdus += 1;
2610: 
2611:     LOG_D(NR_MAC,
2612:           "%4d.%2d Scheduling UE specific PUSCH for sched %d.%d, ul_tti_req %d.%d\n",
2613:           frame,
2614:           slot,
2615:           sched_pusch->frame,
2616:           sched_pusch->slot,
2617:           future_ul_tti_req->SFN,
2618:           future_ul_tti_req->Slot);
2619: 
2620:     pusch_pdu->pdu_bit_map = PUSCH_PDU_BITMAP_PUSCH_DATA;
2621:     pusch_pdu->rnti = rnti;
2622:     pusch_pdu->handle = 0; //not yet used
2623: 
2624:     /* FAPI: BWP */
2625: 
2626:     pusch_pdu->bwp_size  = current_BWP->BWPSize;
2627:     pusch_pdu->bwp_start = current_BWP->BWPStart;
2628:     pusch_pdu->subcarrier_spacing = current_BWP->scs;
2629:     pusch_pdu->cyclic_prefix = 0;
2630: 
2631:     /* FAPI: PUSCH information always included */
2632:     pusch_pdu->target_code_rate = sched_pusch->R;
2633:     pusch_pdu->qam_mod_order = sched_pusch->Qm;
2634:     pusch_pdu->mcs_index = sched_pusch->mcs;
2635:     pusch_pdu->mcs_table = current_BWP->mcs_table;
2636:     pusch_pdu->transform_precoding = current_BWP->transform_precoding;
2637:     if (current_BWP->pusch_Config && current_BWP->pusch_Config->dataScramblingIdentityPUSCH)
2638:       pusch_pdu->data_scrambling_id = *current_BWP->pusch_Config->dataScramblingIdentityPUSCH;
2639:     else
2640:       pusch_pdu->data_scrambling_id = *scc->physCellId;
2641:     pusch_pdu->nrOfLayers = sched_pusch->nrOfLayers;
2642:     // If nrOfLayers is the same as in srs_feedback, we use the best TPMI, i.e. the one in srs_feedback.
2643:     // Otherwise, we use the valid TPMI that we saved in the first transmission.
2644:     if (pusch_pdu->nrOfLayers != (sched_ctrl->srs_feedback.ul_ri + 1))
2645:       tpmi = &sched_pusch->tpmi;
2646:     pusch_pdu->num_dmrs_cdm_grps_no_data = sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data;
2647: 
2648:     /* FAPI: DMRS */
2649:     pusch_pdu->num_dmrs_cdm_grps_no_data = sched_pusch->dmrs_info.num_dmrs_cdm_grps_no_data;
2650:     pusch_pdu->dmrs_ports = ((1<<sched_pusch->nrOfLayers) - 1);
2651:     pusch_pdu->ul_dmrs_symb_pos = sched_pusch->dmrs_info.ul_dmrs_symb_pos;
2652:     pusch_pdu->dmrs_config_type = sched_pusch->dmrs_info.dmrs_config_type;
2653:     pusch_pdu->scid = 0;      // DMRS sequence initialization [TS38.211, sec 6.4.1.1.1]
2654:     const NR_DMRS_UplinkConfig_t *NR_DMRS_UplinkConfig = get_DMRS_UplinkConfig(current_BWP->pusch_Config, &sched_pusch->tda_info);
2655:     if (pusch_pdu->transform_precoding) { // transform precoding disabled
2656:       long *scramblingid=NULL;
2657:       pusch_pdu->pusch_identity = *scc->physCellId;
2658:       if (NR_DMRS_UplinkConfig && pusch_pdu->scid == 0)
2659:         scramblingid = NR_DMRS_UplinkConfig->transformPrecodingDisabled->scramblingID0;
2660:       else if (NR_DMRS_UplinkConfig)
2661:         scramblingid = NR_DMRS_UplinkConfig->transformPrecodingDisabled->scramblingID1;
2662:       if (scramblingid == NULL)
2663:         pusch_pdu->ul_dmrs_scrambling_id = *scc->physCellId;
2664:       else
2665:         pusch_pdu->ul_dmrs_scrambling_id = *scramblingid;
2666:     }
2667:     else {
2668:       pusch_pdu->ul_dmrs_scrambling_id = *scc->physCellId;
2669:       if (NR_DMRS_UplinkConfig &&
2670:           NR_DMRS_UplinkConfig->transformPrecodingEnabled &&
2671:           NR_DMRS_UplinkConfig->transformPrecodingEnabled->nPUSCH_Identity != NULL)
2672:         pusch_pdu->pusch_identity = *NR_DMRS_UplinkConfig->transformPrecodingEnabled->nPUSCH_Identity;
2673:       else if (NR_DMRS_UplinkConfig)
2674:         pusch_pdu->pusch_identity = *scc->physCellId;
2675:     }
2676:     pusch_pdu->scid = 0;      // DMRS sequence initialization [TS38.211, sec 6.4.1.1.1]
2677:     pusch_pdu->dmrs_ports = ((1<<sched_pusch->nrOfLayers) - 1);
2678: 
2679:     /* FAPI: Pusch Allocation in frequency domain */
2680:     pusch_pdu->resource_alloc = 1; //type 1
2681:     pusch_pdu->rb_start = sched_pusch->rbStart;
2682:     pusch_pdu->rb_size = sched_pusch->rbSize;
2683:     // by Luhan
2684:     // LOG_W(MAC,
2685:     //       "-----------pusch_pdu->rnti is %d, pusch_pdu->bwp_size is %d, pusch_pdu->rb_size is %d \n",
2686:     //       pusch_pdu->rnti,
2687:     //       pusch_pdu->bwp_size,
2688:     //       pusch_pdu->rb_size);
2689:     pusch_pdu->vrb_to_prb_mapping = 0;
2690:     if (current_BWP->pusch_Config==NULL || current_BWP->pusch_Config->frequencyHopping==NULL)
2691:       pusch_pdu->frequency_hopping = 0;
2692:     else
2693:       pusch_pdu->frequency_hopping = 1;
2694: 
2695:     /* FAPI: Resource Allocation in time domain */
2696:     pusch_pdu->start_symbol_index = sched_pusch->tda_info.startSymbolIndex;
2697:     pusch_pdu->nr_of_symbols = sched_pusch->tda_info.nrOfSymbols;
2698: 
2699:     /* PUSCH PDU */
2700:     AssertFatal(cur_harq->round < nr_mac->ul_bler.harq_round_max, "Indexing nr_rv_round_map[%d] is out of bounds\n", cur_harq->round%4);
2701:     pusch_pdu->pusch_data.rv_index = nr_rv_round_map[cur_harq->round%4];
2702:     pusch_pdu->pusch_data.harq_process_id = harq_id;
2703:     pusch_pdu->pusch_data.new_data_indicator = (cur_harq->round == 0) ? 1 : 0;  // not NDI but indicator for new transmission
2704:     pusch_pdu->pusch_data.tb_size = sched_pusch->tb_size;
2705:     pusch_pdu->pusch_data.num_cb = 0; //CBG not supported
2706: 
2707:     // Beamforming
2708:     pusch_pdu->beamforming.num_prgs = 0;
2709:     pusch_pdu->beamforming.prg_size = 0; // bwp_size;
2710:     pusch_pdu->beamforming.dig_bf_interface = 1;
2711:     pusch_pdu->beamforming.prgs_list[0].dig_bf_interface_list[0].beam_idx = UE->UE_beam_index;
2712: 
2713:     pusch_pdu->maintenance_parms_v3.ldpcBaseGraph = get_BG(sched_pusch->tb_size<<3,sched_pusch->R);
2714: 
2715:     // Calacualte the normalized tx_power for PHR
2716:     long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2717:     int tbs_bits = pusch_pdu->pusch_data.tb_size << 3;
2718: 
2719:     sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2720:                                                       tbs_bits,
2721:                                                       sched_pusch->rbSize,
2722:                                                       sched_pusch->nrOfLayers,
2723:                                                       sched_pusch->tda_info.nrOfSymbols,
2724:                                                       sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2725:                                                       deltaMCS,
2726:                                                       false);
2727: 
2728:     NR_UE_ServingCell_Info_t *sc_info = &UE->sc_info;
2729:     if (sc_info->rateMatching_PUSCH) {
2730:       // TBS_LBRM according to section 5.4.2.1 of 38.212
2731:       long *maxMIMO_Layers = sc_info->maxMIMO_Layers_PUSCH;
2732:       if (!maxMIMO_Layers)
2733:         maxMIMO_Layers = current_BWP->pusch_Config->maxRank;
2734:       AssertFatal (maxMIMO_Layers != NULL,"Option with max MIMO layers not configured is not supported\n");
2735:       pusch_pdu->maintenance_parms_v3.tbSizeLbrmBytes =
2736:           nr_compute_tbslbrm(current_BWP->mcs_table, sc_info->ul_bw_tbslbrm, *maxMIMO_Layers);
2737:     } else
2738:       pusch_pdu->maintenance_parms_v3.tbSizeLbrmBytes = 0;
2739: 
2740:     LOG_D(NR_MAC,"PUSCH PDU : data_scrambling_identity %x, dmrs_scrambling_id %x\n",pusch_pdu->data_scrambling_id,pusch_pdu->ul_dmrs_scrambling_id);
2741:     /* TRANSFORM PRECODING --------------------------------------------------------*/
2742: 
2743:     if (pusch_pdu->transform_precoding == NR_PUSCH_Config__transformPrecoder_enabled){
2744: 
2745:       // U as specified in section 6.4.1.1.1.2 in 38.211, if sequence hopping and group hopping are disabled
2746:       pusch_pdu->dfts_ofdm.low_papr_group_number = pusch_pdu->pusch_identity % 30;
2747: 
2748:       // V as specified in section 6.4.1.1.1.2 in 38.211 V = 0 if sequence hopping and group hopping are disabled
2749:       if ((!NR_DMRS_UplinkConfig ||
2750:           !NR_DMRS_UplinkConfig->transformPrecodingEnabled ||
2751:           (!NR_DMRS_UplinkConfig->transformPrecodingEnabled->sequenceGroupHopping && !NR_DMRS_UplinkConfig->transformPrecodingEnabled->sequenceHopping)) &&
2752:           !scc->uplinkConfigCommon->initialUplinkBWP->pusch_ConfigCommon->choice.setup->groupHoppingEnabledTransformPrecoding)
2753:         pusch_pdu->dfts_ofdm.low_papr_sequence_number = 0;
2754:       else
2755:         AssertFatal(1==0,"Hopping mode is not supported in transform precoding\n");
2756: 
2757:       LOG_D(NR_MAC,"TRANSFORM PRECODING IS ENABLED. CDM groups: %d, U: %d MCS table: %d\n", pusch_pdu->num_dmrs_cdm_grps_no_data, pusch_pdu->dfts_ofdm.low_papr_group_number, current_BWP->mcs_table);
2758:     }
2759: 
2760:     /*-----------------------------------------------------------------------------*/
2761: 
2762:     /* PUSCH PTRS */
2763:     if (NR_DMRS_UplinkConfig && NR_DMRS_UplinkConfig->phaseTrackingRS != NULL) {
2764:       bool valid_ptrs_setup = false;
2765:       pusch_pdu->pusch_ptrs.ptrs_ports_list   = (nfapi_nr_ptrs_ports_t *) malloc(2*sizeof(nfapi_nr_ptrs_ports_t));
2766:       valid_ptrs_setup = set_ul_ptrs_values(NR_DMRS_UplinkConfig->phaseTrackingRS->choice.setup,
2767:                                             pusch_pdu->rb_size, pusch_pdu->mcs_index, pusch_pdu->mcs_table,
2768:                                             &pusch_pdu->pusch_ptrs.ptrs_freq_density,&pusch_pdu->pusch_ptrs.ptrs_time_density,
2769:                                             &pusch_pdu->pusch_ptrs.ptrs_ports_list->ptrs_re_offset,&pusch_pdu->pusch_ptrs.num_ptrs_ports,
2770:                                             &pusch_pdu->pusch_ptrs.ul_ptrs_power, pusch_pdu->nr_of_symbols);
2771:       if (valid_ptrs_setup==true) {
2772:         pusch_pdu->pdu_bit_map |= PUSCH_PDU_BITMAP_PUSCH_PTRS; // enable PUSCH PTRS
2773:       }
2774:     }
2775:     else{
2776:       pusch_pdu->pdu_bit_map &= ~PUSCH_PDU_BITMAP_PUSCH_PTRS; // disable PUSCH PTRS
2777:     }
2778: 
2779:     /* look up the PDCCH PDU for this BWP and CORESET. If it does not exist,
2780:      * create it */
2781:     NR_SearchSpace_t *ss = sched_ctrl->search_space;
2782:     NR_ControlResourceSet_t *coreset = sched_ctrl->coreset;
2783:     const int coresetid = coreset->controlResourceSetId;
2784:     nfapi_nr_dl_tti_pdcch_pdu_rel15_t *pdcch_pdu = pdcch_pdu_coreset[coresetid];
2785:     if (!pdcch_pdu) {
2786:       nfapi_nr_ul_dci_request_pdus_t *ul_dci_request_pdu = &ul_dci_req->ul_dci_pdu_list[ul_dci_req->numPdus];
2787:       memset(ul_dci_request_pdu, 0, sizeof(nfapi_nr_ul_dci_request_pdus_t));
2788:       ul_dci_request_pdu->PDUType = NFAPI_NR_DL_TTI_PDCCH_PDU_TYPE;
2789:       ul_dci_request_pdu->PDUSize = (uint8_t)(4+sizeof(nfapi_nr_dl_tti_pdcch_pdu));
2790:       pdcch_pdu = &ul_dci_request_pdu->pdcch_pdu.pdcch_pdu_rel15;
2791:       ul_dci_req->numPdus += 1;
2792:       nr_configure_pdcch(pdcch_pdu, coreset, &sched_ctrl->sched_pdcch, false);
2793:       pdcch_pdu_coreset[coresetid] = pdcch_pdu;
2794:     }
2795: 
2796:     LOG_D(NR_MAC,"Configuring ULDCI/PDCCH in %d.%d at CCE %d, rnti %04x\n", frame,slot,sched_ctrl->cce_index,rnti);
2797: 
2798:     /* Fill PDCCH DL DCI PDU */
2799:     nfapi_nr_dl_dci_pdu_t *dci_pdu = &pdcch_pdu->dci_pdu[pdcch_pdu->numDlDci];
2800:     pdcch_pdu->numDlDci++;
2801:     dci_pdu->RNTI = rnti;
2802:     if (coreset->pdcch_DMRS_ScramblingID &&
2803:         ss->searchSpaceType->present == NR_SearchSpace__searchSpaceType_PR_ue_Specific) {
2804:       dci_pdu->ScramblingId = *coreset->pdcch_DMRS_ScramblingID;
2805:       dci_pdu->ScramblingRNTI = rnti;
2806:     } else {
2807:       dci_pdu->ScramblingId = *scc->physCellId;
2808:       dci_pdu->ScramblingRNTI = 0;
2809:     }
2810:     dci_pdu->AggregationLevel = sched_ctrl->aggregation_level;
2811:     dci_pdu->CceIndex = sched_ctrl->cce_index;
2812:     dci_pdu->beta_PDCCH_1_0 = 0;
2813:     dci_pdu->powerControlOffsetSS = 1;
2814:     dci_pdu->precodingAndBeamforming.num_prgs = 0;
2815:     dci_pdu->precodingAndBeamforming.prg_size = 0;
2816:     dci_pdu->precodingAndBeamforming.dig_bf_interfaces = 1;
2817:     dci_pdu->precodingAndBeamforming.prgs_list[0].pm_idx = 0;
2818:     dci_pdu->precodingAndBeamforming.prgs_list[0].dig_bf_interface_list[0].beam_idx = UE->UE_beam_index;
2819: 
2820:     dci_pdu_rel15_t uldci_payload;
2821:     memset(&uldci_payload, 0, sizeof(uldci_payload));
2822:     if (current_BWP->dci_format == NR_UL_DCI_FORMAT_0_1)
2823:       LOG_D(NR_MAC_DCI,
2824:             "add ul dci harq %d for %d.%d %d.%d round %d\n",
2825:             harq_id,
2826:             frame,
2827:             slot,
2828:             sched_pusch->frame,
2829:             sched_pusch->slot,
2830:             sched_ctrl->ul_harq_processes[harq_id].round);
2831:     config_uldci(&UE->sc_info,
2832:                  pusch_pdu,
2833:                  &uldci_payload,
2834:                  &sched_ctrl->srs_feedback,
2835:                  tpmi,
2836:                  sched_pusch->time_domain_allocation,
2837:                  UE->UE_sched_ctrl.tpc0,
2838:                  cur_harq->ndi,
2839:                  current_BWP);
2840: 
2841:     // Reset TPC to 0 dB to not request new gain multiple times before computing new value for SNR
2842:     UE->UE_sched_ctrl.tpc0 = 1;
2843: 
2844:     fill_dci_pdu_rel15(&UE->sc_info,
2845:                        &UE->current_DL_BWP,
2846:                        current_BWP,
2847:                        dci_pdu,
2848:                        &uldci_payload,
2849:                        current_BWP->dci_format,
2850:                        TYPE_C_RNTI_,
2851:                        current_BWP->bwp_id,
2852:                        ss,
2853:                        coreset,
2854:                        UE->pdsch_HARQ_ACK_Codebook,
2855:                        nr_mac->cset0_bwp_size);
2856: 
2857:     memset(sched_pusch, 0, sizeof(*sched_pusch));
2858:   }
2859: }

(End of file - total 2859 lines)
</content>
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "ul_mcs_scan",
  "include": "*.h"
}
```

**Output:**
```
Found 26 matches
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

```

---

## Assistant (Build · glm-5 · 65.3s)

_Thinking:_

现在我有了完整的上下文。根据session文件和代码内容，我可以看到：

**已经实现的功能：**

1. **MCS扫描功能** (`ul_mcs_scan_enabled`, `ul_mcs_scan_auto_sweep`)：已经在代码中实现
2. **RB遍历功能**：
   - `compute_rb_boundaries_for_mcs()` 函数（第43-74行）计算每个MCS对应的RB边界值
   - `ul_mcs_scan_rb_values_per_mcs[29][32]` 存储每个MCS的32个RB边界值
   - `ul_mcs_scan_cb_period` 控制CB（Code Block）遍历周期
   - `ul_mcs_scan_current_cb_index` 跟踪当前CB索引

3. **配置参数**（在 `MACRLC_nr_paramdef.h` 中）：
   - `ul_mcs_scan_enabled` - 启用MCS扫描
   - `ul_mcs_scan_auto_sweep` - 自动扫描模式
   - `ul_mcs_scan_min_mcs` / `ul_mcs_scan_max_mcs` - MCS范围
   - `ul_mcs_scan_period` - MCS切换周期（帧数）
   - `ul_mcs_scan_cb_period` - CB（RB）切换周期（帧数）
   - `ul_mcs_scan_start` - 起始MCS

4. **工作原理**（在 `pf_ul` 函数中，约1960-2036行）：
   - 系统自动遍历不同MCS值
   - 对于每个MCS，计算不同CB数量对应的RB边界
   - 每隔`ul_mcs_scan_period`帧切换MCS
   - 每隔`ul_mcs_scan_cb_period`帧切换RB值（在同一MCS内遍历不同CB边界）

这个功能**已经完整实现**。代码会：
1. 根据配置的MCS范围自动遍历
2. 对每个MCS计算并遍历不同CB数量对应的RB值
3. 在调度时使用计算出的RB值（约2248-2258行）

让我给用户一个简洁的总结。

根据上次对话的记录和代码分析，**RB遍历功能已经完整实现**。

## 已实现的功能

### 1. 核心函数
- `compute_rb_boundaries_for_mcs()` (gNB_scheduler_ulsch.c:43-74) - 计算每个MCS对应的RB边界值

### 2. 配置参数 (可在配置文件中设置)
| 参数 | 说明 |
|------|------|
| `ul_mcs_scan_enabled` | 启用MCS扫描 |
| `ul_mcs_scan_auto_sweep` | 自动遍历模式 |
| `ul_mcs_scan_min_mcs` / `max_mcs` | MCS范围 (默认0-28) |
| `ul_mcs_scan_period` | MCS切换周期(帧数) |
| `ul_mcs_scan_cb_period` | CB/RB切换周期(帧数) |
| `ul_mcs_scan_start` | 起始MCS值 |

### 3. 工作机制
- 系统自动遍历配置范围内的MCS值
- 对每个MCS，计算32个RB边界值(对应不同CB数量)
- 定期切换RB值以遍历足够多的RB组合
- 日志输出：`UL MCS SWEEP: mcs=X, cb_idx=Y, rb=Z`

### 4. 代码位置
- RB选择逻辑: `gNB_scheduler_ulsch.c:2246-2258`
- MCS遍历逻辑: `gNB_scheduler_ulsch.c:1960-2036`

功能已可用，只需在配置文件中启用相关参数即可使用。

---

## User

为什么一个作用域中定义两个NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;也不会报错？在pf_ul的UE_iterator(UE_list,UE)中。)

---

## Assistant (Build · glm-5 · 46.3s)

_Thinking:_

用户问的是在 `pf_ul` 函数中，为什么在 `UE_iterator(UE_list, UE)` 循环内定义了两次 `NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;` 却不会报错。

让我回顾代码，在 pf_ul 函数中：

第一次出现在循环开始处（大约1866行附近）：
```c
UE_iterator(UE_list, UE) {
    ...
    NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
    ...
}
```

第二次出现在处理 B == 0 && do_sched 的情况时（大约2109行）：
```c
if (B == 0 && do_sched) {
    ...
    NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
    ...
}
```

这不会报错的原因是：
1. 它们在不同的作用域中
2. 内层的 `sched_pusch` 会遮蔽（shadow）外层的 `sched_pusch`

让我确认一下代码结构。

这是C语言的**变量遮蔽（shadowing）**规则，不会报错但可能有隐患。

让我指出具体位置：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 1864,
  "limit": 80
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
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

(Showing lines 1864-1943 of 2859. Use offset=1944 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 25.3s)

_Thinking:_

让我看第二次定义的位置，大约在2109行附近

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "limit": 50,
  "offset": 2100
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
2100:               bwpSize);
2101:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2102:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2103:         continue;
2104:       }
2105: 
2106:       sched_ctrl->cce_index = CCEIndex;
2107:       fill_pdcch_vrb_map(nrmac, CC_id, &sched_ctrl->sched_pdcch, CCEIndex, sched_ctrl->aggregation_level, dci_beam.idx);
2108: 
2109:       NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;
2110:       sched_pusch->mcs = min(nrmac->min_grant_mcs, sched_pusch->mcs);
2111:       update_ul_ue_R_Qm(sched_pusch->mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &sched_pusch->R, &sched_pusch->Qm);
2112:       sched_pusch->rbStart = rbStart;
2113:       sched_pusch->rbSize = min_rb;
2114:       sched_pusch->frame = sched_frame;
2115:       sched_pusch->slot = sched_slot;
2116:       sched_pusch->tb_size = nr_compute_tbs(sched_pusch->Qm,
2117:                                             sched_pusch->R,
2118:                                             sched_pusch->rbSize,
2119:                                             sched_pusch->tda_info.nrOfSymbols,
2120:                                             sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2121:                                             0, // nb_rb_oh
2122:                                             0,
2123:                                             sched_pusch->nrOfLayers) >> 3;
2124:       long *deltaMCS = current_BWP->pusch_Config ? current_BWP->pusch_Config->pusch_PowerControl->deltaMCS : NULL;
2125: 
2126:       sched_pusch->phr_txpower_calc = compute_ph_factor(current_BWP->scs,
2127:                                                         sched_pusch->tb_size << 3,
2128:                                                         sched_pusch->rbSize,
2129:                                                         sched_pusch->nrOfLayers,
2130:                                                         sched_pusch->tda_info.nrOfSymbols,
2131:                                                         sched_pusch->dmrs_info.N_PRB_DMRS * sched_pusch->dmrs_info.num_dmrs_symb,
2132:                                                         deltaMCS,
2133:                                                         false);
2134:       LOG_D(NR_MAC,
2135:             "pf_ul %d.%d UE %x Scheduling PUSCH (no data) nrb %d mcs %d tbs %d bits phr_txpower %d\n",
2136:             frame,
2137:             slot,
2138:             UE->rnti,
2139:             sched_pusch->rbSize,
2140:             sched_pusch->mcs,
2141:             sched_pusch->tb_size << 3,
2142:             sched_pusch->phr_txpower_calc);
2143: 
2144:       /* Mark the corresponding RBs as used */
2145:       n_rb_sched[beam.idx] -= sched_pusch->rbSize;
2146:       for (int rb = bwpStart; rb < sched_ctrl->sched_pusch.rbSize; rb++)
2147:         rballoc_mask[rb + sched_ctrl->sched_pusch.rbStart] |= slbitmap;
2148: 
2149:       remainUEs[beam.idx]--;

(Showing lines 2100-2149 of 2859. Use offset=2150 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 38.2s)

_Thinking:_

现在我看到了，让我检查一下这是在哪个 if 块内：

第一次定义在 1873 行，在 UE_iterator 的外层作用域

第二次定义在 2109 行，应该是在某个 if 块内部

让我确认这个 if 块的上下文。

让我查看第2109行所在的if块结构：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "limit": 30,
  "offset": 2050
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
2050:     /* Schedule UE on SR or UL inactivity and no data (otherwise, will be scheduled
2051:      * based on data to transmit) */
2052:     if (B == 0 && do_sched) {
2053:       /* if no data, pre-allocate 5RB */
2054:       /* Find a free CCE */
2055:       int CCEIndex = get_cce_index(nrmac,
2056:                                    CC_id, slot, UE->rnti,
2057:                                    &sched_ctrl->aggregation_level,
2058:                                    dci_beam.idx,
2059:                                    sched_ctrl->search_space,
2060:                                    sched_ctrl->coreset,
2061:                                    &sched_ctrl->sched_pdcch,
2062:                                    false,
2063:                                    sched_ctrl->pdcch_cl_adjust);
2064:       if (CCEIndex < 0) {
2065:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI (BSR 0)\n", UE->rnti, frame, slot);
2066:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2067:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2068:         continue;
2069:       }
2070: 
2071:       sched_pusch->nrOfLayers = sched_ctrl->srs_feedback.ul_ri + 1;
2072:       sched_pusch->time_domain_allocation = get_ul_tda(nrmac, sched_frame, sched_slot);
2073:       sched_pusch->tda_info = get_ul_tda_info(current_BWP,
2074:                                               sched_ctrl->coreset->controlResourceSetId,
2075:                                               sched_ctrl->search_space->searchSpaceType->present,
2076:                                               TYPE_C_RNTI_,
2077:                                               sched_pusch->time_domain_allocation);
2078:       AssertFatal(sched_pusch->tda_info.valid_tda, "Invalid TDA from get_ul_tda_info\n");
2079:       sched_pusch->dmrs_info = get_ul_dmrs_params(scc, current_BWP, &sched_pusch->tda_info, sched_pusch->nrOfLayers);

(Showing lines 2050-2079 of 2859. Use offset=2080 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 44.0s)

_Thinking:_

现在我明白了代码结构：

```c
UE_iterator(UE_list, UE) {                        // 外层作用域
    NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;  // 第1次定义 (1873行)
    
    // ... 代码 ...
    
    if (B == 0 && do_sched) {                     // 内层 if 块作用域
        // 第2071行使用了外层的 sched_pusch
        
        NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;  // 第2次定义 (2109行)
        
        // 之后在内层块中使用的是内层的 sched_pusch
    }
    
    // 这里继续使用外层的 sched_pusch
}
```

这是 C 语言的变量遮蔽（shadowing）规则：
1. 第1873行定义的外层 `sched_pusch` 在整个 UE_iterator 循环内有效
2. 第2109行定义的内层 `sched_pusch` 只在 `if (B == 0 && do_sched)` 块内有效
3. 内层变量会遮蔽外层同名变量

但问题是，这种写法其实是冗余的，因为两次定义的值完全一样。而且，第2109行之前（如2071行）已经在使用外层的 `sched_pusch`，说明外层变量已经可用。

这是一个潜在的代码bug或者冗余代码，应该被清理掉。

## 原因：C语言变量遮蔽（Variable Shadowing）规则

代码结构如下：

```c
UE_iterator(UE_list, UE) {                        // 外层作用域
    NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;  // ① 第1873行
    
    // ... 使用外层 sched_pusch ...
    
    if (B == 0 && do_sched) {                     // 内层 if 块
        sched_pusch->nrOfLayers = ...;            // ② 第2071行：使用外层变量
        
        NR_sched_pusch_t *sched_pusch = &sched_ctrl->sched_pusch;  // ③ 第2109行：遮蔽外层
        
        // 之后使用的是内层 sched_pusch
    }
}
```

**为什么不报错：**
- C语言允许内层作用域声明与外层同名的变量
- 内层变量会**遮蔽（shadow）**外层同名变量
- 在内层块中，使用的是内层定义的变量

**问题：**
1. **冗余代码**：两次定义的值完全相同
2. **第2071行已在使用外层变量**，说明外层 `sched_pusch` 在 if 块内完全可用
3. **容易混淆**：可能引发编译器警告（`-Wshadow`）

**建议删除第2109行的重复定义**，直接使用外层变量即可。

---

## User

更改遍历RB的方式，不提前计算CB的边界，直接按新配置参数ul_mcs_scan_RB_period扫描RB就行，每隔一个period就RB=（RB+5） % 274来遍历，由于RB最大是273，除不进5，所以按理来说也会遍历每个数。规划这个方案，如何在现有代码上以最小侵入式代码改动进行修改。

---

## Assistant (Plan · glm-5 · 34.7s)

_Thinking:_

用户想要修改RB遍历方式，从原来的基于CB边界计算的方式改为简单的RB递增遍历方式。

让我先分析现有代码结构，然后提出最小侵入式的修改方案。

现有逻辑：
1. `compute_rb_boundaries_for_mcs()` - 预计算每个MCS的RB边界
2. `ul_mcs_scan_rb_values[32]` - 存储32个RB边界值
3. `ul_mcs_scan_rb_values_per_mcs[29][32]` - 每个MCS的RB边界值
4. `ul_mcs_scan_cb_period` - CB切换周期
5. `ul_mcs_scan_current_cb_index` - 当前CB索引

用户要求的新逻辑：
1. 简单地每隔`ul_mcs_scan_RB_period`帧，RB = (RB + 5) % 274
2. 这样会遍历 0, 5, 10, ..., 270, 1, 6, 11, ..., 271, 2, 7, ...
3. 因为273除不尽5，所以最终会遍历所有数

让我先读取相关代码，理解现有结构。

让我先分析现有代码结构，了解需要修改的部分：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "offset": 1958,
  "limit": 100
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
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
2015:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
2016:         for(int i=0;i<nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];i++){
2017:           LOG_W(NR_MAC,"MCS %d CB %d RB %d\n", target_mcs, i, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs][i]);
2018:         }
2019:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
2020:         nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];
2021:         nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];
2022:         memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 
2023:                sizeof(nrmac->ul_mcs_scan_rb_values));
2024:         
2025:         if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {
2026:           nrmac->ul_mcs_scan_cb_accum_frames = 0;
2027:           if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {
2028:             nrmac->ul_mcs_scan_current_cb_index++;
2029:             nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;
2030:           }
2031:         }
2032:         
2033:         uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2034:         uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2035:         LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, cb_idx=%d/%d, rb=%d\n",
2036:               frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);
2037:       } else {
2038:         target_mcs = nrmac->ul_mcs_scan_ref;
2039:       }
2040:       sched_pusch->mcs = min(target_mcs, max_mcs);
2041:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2042:     } else if (bo->harq_round_max == 1) {
2043:       sched_pusch->mcs = max_mcs;
2044:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2045:     } else {
2046:       sched_pusch->mcs = get_mcs_from_bler(bo, stats, &sched_ctrl->ul_bler_stats, max_mcs, frame);
2047:       LOG_W(NR_MAC,"%d.%d starting mcs %d bleri %f,bo->max_mcs = %d\n", frame, slot, sched_pusch->mcs, sched_ctrl->ul_bler_stats.bler,bo->max_mcs);
2048:     }
2049:     // LOG_W(NR_MAC,"sched_pusch->mcs = %d",sched_pusch->mcs);
2050:     /* Schedule UE on SR or UL inactivity and no data (otherwise, will be scheduled
2051:      * based on data to transmit) */
2052:     if (B == 0 && do_sched) {
2053:       /* if no data, pre-allocate 5RB */
2054:       /* Find a free CCE */
2055:       int CCEIndex = get_cce_index(nrmac,
2056:                                    CC_id, slot, UE->rnti,
2057:                                    &sched_ctrl->aggregation_level,

(Showing lines 1958-2057 of 2859. Use offset=2058 to continue.)
</content>
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "ul_mcs_scan_current_rb|ul_mcs_scan_RB",
  "include": "*.h"
}
```

**Output:**
```
No files found
```

---

## Assistant (Plan · glm-5 · 54.1s)

_Thinking:_

现在我需要理解现有代码结构，然后规划最小侵入式的修改方案。

现有结构：
1. `compute_rb_boundaries_for_mcs()` - 计算RB边界
2. `ul_mcs_scan_rb_values[32]` - 存储RB值
3. `ul_mcs_scan_rb_values_per_mcs[29][32]` - 每个MCS的RB值
4. `ul_mcs_scan_cb_period` - CB切换周期
5. `ul_mcs_scan_cb_accum_frames` - 累计帧数
6. `ul_mcs_scan_current_cb_index` - 当前CB索引
7. `ul_mcs_scan_max_cb` - 最大CB数
8. `ul_mcs_scan_cb_progress[29]` - 每个MCS的CB进度
9. `ul_mcs_scan_max_cb_per_mcs[29]` - 每个MCS的最大CB数

用户想要的简化方案：
1. 新增 `ul_mcs_scan_RB_period` - RB切换周期
2. 新增 `ul_mcs_scan_current_rb` - 当前RB值
3. 每隔period帧：RB = (RB + 5) % 274

让我查看头文件中的定义，以及RB值在哪里被使用。

让我继续查看RB值使用的地方和相关头文件：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "limit": 30,
  "offset": 2243
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
2243:     sched_pusch->rbStart = rbStart;
2244:     uint16_t max_rbSize = 1;
2245:     uint16_t max_hcs_rb_size;
2246:     if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {
2247:       uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2248:       max_hcs_rb_size = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2249:       if (max_hcs_rb_size < 5) max_hcs_rb_size = 5;
2250:       if (max_hcs_rb_size > 273) max_hcs_rb_size = 273;
2251:     } else {
2252:       max_hcs_rb_size = rand_in_range(10, 273);
2253:     }
2254:     // uint16_t max_hcs_rb_size = 150;
2255:     while (rbStart + max_rbSize < bwpSize && !(rballoc_mask[rbStart + bwpStart + max_rbSize] & slbitmap)){
2256:             max_rbSize++;
2257:     }
2258:     max_rbSize = min(max_rbSize, max_hcs_rb_size);
2259:     
2260:     // double prediction =  LeafModelExported_predict_runtime_cost_p70(sched_pusch->mcs, sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2261:     // int best_prb = select_prb(sched_pusch->mcs,sched_pusch->tda_info.nrOfSymbols,max_rbSize,sched_ctrl->ul_harq_processes[sched_pusch->ul_harq_pid].round);
2262:     LOG_W(PHY,"max_rbSize = %hd\n",max_rbSize);
2263:     // LOG_W(PHY,"max_rbSize = %hd,prediction = %f\n",max_rbSize,prediction);
2264:     // max_rbSize = best_prb;
2265:       //by Luhan
2266:     // LOG_W(MAC,"---------------by Luhan, max_rbSize is %d, slot is %d, sched_slot is %d \n",max_rbSize, slot,sched_slot);
2267:     
2268:     if (rbStart + min_rb >= bwpSize || max_rbSize < min_rb) {
2269:       reset_beam_status(&nrmac->beam_info, frame, slot, iterator->UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2270:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, iterator->UE->UE_beam_index, slots_per_frame, beam.new_beam);
2271:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] could not allocate UL data: no resources (rbStart %d, min_rb %d, bwpSize %d)\n",
2272:             iterator->UE->rnti,

(Showing lines 2243-2272 of 2859. Use offset=2273 to continue.)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h",
  "limit": 30,
  "offset": 930
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

---

## Assistant (Plan · glm-5 · 38.5s)

_Thinking:_

现在我理解了现有代码结构。让我规划最小侵入式的修改方案。

现有逻辑流程：
1. 第1960-2036行：MCS扫描逻辑，计算CB边界
2. 第2246-2258行：使用RB值设置max_hcs_rb_size

用户想要的简化方案：
- 不再计算CB边界
- 直接按period递增RB：RB = (RB + 5) % 274

最小侵入式修改方案：

1. **新增成员变量** (nr_mac_gNB.h):
   - `uint32_t ul_mcs_scan_RB_period` - RB切换周期
   - `uint32_t ul_mcs_scan_RB_accum_frames` - RB累计帧数
   - `uint16_t ul_mcs_scan_current_rb` - 当前RB值

2. **新增配置参数** (MACRLC_nr_paramdef.h):
   - 添加 `ul_mcs_scan_RB_period` 配置项

3. **修改扫描逻辑** (gNB_scheduler_ulsch.c):
   - 简化第1960-2036行的逻辑
   - 可以添加一个新的flag来区分两种模式，或者直接替换

让我继续查看配置参数部分。

让我查看配置参数的定义：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "limit": 50,
  "offset": 75
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h</path>
<type>file</type>
<content>
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
120: #define MACRLCPARAMS_DESC { \
121:   {CONFIG_STRING_MACRLC_CC,                          NULL,                     0, .uptr=NULL,   .defintval=50011,           TYPE_UINT,    0}, \
122:   {CONFIG_STRING_MACRLC_TRANSPORT_N_PREFERENCE,      NULL,                     0, .strptr=NULL, .defstrval="local_L1",      TYPE_STRING,  0}, \
123:   {CONFIG_STRING_MACRLC_LOCAL_N_ADDRESS,             NULL,                     0, .strptr=NULL, .defstrval="127.0.0.1",     TYPE_STRING,  0}, \
124:   {CONFIG_STRING_MACRLC_REMOTE_N_ADDRESS,            NULL,                     0, .uptr=NULL,   .defstrval="127.0.0.2",     TYPE_STRING,  0}, \

(Showing lines 75-124 of 275. Use offset=125 to continue.)
</content>
```

**Tool: grep**

**Input:**
```json
{
  "pattern": "ul_mcs_scan",
  "include": "*.c",
  "path": "/home/bupt/wlh/ran/openair2/GNB_APP"
}
```

**Output:**
```
Found 18 matches
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

```

---

## Assistant (Plan · glm-5 · 193.1s)

_Thinking:_

现在我已经完全理解了现有代码结构。让我规划最小侵入式的修改方案。

现有结构总结：
1. **配置定义**：`MACRLC_nr_paramdef.h` 第80-87行
2. **结构体成员**：`nr_mac_gNB.h` 第935-952行
3. **配置加载**：`gnb_config.c` 第1636-1654行
4. **扫描逻辑**：`gNB_scheduler_ulsch.c` 第1960-2036行（MCS扫描）、第2246-2258行（RB使用）

用户想要的简化方案：
- 不再计算CB边界
- 直接按period递增RB：RB = (RB + 5) % 274

最小侵入式修改方案：

方案一：直接替换现有CB逻辑
- 重用现有的 `ul_mcs_scan_cb_period` 作为 `ul_mcs_scan_RB_period`
- 重用 `ul_mcs_scan_cb_accum_frames` 作为 `ul_mcs_scan_RB_accum_frames`
- 重用 `ul_mcs_scan_current_cb_index` 来存储当前RB值（改名为current_rb更好）
- 删除不再需要的变量和计算

方案二：添加新模式参数
- 添加 `ul_mcs_scan_rb_sweep_mode` 来区分两种模式
- 保留原有CB边界计算功能

我觉得方案一更符合用户要求的"最小侵入式"。

现在我已经完全理解了代码结构。让我提出最小侵入式的修改方案：

---

## 最小侵入式修改方案

### 设计思路

**复用现有变量**，避免大规模修改：

| 现有变量 | 新用途 |
|---------|--------|
| `ul_mcs_scan_cb_period` | → 作为 `RB_period`（RB切换周期） |
| `ul_mcs_scan_cb_accum_frames` | → 作为 `RB_accum_frames`（RB累计帧数） |
| `ul_mcs_scan_current_cb_index` | → 存储当前CB索引（保留，但不再查表，直接计算RB） |

**可删除的冗余变量**（可选，建议保留但不再使用）：
- `ul_mcs_scan_rb_values[32]`
- `ul_mcs_scan_rb_values_per_mcs[29][32]`
- `ul_mcs_scan_max_cb_per_mcs[29]`
- `ul_mcs_scan_cb_progress[29]`
- `ul_mcs_scan_max_cb`

---

### 修改清单

#### 1. `nr_mac_gNB.h` (可选修改)
添加新变量（如果想保留原有功能，可添加新模式flag）：
```c
// 在第952行后添加（如果想保留两种模式）
bool ul_mcs_scan_rb_step_mode;  // true: 新的步进模式, false: 原CB边界模式
```

#### 2. `MACRLC_nr_paramdef.h`
修改第113行帮助文本：
```c
#define HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD "Number of frames before incrementing RB by 5 (default 20)"
```

#### 3. `gnb_config.c`
添加初始化（如果添加新变量）：
```c
RC.nrmac[j]->ul_mcs_scan_rb_step_mode = true;  // 默认启用新步进模式
```

#### 4. `gNB_scheduler_ulsch.c` (核心修改)

**第1960-2036行**：简化扫描逻辑

```c
if (nrmac->ul_mcs_scan_enabled) {
  uint8_t target_mcs;
  if (nrmac->ul_mcs_scan_auto_sweep) {
    // MCS扫描逻辑（保持不变）
    uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;
    uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);
    uint8_t scan_start = nrmac->ul_mcs_scan_start;
    if (scan_start < scan_min) scan_start = scan_min;
    if (scan_start > scan_max) scan_start = scan_max;
    int mcs_range = scan_max - scan_min + 1;
    uint32_t period = nrmac->ul_mcs_scan_period;
    uint32_t rb_period = nrmac->ul_mcs_scan_cb_period;  // 复用为RB周期
    
    if (nrmac->ul_mcs_scan_last_frame != frame) {
      nrmac->ul_mcs_scan_last_frame = frame;
      
      int mcs_index = nrmac->ul_mcs_scan_current_index;
      int upper_range = scan_max - scan_start + 1;
      uint8_t current_mcs;
      if (mcs_index < upper_range) {
        current_mcs = scan_start + mcs_index;
      } else {
        current_mcs = scan_min + (mcs_index - upper_range);
      }
      
      nrmac->ul_mcs_scan_accum_frames++;
      
      // MCS切换
      if (nrmac->ul_mcs_scan_accum_frames >= period) {
        nrmac->ul_mcs_scan_accum_frames = 0;
        nrmac->ul_mcs_scan_current_index++;
        if (nrmac->ul_mcs_scan_current_index >= mcs_range) {
          nrmac->ul_mcs_scan_current_index = 0;
        }
        // MCS切换时重置RB为5（起始值）
        nrmac->ul_mcs_scan_current_cb_index = 1;  // RB = 1*5 = 5
      }
      
      // RB步进：每隔rb_period帧，RB += 5
      nrmac->ul_mcs_scan_cb_accum_frames++;
      if (nrmac->ul_mcs_scan_cb_accum_frames >= rb_period) {
        nrmac->ul_mcs_scan_cb_accum_frames = 0;
        nrmac->ul_mcs_scan_current_cb_index++;
        if (nrmac->ul_mcs_scan_current_cb_index >= 55) {  // 55*5=275 > 273，所以循环
          nrmac->ul_mcs_scan_current_cb_index = 0;
        }
      }
    }
    
    // 计算当前MCS
    int mcs_index = nrmac->ul_mcs_scan_current_index;
    int upper_range = scan_max - scan_start + 1;
    if (mcs_index < upper_range) {
      target_mcs = scan_start + mcs_index;
    } else {
      target_mcs = scan_min + (mcs_index - upper_range);
    }
    
    // 直接计算RB值
    uint16_t target_rb = nrmac->ul_mcs_scan_current_cb_index * 5;
    if (target_rb < 5) target_rb = 5;
    if (target_rb > 273) target_rb = 273;
    
    LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, rb_idx=%d, rb=%d\n",
          frame, slot, target_mcs, nrmac->ul_mcs_scan_current_cb_index, target_rb);
  } else {
    target_mcs = nrmac->ul_mcs_scan_ref;
  }
  sched_pusch->mcs = min(target_mcs, max_mcs);
  sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
}
```

**第2246-2258行**：修改RB使用逻辑

```c
if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {
  uint16_t target_rb = nrmac->ul_mcs_scan_current_cb_index * 5;
  if (target_rb < 5) target_rb = 5;
  if (target_rb > 273) target_rb = 273;
  max_hcs_rb_size = target_rb;
} else {
  max_hcs_rb_size = rand_in_range(10, 273);
}
```

---

### 遍历数学验证

`RB = (idx * 5) % 274` 的遍历序列：
```
idx: 0,1,2,...,54,55,56,... → RB: 0,5,10,...,270,1,6,11,...
```

由于 `gcd(5, 274) = 1`（274=2×137），因此会遍历 **0~273所有值**，共274步完成一轮。

---

### 需要确认的问题

**Tool: question**

**Input:**
```json
{
  "questions": [
    {
      "question": "是否需要保留原有的CB边界计算功能（通过新增模式参数切换），还是直接替换为新的步进模式？",
      "header": "模式选择",
      "options": [
        {
          "label": "直接替换",
          "description": "删除CB边界逻辑，只保留RB步进模式，代码更简洁"
        },
        {
          "label": "保留两种模式",
          "description": "添加ul_mcs_scan_rb_step_mode参数，可选择使用哪种模式"
        }
      ]
    }
  ]
}
```

**Output:**
```
User has answered your questions: "是否需要保留原有的CB边界计算功能（通过新增模式参数切换），还是直接替换为新的步进模式？"="直接替换". You can now continue with the user's answers in mind.
```

---

## Assistant (Plan · glm-5 · 71.9s)

_Thinking:_

用户选择直接替换，不保留原有的CB边界计算功能。这样可以进一步简化代码。

现在我需要完善方案，确保所有细节都考虑到。

好的，选择直接替换。现在完善最终方案：

---

## 最终修改方案（直接替换）

### 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `nr_mac_gNB.h` | 删除变量 | 删除5个不再使用的CB相关变量 |
| `MACRLC_nr_paramdef.h` | 修改帮助文本 | 更新参数说明 |
| `gnb_config.c` | 删除初始化 | 删除CB相关变量的初始化代码 |
| `gNB_scheduler_ulsch.c` | 核心修改 | 简化RB扫描逻辑 |

---

### 详细修改内容

#### 1. `nr_mac_gNB.h` (第945-952行)

**删除以下变量**：
```c
// 删除这些行
uint32_t ul_mcs_scan_cb_period;
uint32_t ul_mcs_scan_cb_accum_frames;
uint8_t ul_mcs_scan_current_cb_index;
uint8_t ul_mcs_scan_max_cb;
uint16_t ul_mcs_scan_rb_values[32];
uint8_t ul_mcs_scan_cb_progress[29];
uint8_t ul_mcs_scan_max_cb_per_mcs[29];
uint16_t ul_mcs_scan_rb_values_per_mcs[29][32];
```

**添加新变量**：
```c
uint32_t ul_mcs_scan_rb_period;        // RB步进周期（帧数）
uint32_t ul_mcs_scan_rb_accum_frames;  // RB累计帧数
uint16_t ul_mcs_scan_current_rb;       // 当前RB值
```

#### 2. `MACRLC_nr_paramdef.h`

**修改**（第87行）：
```c
#define CONFIG_STRING_MACRLC_UL_MCS_SCAN_RB_PERIOD "ul_mcs_scan_rb_period"
```

**修改**（第113行）：
```c
#define HLP_MACRLC_UL_MCS_SCAN_RB_PERIOD "Number of frames before incrementing RB by 5 (default 10)"
```

**修改参数表**（需要在对应位置添加新参数定义）：
```c
{CONFIG_STRING_MACRLC_UL_MCS_SCAN_RB_PERIOD, HLP_MACRLC_UL_MCS_SCAN_RB_PERIOD, 0, .uptr=NULL, .defintval=10, TYPE_UINT, 0}, \
```

#### 3. `gnb_config.c` (第1643-1654行附近)

**替换为**：
```c
RC.nrmac[j]->ul_mcs_scan_rb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_RB_PERIOD_IDX].uptr);
RC.nrmac[j]->ul_mcs_scan_rb_accum_frames = 0;
RC.nrmac[j]->ul_mcs_scan_current_rb = 5;  // 起始RB值
```

**删除**：
```c
// 删除这些行
RC.nrmac[j]->ul_mcs_scan_cb_period = ...
RC.nrmac[j]->ul_mcs_scan_current_cb_index = 0;
RC.nrmac[j]->ul_mcs_scan_cb_accum_frames = 0;
RC.nrmac[j]->ul_mcs_scan_max_cb = 0;
memset(RC.nrmac[j]->ul_mcs_scan_cb_progress, 0, ...);
memset(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs, 0, ...);
memset(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs, 0, ...);
```

#### 4. `gNB_scheduler_ulsch.c`

**删除函数** `compute_rb_boundaries_for_mcs()` (第43-74行)

**修改第1960-2036行**：
```c
if (nrmac->ul_mcs_scan_enabled) {
  uint8_t target_mcs;
  if (nrmac->ul_mcs_scan_auto_sweep) {
    uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;
    uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);
    uint8_t scan_start = nrmac->ul_mcs_scan_start;
    if (scan_start < scan_min) scan_start = scan_min;
    if (scan_start > scan_max) scan_start = scan_max;
    int mcs_range = scan_max - scan_min + 1;
    uint32_t period = nrmac->ul_mcs_scan_period;
    uint32_t rb_period = nrmac->ul_mcs_scan_rb_period;
    
    if (nrmac->ul_mcs_scan_last_frame != frame) {
      nrmac->ul_mcs_scan_last_frame = frame;
      
      nrmac->ul_mcs_scan_accum_frames++;
      nrmac->ul_mcs_scan_rb_accum_frames++;
      
      // MCS切换
      if (nrmac->ul_mcs_scan_accum_frames >= period) {
        nrmac->ul_mcs_scan_accum_frames = 0;
        nrmac->ul_mcs_scan_current_index++;
        if (nrmac->ul_mcs_scan_current_index >= mcs_range) {
          nrmac->ul_mcs_scan_current_index = 0;
        }
        // MCS切换时重置RB
        nrmac->ul_mcs_scan_current_rb = 5;
      }
      
      // RB步进：每隔rb_period帧，RB = (RB + 5) % 274
      if (nrmac->ul_mcs_scan_rb_accum_frames >= rb_period) {
        nrmac->ul_mcs_scan_rb_accum_frames = 0;
        nrmac->ul_mcs_scan_current_rb = (nrmac->ul_mcs_scan_current_rb + 5) % 274;
        if (nrmac->ul_mcs_scan_current_rb < 5) nrmac->ul_mcs_scan_current_rb = 5;
      }
    }
    
    // 计算当前MCS
    int mcs_index = nrmac->ul_mcs_scan_current_index;
    int upper_range = scan_max - scan_start + 1;
    if (mcs_index < upper_range) {
      target_mcs = scan_start + mcs_index;
    } else {
      target_mcs = scan_min + (mcs_index - upper_range);
    }
    
    LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, rb=%d\n",
          frame, slot, target_mcs, nrmac->ul_mcs_scan_current_rb);
  } else {
    target_mcs = nrmac->ul_mcs_scan_ref;
  }
  sched_pusch->mcs = min(target_mcs, max_mcs);
  sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
}
```

**修改第2246-2258行**：
```c
if (nrmac->ul_mcs_scan_enabled && nrmac->ul_mcs_scan_auto_sweep) {
  max_hcs_rb_size = nrmac->ul_mcs_scan_current_rb;
  if (max_hcs_rb_size < 5) max_hcs_rb_size = 5;
  if (max_hcs_rb_size > 273) max_hcs_rb_size = 273;
} else {
  max_hcs_rb_size = rand_in_range(10, 273);
}
```

---

### 配置文件示例

```ini
MACRLCs = (
  {
    ul_mcs_scan_enabled = 1;
    ul_mcs_scan_auto_sweep = 1;
    ul_mcs_scan_min_mcs = 5;
    ul_mcs_scan_max_mcs = 28;
    ul_mcs_scan_start = 9;
    ul_mcs_scan_period = 100;    # MCS切换周期（帧）
    ul_mcs_scan_rb_period = 10;  # RB步进周期（帧）
  }
)
```

---

### 修改影响范围

| 影响 | 说明 |
|------|------|
| 删除代码行数 | 约 60 行 |
| 新增代码行数 | 约 20 行 |
| 净减少 | ~40 行 |
| 编译依赖 | 无新增依赖 |
| 运行时行为 | RB遍历从CB边界查表改为步进递增 |

---

方案规划完成，可以开始实施吗？

---

## User

开始实施

---

## Assistant (Build · glm-5 · 39.6s)

_Thinking:_

用户要求开始实施修改方案。我需要按照规划逐步修改以下文件：

1. `nr_mac_gNB.h` - 删除旧变量，添加新变量
2. `MACRLC_nr_paramdef.h` - 修改配置参数定义
3. `gnb_config.c` - 修改初始化代码
4. `gNB_scheduler_ulsch.c` - 核心修改，删除compute_rb_boundaries_for_mcs函数，修改扫描逻辑

让我开始实施。

开始实施修改。

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "修改 gnb_config.c - 更新初始化代码",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
    "status": "pending",
    "priority": "high"
  },
  {
    "content": "修改 gnb_config.c - 更新初始化代码",
    "status": "pending",
    "priority": "high"
  },
  {
    "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
    "status": "pending",
    "priority": "high"
  }
]
```

---

## Assistant (Build · glm-5 · 33.7s)

_Thinking:_

现在开始修改文件。首先修改 nr_mac_gNB.h

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h",
  "oldString": "  uint32_t ul_mcs_scan_cb_period;\n  uint32_t ul_mcs_scan_cb_accum_frames;\n  uint8_t ul_mcs_scan_current_cb_index;\n  uint8_t ul_mcs_scan_max_cb;\n  uint16_t ul_mcs_scan_rb_values[32];\n  uint8_t ul_mcs_scan_cb_progress[29];\n  uint8_t ul_mcs_scan_max_cb_per_mcs[29];\n  uint16_t ul_mcs_scan_rb_values_per_mcs[29][32];",
  "newString": "  uint32_t ul_mcs_scan_rb_period;\n  uint32_t ul_mcs_scan_rb_accum_frames;\n  uint16_t ul_mcs_scan_current_rb;"
}
```

**Output:**
```
Edit applied successfully.

LSP errors detected in this file, please fix:
<diagnostics file="/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/nr_mac_gNB.h">
ERROR [45:10] 'common/utils/ds/seq_arr.h' file not found
ERROR [106:14] Unknown type name 'uint8_t' (fix available)
ERROR [175:32] Use of undeclared identifier 'NUM_PDCCH_AGG_LEVELS'
ERROR [179:3] Unknown type name 'uint8_t' (fix available)
ERROR [180:3] Unknown type name 'uint8_t' (fix available)
ERROR [184:3] Unknown type name 'uint16_t' (fix available)
ERROR [185:3] Unknown type name 'uint16_t' (fix available)
ERROR [186:3] Unknown type name 'uint8_t' (fix available)
ERROR [187:3] Unknown type name 'uint8_t' (fix available)
ERROR [188:3] Unknown type name 'uint8_t' (fix available)
ERROR [189:3] Unknown type name 'uint8_t' (fix available)
ERROR [190:3] Unknown type name 'uint8_t' (fix available)
ERROR [191:3] Unknown type name 'uint8_t' (fix available)
ERROR [192:3] Unknown type name 'uint16_t' (fix available)
ERROR [193:3] Unknown type name 'uint8_t' (fix available)
ERROR [206:3] Unknown type name 'uint8_t' (fix available)
ERROR [208:3] Unknown type name 'uint8_t' (fix available)
ERROR [212:3] Unknown type name 'uint8_t' (fix available)
ERROR [214:3] Unknown type name 'frame_t'
ERROR [216:3] Unknown type name 'sub_frame_t'
... and 1 more
</diagnostics>
```

---

## Assistant (Build · glm-5 · 50.2s)

_Thinking:_

这些LSP错误看起来是编辑器/LSP的问题，与我们的修改无关。这些错误是由于LSP没有正确解析头文件的依赖关系导致的。实际的代码修改是正确的。

让我继续修改下一个文件。

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "修改 gnb_config.c - 更新初始化代码",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "content": "修改 gnb_config.c - 更新初始化代码",
    "status": "pending",
    "priority": "high"
  },
  {
    "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
    "status": "pending",
    "priority": "high"
  }
]
```

---

## Assistant (Build · glm-5 · 70.1s)

_Thinking:_

现在修改 MACRLC_nr_paramdef.h。我需要：
1. 修改第87行的配置字符串宏定义
2. 修改第113行的帮助文本

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "oldString": "#define CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD         \"ul_mcs_scan_cb_period\"",
  "newString": "#define CONFIG_STRING_MACRLC_UL_MCS_SCAN_RB_PERIOD         \"ul_mcs_scan_rb_period\""
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · glm-5 · 55.4s)

_Thinking:_

修改帮助文本。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "newString": "#define HLP_MACRLC_UL_MCS_SCAN_RB_PERIOD \"Number of frames before incrementing RB by 5 (default 10)\"",
  "oldString": "#define HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD \"Number of frames to hold each codeblock count before switching RB (default 20)\""
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · glm-5 · 30.6s)

_Thinking:_

现在需要找到参数表的定义位置，修改参数定义。让我先读取参数表的内容。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "limit": 60,
  "offset": 145
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h</path>
<type>file</type>
<content>
145:   {CONFIG_STRING_MACRLC_UL_BLER_TARGET_UPPER,        HLP_MACRLC_UL_BLER_UP,    0, .dblptr=NULL, .defdblval=0.15,            TYPE_DOUBLE,  0}, \
146:   {CONFIG_STRING_MACRLC_UL_BLER_TARGET_LOWER,        HLP_MACRLC_UL_BLER_LO,    0, .dblptr=NULL, .defdblval=0.05,            TYPE_DOUBLE,  0}, \
147:   {CONFIG_STRING_MACRLC_UL_MAX_MCS,                  HLP_MACRLC_UL_MAX_MCS,    0, .u8ptr=NULL,  .defintval=28,              TYPE_UINT8,   0}, \
148:   {CONFIG_STRING_MACRLC_DL_HARQ_ROUND_MAX,           HLP_MACRLC_DL_HARQ_MAX,   0, .u8ptr=NULL,  .defintval=4,               TYPE_UINT8,   0}, \
149:   {CONFIG_STRING_MACRLC_UL_HARQ_ROUND_MAX,           HLP_MACRLC_UL_HARQ_MAX,   0, .u8ptr=NULL,  .defintval=4,               TYPE_UINT8,   0}, \
150:   {CONFIG_STRING_MACRLC_MIN_GRANT_PRB,               HLP_MACRLC_MIN_GRANT_PRB, 0, .u8ptr=NULL,  .defintval=5,               TYPE_UINT8,   0}, \
151:   {CONFIG_STRING_MACRLC_MIN_GRANT_MCS,               HLP_MACRLC_MIN_GRANT_MCS, 0, .u8ptr=NULL,  .defintval=9,               TYPE_UINT8,   0}, \
152:   {CONFIG_STRING_MACRLC_IDENTITY_PM,                 HLP_MACRLC_IDENTITY_PM,   PARAMFLAG_BOOL, .u8ptr=NULL, .defintval=0,   TYPE_UINT8,   0}, \
153:   {CONFIG_STRING_MACRLC_LOCAL_N_ADDRESS_F1U,         NULL,                     0, .strptr=NULL, .defstrval=NULL,            TYPE_STRING,  0}, \
154:   {CONFIG_STRING_MACRLC_TRANSPORT_S_SHM_PREFIX,      NULL,                     0, .strptr=NULL, .defstrval="nvipc",         TYPE_STRING,  0}, \
155:   {CONFIG_STRING_MACRLC_TRANSPORT_S_POLL_CORE,       NULL,                     0, .i8ptr=NULL,  .defintval=-1,              TYPE_INT8,    0}, \
156:   {CONFIG_STRING_MACRLC_ANALOG_BEAMFORMING,          HLP_MACRLC_AB,            PARAMFLAG_BOOL, .u8ptr=NULL, .defintval=0,   TYPE_UINT8,   0}, \
157:   {CONFIG_STRING_MACRLC_BEAM_DURATION,               HLP_MACRLC_BEAM_DURATION, 0, .u8ptr=NULL,  .defintval=1,               TYPE_UINT8,   0}, \
158:   {CONFIG_STRING_MACRLC_BEAMS_PERIOD,                HLP_MACRLC_BEAMS_PERIOD,  0, .u8ptr=NULL,  .defintval=1,               TYPE_UINT8,   0}, \
159:   {CONFIG_STRING_MACRLC_PUSCH_RSSI_THRESHOLD,        HLP_MACRLC_PUSCH_RSSI_THRESHOLD, \
160:                                                                                0, .iptr=NULL,   .defintval=0,               TYPE_INT,     0}, \
161:   {CONFIG_STRING_MACRLC_PUCCH_RSSI_THRESHOLD,        HLP_MACRLC_PUCCH_RSSI_THRESHOLD, \
162:                                                                                0, .iptr=NULL,   .defintval=0,               TYPE_INT,     0}, \
163:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_ENABLED,         HLP_MACRLC_UL_MCS_SCAN_EN,  PARAMFLAG_BOOL, .u8ptr=NULL, .defintval=0,   TYPE_UINT8,   0}, \
164:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_REF,             HLP_MACRLC_UL_MCS_SCAN_REF, 0, .u8ptr=NULL,  .defintval=9,               TYPE_UINT8,   0}, \
165:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_AUTO_SWEEP,      HLP_MACRLC_UL_MCS_SCAN_SWEEP, PARAMFLAG_BOOL, .u8ptr=NULL, .defintval=0,   TYPE_UINT8,   0}, \
166:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_MIN_MCS,         HLP_MACRLC_UL_MCS_SCAN_MIN, 0, .u8ptr=NULL,  .defintval=5,               TYPE_UINT8,   0}, \
167:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_MAX_MCS,         HLP_MACRLC_UL_MCS_SCAN_MAX, 0, .u8ptr=NULL,  .defintval=28,              TYPE_UINT8,   0}, \
168:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_PERIOD,          HLP_MACRLC_UL_MCS_SCAN_PERIOD, 0, .uptr=NULL,  .defintval=100,             TYPE_UINT,    0}, \
169:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_START,           HLP_MACRLC_UL_MCS_SCAN_START, 0, .u8ptr=NULL,  .defintval=9,               TYPE_UINT8,   0}, \
170:   {CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD,       HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD, 0, .uptr=NULL,  .defintval=20,              TYPE_UINT,    0}, \
171: }
172: // clang-format off
173: 
174: #define MACRLC_CC_IDX                                          0
175: #define MACRLC_TRANSPORT_N_PREFERENCE_IDX                      1
176: #define MACRLC_LOCAL_N_ADDRESS_IDX                             2
177: #define MACRLC_REMOTE_N_ADDRESS_IDX                            3
178: #define MACRLC_LOCAL_N_PORTC_IDX                               4
179: #define MACRLC_REMOTE_N_PORTC_IDX                              5
180: #define MACRLC_LOCAL_N_PORTD_IDX                               6
181: #define MACRLC_REMOTE_N_PORTD_IDX                              7
182: #define MACRLC_TRANSPORT_S_PREFERENCE_IDX                      8
183: #define MACRLC_LOCAL_S_ADDRESS_IDX                             9
184: #define MACRLC_REMOTE_S_ADDRESS_IDX                            10
185: #define MACRLC_LOCAL_S_PORTC_IDX                               11
186: #define MACRLC_REMOTE_S_PORTC_IDX                              12
187: #define MACRLC_LOCAL_S_PORTD_IDX                               13
188: #define MACRLC_REMOTE_S_PORTD_IDX                              14
189: #define MACRLC_ULSCH_MAX_FRAME_INACTIVITY                      15
190: #define MACRLC_PUSCHTARGETSNRX10_IDX                           16
191: #define MACRLC_PUCCHTARGETSNRX10_IDX                           17
192: #define MACRLC_UL_PRBBLACK_SNR_THRESHOLD_IDX                   18
193: #define MACRLC_PUCCHFAILURETHRES_IDX                           19
194: #define MACRLC_PUSCHFAILURETHRES_IDX                           20
195: #define MACRLC_DL_BLER_TARGET_UPPER_IDX                        21
196: #define MACRLC_DL_BLER_TARGET_LOWER_IDX                        22
197: #define MACRLC_DL_MAX_MCS_IDX                                  23
198: #define MACRLC_UL_BLER_TARGET_UPPER_IDX                        24
199: #define MACRLC_UL_BLER_TARGET_LOWER_IDX                        25
200: #define MACRLC_UL_MAX_MCS_IDX                                  26
201: #define MACRLC_DL_HARQ_ROUND_MAX_IDX                           27
202: #define MACRLC_UL_HARQ_ROUND_MAX_IDX                           28
203: #define MACRLC_MIN_GRANT_PRB_IDX                               29
204: #define MACRLC_MIN_GRANT_MCS_IDX                               30

(Showing lines 145-204 of 275. Use offset=205 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 70.1s)

_Thinking:_

需要修改第170行的参数定义。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "newString": "  {CONFIG_STRING_MACRLC_UL_MCS_SCAN_RB_PERIOD,       HLP_MACRLC_UL_MCS_SCAN_RB_PERIOD, 0, .uptr=NULL,  .defintval=10,              TYPE_UINT,    0}, \\",
  "oldString": "  {CONFIG_STRING_MACRLC_UL_MCS_SCAN_CB_PERIOD,       HLP_MACRLC_UL_MCS_SCAN_CB_PERIOD, 0, .uptr=NULL,  .defintval=20,              TYPE_UINT,    0}, \\"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · glm-5 · 52.6s)

_Thinking:_

现在需要修改索引定义。让我读取更多内容来找到索引定义。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "limit": 30,
  "offset": 205
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h</path>
<type>file</type>
<content>
205: #define MACRLC_IDENTITY_PM_IDX                                 31
206: #define MACRLC_LOCAL_N_ADDRESS_F1U_IDX                         32
207: #define MACRLC_TRANSPORT_S_SHM_PREFIX                          33
208: #define MACRLC_TRANSPORT_S_POLL_CORE                           34
209: #define MACRLC_ANALOG_BEAMFORMING_IDX                          35
210: #define MACRLC_ANALOG_BEAM_DURATION_IDX                        36
211: #define MACRLC_ANALOG_BEAMS_PERIOD_IDX                         37
212: #define MACRLC_PUSCH_RSSI_THRES_IDX                            38
213: #define MACRLC_PUCCH_RSSI_THRES_IDX                            39
214: #define MACRLC_UL_MCS_SCAN_ENABLED_IDX                         40
215: #define MACRLC_UL_MCS_SCAN_REF_IDX                             41
216: #define MACRLC_UL_MCS_SCAN_AUTO_SWEEP_IDX                      42
217: #define MACRLC_UL_MCS_SCAN_MIN_MCS_IDX                         43
218: #define MACRLC_UL_MCS_SCAN_MAX_MCS_IDX                         44
219: #define MACRLC_UL_MCS_SCAN_PERIOD_IDX                          45
220: #define MACRLC_UL_MCS_SCAN_START_IDX                           46
221: #define MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX                       47
222: 
223: #define MACRLCPARAMS_CHECK { \
224:   { .s5 = { NULL } }, \
225:   { .s5 = { NULL } }, \
226:   { .s5 = { NULL } }, \
227:   { .s5 = { NULL } }, \
228:   { .s5 = { NULL } }, \
229:   { .s5 = { NULL } }, \
230:   { .s5 = { NULL } }, \
231:   { .s5 = { NULL } }, \
232:   { .s5 = { NULL } }, \
233:   { .s5 = { NULL } }, \
234:   { .s5 = { NULL } }, \

(Showing lines 205-234 of 275. Use offset=235 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 35.5s)

_Thinking:_

需要修改第221行的索引定义，从 CB_PERIOD 改为 RB_PERIOD。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/MACRLC_nr_paramdef.h",
  "newString": "#define MACRLC_UL_MCS_SCAN_RB_PERIOD_IDX                       47",
  "oldString": "#define MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX                       47"
}
```

**Output:**
```
Edit applied successfully.
```

---

## Assistant (Build · glm-5 · 57.5s)

_Thinking:_

现在修改 gnb_config.c。

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 gnb_config.c - 更新初始化代码",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 gnb_config.c - 更新初始化代码",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
    "status": "pending",
    "priority": "high"
  }
]
```

---

## Assistant (Build · glm-5 · 46.1s)

_Thinking:_

现在修改 gnb_config.c。我需要修改初始化代码。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c",
  "limit": 30,
  "offset": 1635
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c</path>
<type>file</type>
<content>
1635:         ul_bler_options->harq_round_max = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_HARQ_ROUND_MAX_IDX].u8ptr);
1636:       RC.nrmac[j]->ul_mcs_scan_enabled = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_ENABLED_IDX].u8ptr);
1637:       RC.nrmac[j]->ul_mcs_scan_ref = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_REF_IDX].u8ptr);
1638:       RC.nrmac[j]->ul_mcs_scan_auto_sweep = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_AUTO_SWEEP_IDX].u8ptr);
1639:       RC.nrmac[j]->ul_mcs_scan_min_mcs = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_MIN_MCS_IDX].u8ptr);
1640:       RC.nrmac[j]->ul_mcs_scan_max_mcs = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_MAX_MCS_IDX].u8ptr);
1641:       RC.nrmac[j]->ul_mcs_scan_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_PERIOD_IDX].uptr);
1642:       RC.nrmac[j]->ul_mcs_scan_start = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_START_IDX].u8ptr);
1643:       RC.nrmac[j]->ul_mcs_scan_cb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX].uptr);
1644:       RC.nrmac[j]->ul_mcs_scan_current_cb_index = 0;
1645:       RC.nrmac[j]->ul_mcs_scan_cb_accum_frames = 0;
1646:       RC.nrmac[j]->ul_mcs_scan_max_cb = 0;
1647:       memset(RC.nrmac[j]->ul_mcs_scan_cb_progress, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_cb_progress));
1648:       memset(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs));
1649:       memset(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs));
1650:       LOG_I(NR_MAC, "UL MCS Scan: enabled=%d, ref=%d, auto_sweep=%d, min=%d, max=%d, period=%u, start=%d, cb_period=%u\n",
1651:             RC.nrmac[j]->ul_mcs_scan_enabled, RC.nrmac[j]->ul_mcs_scan_ref, 
1652:             RC.nrmac[j]->ul_mcs_scan_auto_sweep, RC.nrmac[j]->ul_mcs_scan_min_mcs,
1653:             RC.nrmac[j]->ul_mcs_scan_max_mcs, RC.nrmac[j]->ul_mcs_scan_period,
1654:             RC.nrmac[j]->ul_mcs_scan_start, RC.nrmac[j]->ul_mcs_scan_cb_period);
1655:       RC.nrmac[j]->min_grant_prb = *(MacRLC_ParamList.paramarray[j][MACRLC_MIN_GRANT_PRB_IDX].u8ptr);
1656:       RC.nrmac[j]->min_grant_mcs = *(MacRLC_ParamList.paramarray[j][MACRLC_MIN_GRANT_MCS_IDX].u8ptr);
1657:       RC.nrmac[j]->identity_pm = *(MacRLC_ParamList.paramarray[j][MACRLC_IDENTITY_PM_IDX].u8ptr);
1658:       // PRB Blacklist
1659:       uint16_t prbbl[MAX_BWP_SIZE] = {0};
1660:       int num_ulprbbl = get_prb_blacklist(j, prbbl);
1661:       if (num_ulprbbl != -1) {
1662:         LOG_I(NR_PHY, "Copying %d blacklisted PRB to L1 context\n", num_ulprbbl);
1663:         memcpy(RC.nrmac[j]->ulprbbl, prbbl, MAX_BWP_SIZE * sizeof(prbbl[0]));
1664:       }

(Showing lines 1635-1664 of 2729. Use offset=1665 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 1440.5s)

_Thinking:_

需要替换第1643-1654行的内容。

---

## User

继续修改

---

## Assistant (Build · glm-5 · 65.8s)

_Thinking:_

用户让我继续修改。我需要修改 gnb_config.c 文件，替换旧的CB相关初始化代码为新的RB步进相关初始化代码。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c",
  "newString": "      RC.nrmac[j]->ul_mcs_scan_rb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_RB_PERIOD_IDX].uptr);\n      RC.nrmac[j]->ul_mcs_scan_rb_accum_frames = 0;\n      RC.nrmac[j]->ul_mcs_scan_current_rb = 5;\n      LOG_I(NR_MAC, \"UL MCS Scan: enabled=%d, ref=%d, auto_sweep=%d, min=%d, max=%d, period=%u, start=%d, rb_period=%u\\n\",\n            RC.nrmac[j]->ul_mcs_scan_enabled, RC.nrmac[j]->ul_mcs_scan_ref, \n            RC.nrmac[j]->ul_mcs_scan_auto_sweep, RC.nrmac[j]->ul_mcs_scan_min_mcs,\n            RC.nrmac[j]->ul_mcs_scan_max_mcs, RC.nrmac[j]->ul_mcs_scan_period,\n            RC.nrmac[j]->ul_mcs_scan_start, RC.nrmac[j]->ul_mcs_scan_rb_period);",
  "oldString": "      RC.nrmac[j]->ul_mcs_scan_cb_period = *(MacRLC_ParamList.paramarray[j][MACRLC_UL_MCS_SCAN_CB_PERIOD_IDX].uptr);\n      RC.nrmac[j]->ul_mcs_scan_current_cb_index = 0;\n      RC.nrmac[j]->ul_mcs_scan_cb_accum_frames = 0;\n      RC.nrmac[j]->ul_mcs_scan_max_cb = 0;\n      memset(RC.nrmac[j]->ul_mcs_scan_cb_progress, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_cb_progress));\n      memset(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_max_cb_per_mcs));\n      memset(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs, 0, sizeof(RC.nrmac[j]->ul_mcs_scan_rb_values_per_mcs));\n      LOG_I(NR_MAC, \"UL MCS Scan: enabled=%d, ref=%d, auto_sweep=%d, min=%d, max=%d, period=%u, start=%d, cb_period=%u\\n\",\n            RC.nrmac[j]->ul_mcs_scan_enabled, RC.nrmac[j]->ul_mcs_scan_ref, \n            RC.nrmac[j]->ul_mcs_scan_auto_sweep, RC.nrmac[j]->ul_mcs_scan_min_mcs,\n            RC.nrmac[j]->ul_mcs_scan_max_mcs, RC.nrmac[j]->ul_mcs_scan_period,\n            RC.nrmac[j]->ul_mcs_scan_start, RC.nrmac[j]->ul_mcs_scan_cb_period);"
}
```

**Output:**
```
Edit applied successfully.

LSP errors detected in this file, please fix:
<diagnostics file="/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.c">
ERROR [30:10] In included file: 'RRC/NR/nr_rrc_defs.h' file not found

/home/bupt/wlh/ran/openair2/GNB_APP/gnb_config.h:33:10:
note: error occurred here
ERROR [107:18] Unknown type name 'NR_ServingCellConfigCommon_t'
ERROR [110:21] Call to undeclared function 'calloc_or_fail'; ISO C99 and later do not support implicit function declarations
ERROR [117:6] Incomplete definition of type 'struct NR_TDD_UL_DL_ConfigCommon'

gnb_config.c:116:10: note: forward declaration of 'struct NR_TDD_UL_DL_ConfigCommon'
ERROR [117:53] Incomplete definition of type 'struct NR_TDD_UL_DL_ConfigCommon'

gnb_config.c:116:10: note: forward declaration of 'struct NR_TDD_UL_DL_ConfigCommon'
ERROR [118:6] Incomplete definition of type 'struct NR_TDD_UL_DL_ConfigCommon'

gnb_config.c:116:10: note: forward declaration of 'struct NR_TDD_UL_DL_ConfigCommon'
ERROR [119:36] Incomplete definition of type 'struct NR_TDD_UL_DL_ConfigCommon'

gnb_config.c:116:10: note: forward declaration of 'struct NR_TDD_UL_DL_ConfigCommon'
ERROR [124:3] Use of undeclared identifier 'NR_FrequencyInfoDL_t'
ERROR [124:25] Use of undeclared identifier 'frequencyInfoDL'
ERROR [125:3] Use of undeclared identifier 'frequencyInfoDL'
ERROR [125:69] Use of undeclared identifier 'frequencyInfoDL'
ERROR [126:3] Use of undeclared identifier 'NR_FreqBandIndicatorNR_t'
ERROR [126:29] Use of undeclared identifier 'dl_frequencyBandList'
ERROR [126:78] Use of undeclared identifier 'dl_frequencyBandList'
ERROR [127:3] Call to undeclared function 'asn1cSeqAdd'; ISO C99 and later do not support implicit function declarations
ERROR [127:16] Use of undeclared identifier 'frequencyInfoDL'
ERROR [127:57] Use of undeclared identifier 'dl_frequencyBandList'
ERROR [128:87] Invalid application of 'sizeof' to an incomplete type 'struct NR_SCS_SpecificCarrier'

gnb_config.c:128:10: note: forward declaration of 'struct NR_SCS_SpecificCarrier'
ERROR [129:16] Use of undeclared identifier 'frequencyInfoDL'
ERROR [131:3] Use of undeclared identifier 'NR_SetupRelease_PDCCH_ConfigCommon_PR_setup'
... and 1 more
</diagnostics>
```

---

## Assistant (Build · glm-5 · 54.5s)

_Thinking:_

这些LSP错误是由于缺少头文件导致的，不是我们修改引起的问题。现在继续修改 gNB_scheduler_ulsch.c 文件。

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 gnb_config.c - 更新初始化代码",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
      "status": "in_progress",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "修改 nr_mac_gNB.h - 删除旧变量，添加新变量",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 MACRLC_nr_paramdef.h - 更新配置参数定义",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 gnb_config.c - 更新初始化代码",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "修改 gNB_scheduler_ulsch.c - 核心扫描逻辑",
    "status": "in_progress",
    "priority": "high"
  }
]
```

---

## Assistant (Build · glm-5 · 43.7s)

_Thinking:_

现在需要修改 gNB_scheduler_ulsch.c 文件，这是核心修改：
1. 删除 compute_rb_boundaries_for_mcs 函数
2. 修改扫描逻辑
3. 修改RB使用逻辑

让我先删除 compute_rb_boundaries_for_mcs 函数，然后修改扫描逻辑。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "newString": "#include \"LAYER2/NR_MAC_gNB/leaf_model_exported.h\"",
  "oldString": "static void compute_rb_boundaries_for_mcs(uint8_t mcs, uint16_t R, uint8_t Qm,\n                                          uint16_t symbols, uint16_t dmrs,\n                                          uint8_t layers, uint16_t *rb_values,\n                                          uint8_t *max_cb)\n{\n  uint32_t Kcb_1 = 8448;\n  uint32_t Kcb_2 = 3840;\n  uint8_t num_values = 0;\n  uint8_t last_cb = 0;\n  uint16_t min_rb = 5;\n  uint16_t max_rb = 273;\n  \n  for (uint16_t rb = min_rb; rb <= max_rb && num_values < 32; rb++) {\n    uint32_t tbs_bits = nr_compute_tbs(Qm, R, rb, symbols, dmrs, 0, 0, layers);\n    uint8_t BG = get_BG(tbs_bits, R);\n    uint32_t Kcb = (BG == 1) ? Kcb_1 : Kcb_2;\n    uint8_t num_cb;\n    if (tbs_bits <= Kcb) {\n      num_cb = 1;\n    } else {\n      num_cb = tbs_bits / (Kcb - 24);\n      if ((Kcb - 24) * num_cb < tbs_bits)\n        num_cb++;\n    }\n    if (num_cb != last_cb) {\n      rb_values[num_values] = rb;\n      num_values++;\n      last_cb = num_cb;\n    }\n  }\n  *max_cb = last_cb;\n}\n#include \"LAYER2/NR_MAC_gNB/leaf_model_exported.h\""
}
```

**Output:**
```
Edit applied successfully.

LSP errors detected in this file, please fix:
<diagnostics file="/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c">
ERROR [32:10] 'LAYER2/NR_MAC_gNB/mac_proto.h' file not found
ERROR [58:16] Unknown type name 'gNB_MAC_INST' (fix available)
ERROR [61:3] Call to undeclared function 'NR_SCHED_ENSURE_LOCKED'; ISO C99 and later do not support implicit function declarations (fix available)
ERROR [64:3] Use of undeclared identifier 'frame_structure_t'
ERROR [64:22] Use of undeclared identifier 'fs'
ERROR [66:7] Use of undeclared identifier 'fs'
ERROR [66:25] Use of undeclared identifier 'TDD'
ERROR [68:13] Call to undeclared function 'get_slot_idx_in_period'; ISO C99 and later do not support implicit function declarations
ERROR [68:42] Use of undeclared identifier 'fs'
ERROR [69:5] Use of undeclared identifier 'tdd_bitmap_t'
ERROR [69:19] Use of undeclared identifier 'tdd_slot_bitmap'
ERROR [69:37] Use of undeclared identifier 'fs'
ERROR [70:10] Use of undeclared identifier 'tdd_slot_bitmap'
ERROR [70:52] Call to undeclared function 'is_mixed_slot'; ISO C99 and later do not support implicit function declarations
ERROR [70:69] Use of undeclared identifier 'fs'
ERROR [76:3] Call to undeclared function 'UE_iterator'; ISO C99 and later do not support implicit function declarations
ERROR [76:36] Use of undeclared identifier 'UE'
ERROR [76:40] Expected ';' after expression (fix available)
ERROR [77:5] Use of undeclared identifier 'NR_sched_srs_t'
ERROR [78:8] Use of undeclared identifier 'sched_srs'
... and 1 more
</diagnostics>
```

---

## Assistant (Build · glm-5 · 76.6s)

_Thinking:_

LSP错误是由于缺少头文件导致的，不是我们修改的问题。现在继续修改扫描逻辑部分。让我先查看当前的扫描逻辑位置。

现在修改核心扫描逻辑：

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "limit": 100,
  "offset": 1880
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
1880:                                           &n_rb_sched[beam.idx],
1881:                                           dci_beam.idx,
1882:                                           UE,
1883:                                           sched_pusch->ul_harq_pid,
1884:                                           scc,
1885:                                           tda);
1886:       if (!r) {
1887:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] UL retransmission could not be allocated\n", UE->rnti, frame, slot);
1888:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1889:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1890:         continue;
1891:       }
1892:       else
1893:         LOG_D(NR_MAC,"%4d.%2d UL Retransmission UE RNTI %04x to be allocated, max_num_ue %d\n", frame, slot, UE->rnti,max_num_ue);
1894: 
1895:       /* reduce max_num_ue once we are sure UE can be allocated, i.e., has CCE */
1896:       remainUEs[beam.idx]--;
1897:       continue;
1898:     }
1899: 
1900:     /* skip this UE if there are no free HARQ processes. This can happen e.g.
1901:      * if the UE disconnected in L2sim, in which case the gNB is not notified
1902:      * (this can be considered a design flaw) */
1903:     if (sched_ctrl->available_ul_harq.head < 0) {
1904:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1905:       reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1906:       LOG_D(NR_MAC, "[UE %04x][%4d.%2d] has no free UL HARQ process, skipping\n", UE->rnti, frame, slot);
1907:       continue;
1908:     }
1909: 
1910:     const int B = max(0, sched_ctrl->estimated_ul_buffer - sched_ctrl->sched_ul_bytes);
1911:     /* preprocessor computed sched_frame/sched_slot */
1912:     const bool do_sched = nr_UE_is_to_be_scheduled(&nrmac->frame_structure,
1913:                                                    UE,
1914:                                                    sched_frame,
1915:                                                    sched_slot,
1916:                                                    nrmac->ulsch_max_frame_inactivity);
1917: 
1918:     LOG_D(NR_MAC,"pf_ul: do_sched UE %04x => %s\n", UE->rnti, do_sched ? "yes" : "no");
1919:     if ((B == 0 && !do_sched) || nr_timer_is_active(&sched_ctrl->transm_interrupt)) {
1920:       reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
1921:       reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
1922:       continue;
1923:     }
1924: 
1925:     const NR_bler_options_t *bo = &nrmac->ul_bler;
1926:     const int max_mcs_table = (current_BWP->mcs_table == 0 || current_BWP->mcs_table == 2) ? 28 : 27;
1927:     const int max_mcs = min(bo->max_mcs, max_mcs_table);
1928:     if (nrmac->ul_mcs_scan_enabled) {
1929:       uint8_t target_mcs;
1930:       if (nrmac->ul_mcs_scan_auto_sweep) {
1931:         uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;
1932:         uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);
1933:         uint8_t scan_start = nrmac->ul_mcs_scan_start;
1934:         if (scan_start < scan_min) scan_start = scan_min;
1935:         if (scan_start > scan_max) scan_start = scan_max;
1936:         int mcs_range = scan_max - scan_min + 1;
1937:         uint32_t period = nrmac->ul_mcs_scan_period;
1938:         uint32_t cb_period = nrmac->ul_mcs_scan_cb_period;
1939:         
1940:         if (nrmac->ul_mcs_scan_last_frame != frame) {
1941:           nrmac->ul_mcs_scan_last_frame = frame;
1942:           
1943:           int mcs_index = nrmac->ul_mcs_scan_current_index;
1944:           int upper_range = scan_max - scan_start + 1;
1945:           uint8_t current_mcs;
1946:           if (mcs_index < upper_range) {
1947:             current_mcs = scan_start + mcs_index;
1948:           } else {
1949:             current_mcs = scan_min + (mcs_index - upper_range);
1950:           }
1951:           
1952:           nrmac->ul_mcs_scan_accum_frames++;
1953:           nrmac->ul_mcs_scan_cb_accum_frames++;
1954:           
1955:           if (nrmac->ul_mcs_scan_accum_frames >= period) {
1956:             nrmac->ul_mcs_scan_accum_frames = 0;
1957:             nrmac->ul_mcs_scan_cb_progress[current_mcs] = nrmac->ul_mcs_scan_current_cb_index;
1958:             nrmac->ul_mcs_scan_current_index++;
1959:             if (nrmac->ul_mcs_scan_current_index >= mcs_range) {
1960:               nrmac->ul_mcs_scan_current_index = 0;
1961:             }
1962:             nrmac->ul_mcs_scan_cb_accum_frames = 0;
1963:           }
1964:         }
1965:         
1966:         int mcs_index = nrmac->ul_mcs_scan_current_index;
1967:         int upper_range = scan_max - scan_start + 1;
1968:         if (mcs_index < upper_range) {
1969:           target_mcs = scan_start + mcs_index;
1970:         } else {
1971:           target_mcs = scan_min + (mcs_index - upper_range);
1972:         }
1973:         
1974:         if (nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs] == 0) {
1975:           uint16_t R;
1976:           uint8_t Qm;
1977:           update_ul_ue_R_Qm(target_mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &R, &Qm);
1978:           compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,
1979:                                          nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],

(Showing lines 1880-1979 of 2827. Use offset=1980 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 81.6s)

_Thinking:_

我看到了需要修改的扫描逻辑代码。让我继续读取更多内容，了解完整的需要替换的代码块。

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "limit": 60,
  "offset": 1978
}
```

**Output:**
```
<path>/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c</path>
<type>file</type>
<content>
1978:           compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,
1979:                                          nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],
1980:                                          &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);
1981:           nrmac->ul_mcs_scan_cb_progress[target_mcs] = 0;
1982:         }
1983:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
1984:         for(int i=0;i<nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];i++){
1985:           LOG_W(NR_MAC,"MCS %d CB %d RB %d\n", target_mcs, i, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs][i]);
1986:         }
1987:         LOG_W(NR_MAC,"-------RB SCAN DEBUG------\n");
1988:         nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];
1989:         nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];
1990:         memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], 
1991:                sizeof(nrmac->ul_mcs_scan_rb_values));
1992:         
1993:         if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {
1994:           nrmac->ul_mcs_scan_cb_accum_frames = 0;
1995:           if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {
1996:             nrmac->ul_mcs_scan_current_cb_index++;
1997:             nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;
1998:           }
1999:         }
2000:         
2001:         uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;
2002:         uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;
2003:         LOG_W(NR_MAC,"%d.%d UL MCS SWEEP: mcs=%d, cb_idx=%d/%d, rb=%d\n",
2004:               frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);
2005:       } else {
2006:         target_mcs = nrmac->ul_mcs_scan_ref;
2007:       }
2008:       sched_pusch->mcs = min(target_mcs, max_mcs);
2009:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2010:     } else if (bo->harq_round_max == 1) {
2011:       sched_pusch->mcs = max_mcs;
2012:       sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;
2013:     } else {
2014:       sched_pusch->mcs = get_mcs_from_bler(bo, stats, &sched_ctrl->ul_bler_stats, max_mcs, frame);
2015:       LOG_W(NR_MAC,"%d.%d starting mcs %d bleri %f,bo->max_mcs = %d\n", frame, slot, sched_pusch->mcs, sched_ctrl->ul_bler_stats.bler,bo->max_mcs);
2016:     }
2017:     // LOG_W(NR_MAC,"sched_pusch->mcs = %d",sched_pusch->mcs);
2018:     /* Schedule UE on SR or UL inactivity and no data (otherwise, will be scheduled
2019:      * based on data to transmit) */
2020:     if (B == 0 && do_sched) {
2021:       /* if no data, pre-allocate 5RB */
2022:       /* Find a free CCE */
2023:       int CCEIndex = get_cce_index(nrmac,
2024:                                    CC_id, slot, UE->rnti,
2025:                                    &sched_ctrl->aggregation_level,
2026:                                    dci_beam.idx,
2027:                                    sched_ctrl->search_space,
2028:                                    sched_ctrl->coreset,
2029:                                    &sched_ctrl->sched_pdcch,
2030:                                    false,
2031:                                    sched_ctrl->pdcch_cl_adjust);
2032:       if (CCEIndex < 0) {
2033:         LOG_D(NR_MAC, "[UE %04x][%4d.%2d] no free CCE for UL DCI (BSR 0)\n", UE->rnti, frame, slot);
2034:         reset_beam_status(&nrmac->beam_info, sched_frame, sched_slot, UE->UE_beam_index, slots_per_frame, beam.new_beam);
2035:         reset_beam_status(&nrmac->beam_info, frame, slot, UE->UE_beam_index, slots_per_frame, dci_beam.new_beam);
2036:         continue;
2037:       }

(Showing lines 1978-2037 of 2827. Use offset=2038 to continue.)
</content>
```

---

## Assistant (Build · glm-5 · 76.8s)

_Thinking:_

现在我需要替换从第1928行到第2016行的扫描逻辑代码。让我一次性替换整个代码块。

**Tool: edit**

**Input:**
```json
{
  "filePath": "/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c",
  "newString": "    if (nrmac->ul_mcs_scan_enabled) {\n      uint8_t target_mcs;\n      if (nrmac->ul_mcs_scan_auto_sweep) {\n        uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;\n        uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);\n        uint8_t scan_start = nrmac->ul_mcs_scan_start;\n        if (scan_start < scan_min) scan_start = scan_min;\n        if (scan_start > scan_max) scan_start = scan_max;\n        int mcs_range = scan_max - scan_min + 1;\n        uint32_t period = nrmac->ul_mcs_scan_period;\n        uint32_t rb_period = nrmac->ul_mcs_scan_rb_period;\n        \n        if (nrmac->ul_mcs_scan_last_frame != frame) {\n          nrmac->ul_mcs_scan_last_frame = frame;\n          \n          nrmac->ul_mcs_scan_accum_frames++;\n          nrmac->ul_mcs_scan_rb_accum_frames++;\n          \n          if (nrmac->ul_mcs_scan_accum_frames >= period) {\n            nrmac->ul_mcs_scan_accum_frames = 0;\n            nrmac->ul_mcs_scan_current_index++;\n            if (nrmac->ul_mcs_scan_current_index >= mcs_range) {\n              nrmac->ul_mcs_scan_current_index = 0;\n            }\n            nrmac->ul_mcs_scan_current_rb = 5;\n          }\n          \n          if (nrmac->ul_mcs_scan_rb_accum_frames >= rb_period) {\n            nrmac->ul_mcs_scan_rb_accum_frames = 0;\n            nrmac->ul_mcs_scan_current_rb = (nrmac->ul_mcs_scan_current_rb + 5) % 274;\n            if (nrmac->ul_mcs_scan_current_rb < 5) nrmac->ul_mcs_scan_current_rb = 5;\n          }\n        }\n        \n        int mcs_index = nrmac->ul_mcs_scan_current_index;\n        int upper_range = scan_max - scan_start + 1;\n        if (mcs_index < upper_range) {\n          target_mcs = scan_start + mcs_index;\n        } else {\n          target_mcs = scan_min + (mcs_index - upper_range);\n        }\n        \n        LOG_W(NR_MAC,\"%d.%d UL MCS SWEEP: mcs=%d, rb=%d\\n\",\n              frame, slot, target_mcs, nrmac->ul_mcs_scan_current_rb);\n      } else {\n        target_mcs = nrmac->ul_mcs_scan_ref;\n      }\n      sched_pusch->mcs = min(target_mcs, max_mcs);\n      sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;\n    } else if (bo->harq_round_max == 1) {",
  "oldString": "    if (nrmac->ul_mcs_scan_enabled) {\n      uint8_t target_mcs;\n      if (nrmac->ul_mcs_scan_auto_sweep) {\n        uint8_t scan_min = nrmac->ul_mcs_scan_min_mcs;\n        uint8_t scan_max = min(nrmac->ul_mcs_scan_max_mcs, max_mcs);\n        uint8_t scan_start = nrmac->ul_mcs_scan_start;\n        if (scan_start < scan_min) scan_start = scan_min;\n        if (scan_start > scan_max) scan_start = scan_max;\n        int mcs_range = scan_max - scan_min + 1;\n        uint32_t period = nrmac->ul_mcs_scan_period;\n        uint32_t cb_period = nrmac->ul_mcs_scan_cb_period;\n        \n        if (nrmac->ul_mcs_scan_last_frame != frame) {\n          nrmac->ul_mcs_scan_last_frame = frame;\n          \n          int mcs_index = nrmac->ul_mcs_scan_current_index;\n          int upper_range = scan_max - scan_start + 1;\n          uint8_t current_mcs;\n          if (mcs_index < upper_range) {\n            current_mcs = scan_start + mcs_index;\n          } else {\n            current_mcs = scan_min + (mcs_index - upper_range);\n          }\n          \n          nrmac->ul_mcs_scan_accum_frames++;\n          nrmac->ul_mcs_scan_cb_accum_frames++;\n          \n          if (nrmac->ul_mcs_scan_accum_frames >= period) {\n            nrmac->ul_mcs_scan_accum_frames = 0;\n            nrmac->ul_mcs_scan_cb_progress[current_mcs] = nrmac->ul_mcs_scan_current_cb_index;\n            nrmac->ul_mcs_scan_current_index++;\n            if (nrmac->ul_mcs_scan_current_index >= mcs_range) {\n              nrmac->ul_mcs_scan_current_index = 0;\n            }\n            nrmac->ul_mcs_scan_cb_accum_frames = 0;\n          }\n        }\n        \n        int mcs_index = nrmac->ul_mcs_scan_current_index;\n        int upper_range = scan_max - scan_start + 1;\n        if (mcs_index < upper_range) {\n          target_mcs = scan_start + mcs_index;\n        } else {\n          target_mcs = scan_min + (mcs_index - upper_range);\n        }\n        \n        if (nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs] == 0) {\n          uint16_t R;\n          uint8_t Qm;\n          update_ul_ue_R_Qm(target_mcs, current_BWP->mcs_table, current_BWP->pusch_Config, &R, &Qm);\n          compute_rb_boundaries_for_mcs(target_mcs, R, Qm, 12, 24, 1,\n                                         nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs],\n                                         &nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs]);\n          nrmac->ul_mcs_scan_cb_progress[target_mcs] = 0;\n        }\n        LOG_W(NR_MAC,\"-------RB SCAN DEBUG------\\n\");\n        for(int i=0;i<nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];i++){\n          LOG_W(NR_MAC,\"MCS %d CB %d RB %d\\n\", target_mcs, i, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs][i]);\n        }\n        LOG_W(NR_MAC,\"-------RB SCAN DEBUG------\\n\");\n        nrmac->ul_mcs_scan_current_cb_index = nrmac->ul_mcs_scan_cb_progress[target_mcs];\n        nrmac->ul_mcs_scan_max_cb = nrmac->ul_mcs_scan_max_cb_per_mcs[target_mcs];\n        memcpy(nrmac->ul_mcs_scan_rb_values, nrmac->ul_mcs_scan_rb_values_per_mcs[target_mcs], \n               sizeof(nrmac->ul_mcs_scan_rb_values));\n        \n        if (cb_period > 0 && nrmac->ul_mcs_scan_cb_accum_frames >= cb_period) {\n          nrmac->ul_mcs_scan_cb_accum_frames = 0;\n          if (nrmac->ul_mcs_scan_current_cb_index + 1 < nrmac->ul_mcs_scan_max_cb) {\n            nrmac->ul_mcs_scan_current_cb_index++;\n            nrmac->ul_mcs_scan_cb_progress[target_mcs] = nrmac->ul_mcs_scan_current_cb_index;\n          }\n        }\n        \n        uint8_t cb_idx = nrmac->ul_mcs_scan_current_cb_index;\n        uint16_t target_rb = (cb_idx < 32) ? nrmac->ul_mcs_scan_rb_values[cb_idx] : 273;\n        LOG_W(NR_MAC,\"%d.%d UL MCS SWEEP: mcs=%d, cb_idx=%d/%d, rb=%d\\n\",\n              frame, slot, target_mcs, cb_idx, nrmac->ul_mcs_scan_max_cb-1, target_rb);\n      } else {\n        target_mcs = nrmac->ul_mcs_scan_ref;\n      }\n      sched_pusch->mcs = min(target_mcs, max_mcs);\n      sched_ctrl->ul_bler_stats.mcs = sched_pusch->mcs;\n    } else if (bo->harq_round_max == 1) {"
}
```

**Output:**
```
Edit applied successfully.

LSP errors detected in this file, please fix:
<diagnostics file="/home/bupt/wlh/ran/openair2/LAYER2/NR_MAC_gNB/gNB_scheduler_ulsch.c">
ERROR [32:10] 'LAYER2/NR_MAC_gNB/mac_proto.h' file not found
ERROR [58:16] Unknown type name 'gNB_MAC_INST' (fix available)
ERROR [61:3] Call to undeclared function 'NR_SCHED_ENSURE_LOCKED'; ISO C99 and later do not support implicit function declarations (fix available)
ERROR [64:3] Use of undeclared identifier 'frame_structure_t'
ERROR [64:22] Use of undeclared identifier 'fs'
ERROR [66:7] Use of undeclared identifier 'fs'
ERROR [66:25] Use of undeclared identifier 'TDD'
ERROR [68:13] Call to undeclared function 'get_slot_idx_in_period'; ISO C99 and later do not support implicit function declarations
ERROR [68:42] Use of undeclared identifier 'fs'
ERROR [69:5] Use of undeclared identifier 'tdd_bitmap_t'
ERROR [69:19] Use of undeclared identifier 'tdd_slot_bitmap'
ERROR [69:37] Use of undeclared identifier 'fs'
ERROR [70:10] Use of undeclared identifier 'tdd_slot_bitmap'
ERROR [70:52] Call to undeclared function 'is_mixed_slot'; ISO C99 and later do not support implicit function declarations
ERROR [70:69] Use of undeclared identifier 'fs'
ERROR [76:3] Call to undeclared function 'UE_iterator'; ISO C99 and later do not support implicit function declarations
ERROR [76:36] Use of undeclared identifier 'UE'
ERROR [76:40] Expected ';' after expression (fix available)
ERROR [77:5] Use of undeclared identifier 'NR_sched_srs_t'
ERROR [78:8] Use of undeclared identifier 'sched_srs'
... and 1 more
</diagnostics>
```

---

## Assistant (Build · glm-5)

---

