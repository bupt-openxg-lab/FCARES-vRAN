#!/usr/bin/env python3
"""Evaluate the backlog model with budget correction (= adding FFT/TX cost into delay)
on a paired UE+gNB capture, using tb_size-based δ alignment + class-A (UE-didn't-get-DCI)
labeling. Reports D / Precision / Recall / F1 / carry==0% per budget variant.

Budget correction identity: carry+delay-(500-FFT-TX) == carry+(delay+FFT+TX)-500,
so we just append FFT/TX columns to --cost-cols and keep budget=500.
"""
import csv, re, subprocess, sys, collections
import numpy as np

PREFIX = sys.argv[1]      # e.g. threshold_test/log4   (decode csv = <PREFIX>.csv)
UE_LOG = sys.argv[2]
TAG    = sys.argv[3]      # e.g. log4

VARIANTS = {
    "B0_base(500)":            "pusch_detection_frontend_cost,codeblock_decode_cost_sum",
    "B1_+FFT":                 "pusch_detection_frontend_cost,codeblock_decode_cost_sum,ru_rx_fft_task_work_sum_cost",
    "B2_+TX":                  "pusch_detection_frontend_cost,codeblock_decode_cost_sum,tx_threadpool_sum_us",
    "B3_+FFT+TX":              "pusch_detection_frontend_cost,codeblock_decode_cost_sum,ru_rx_fft_task_work_sum_cost,tx_threadpool_sum_us",
}

# ---- UE abs_slot sets (wrap-counted, 20 slots/frame) ----
def ue_abs(pat):
    s=set(); wrap=0; prev=None
    for l in open(UE_LOG):
        m=re.search(pat,l)
        if not m: continue
        f=int(m.group(1))
        if prev is not None and f<prev-500: wrap+=1
        prev=f
        s.add((f+1024*wrap)*20+int(m.group(2)))
    return s
UE_TX  = ue_abs(r'\[UE TX\] (\d+)\.(\d+):')
UE_ULG = ue_abs(r'ue_ulgrant\] (\d+)\.(\d+) rnti')

# ---- δ from gNB decoded (decode-detail) ↔ UE TX, matched by (frame,slot,TBS) ----
def reconstruct_ue_tx_keyed():
    out=[]; wrap=0; prev=None
    for l in open(UE_LOG):
        m=re.search(r'\[UE TX\] (\d+)\.(\d+): harq_pid=\d+, tb_size=(\d+)',l)
        if not m: continue
        f=int(m.group(1))
        if prev is not None and f<prev-500: wrap+=1
        prev=f
        out.append(((f+1024*wrap)*20+int(m.group(2)), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return out
ue_tx_keyed=reconstruct_ue_tx_keyed()
ue_by_key=collections.defaultdict(list)
for a,f,s,tb in ue_tx_keyed: ue_by_key[(f,s,tb)].append(a)
deltas=collections.Counter()
gdec_abs=[]
for r in csv.DictReader(open(PREFIX+".csv")):
    a=r.get('scheduled_ul_abs_slot')
    if a in (None,''): continue
    a=int(a); gdec_abs.append(a)
    gf,gs=int(r['scheduled_ul_frame']),int(r['scheduled_ul_slot'])
    gtb=int(r['TBS']) if r.get('TBS') not in (None,'') else -1
    for ua in ue_by_key.get((gf,gs,gtb),[]):
        deltas[a-ua]+=1
DELTA=deltas.most_common(1)[0][0]
ver=sum(1 for a in gdec_abs if (a-DELTA) in UE_TX)
print("[%s] δ=%d  δ-verify(gNB-decoded has UE_TX)= %d/%d = %.1f%%"%(TAG,DELTA,ver,len(gdec_abs),100*ver/len(gdec_abs)))

def best_f1(feat,lab):
    feat=np.array(feat); lab=np.array(lab)
    if lab.sum()<5: return (float('nan'),)*4
    grid=np.unique(np.quantile(feat,np.linspace(0,1,300))); best=None
    for t in grid:
        p=feat>t; tp=int((p&(lab==1)).sum()); fp=int((p&(lab==0)).sum()); fn=int((~p&(lab==1)).sum())
        if tp+fp==0 or tp+fn==0: continue
        pr=tp/(tp+fp); rc=tp/(tp+fn); f=2*pr*rc/(pr+rc) if pr+rc else 0
        if best is None or f>best[0]: best=(f,t,pr,rc)
    return best if best else (float('nan'),)*4

print("%-16s %8s %8s %8s %8s %10s %8s"%("variant","D_us","Prec","Recall","F1","carry=0%","classA"))
for name,cols in VARIANTS.items():
    out="output/budget_%s_%s"%(TAG,name.split('_')[0])
    subprocess.run(["python3","pusch_scheduled_backlog_threshold_analyzer.py",
        "--input-prefix",PREFIX,"--cost-cols",cols,
        "--features","carry_before_us,carry_after_us","--slot-budget-us","500",
        "--output-dir",out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    feat=[]; lab=[]; carryzero=0; ntot=0; classA=0; ndtot=0
    for r in csv.DictReader(open(out+"/scheduled_ul_backlog_samples.csv")):
        a=r.get('scheduled_ul_abs_slot')
        if a in (None,''): continue
        a=int(a); nd=int(r['target_not_detected']); cb=float(r['carry_before_us'])
        ntot+=1
        if cb==0: carryzero+=1
        if nd==1:
            ndtot+=1
            is_classC = (a-DELTA) in UE_TX
            is_classA = (a-DELTA) not in UE_ULG
            if is_classA: classA+=1
            if is_classC: continue            # drop class C (UE sent, gNB lost)
        # positive = class-A nd, negative = success
        pos = 1 if (nd==1 and (a-DELTA) not in UE_ULG) else 0
        feat.append(cb); lab.append(pos)
    f1,D,pr,rc=best_f1(feat,lab)
    print("%-16s %8.0f %8.3f %8.3f %8.3f %9.1f%% %5d/%d"%(name,D,pr,rc,f1,100*carryzero/ntot,classA,ndtot))
