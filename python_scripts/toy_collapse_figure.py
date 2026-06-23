#!/usr/bin/env python3
"""Collapse figure: compute backlog (carry) is the SOLE driver of not_detected.
Pool every per-slot (carry, class-A not_detected) across ALL PRB (93..273) x cache
(NO_CACHE/LOW/XXHIGH). If backlog is the only driver, all curves of P(nd|carry)
collapse onto ONE master curve with a knee at D≈2500µs — whether backlog was pushed
up via PRB or via cache. Strict: shared-wrap UE_TX/UE_ULG same axis; tb_size δ + verify;
clip to UE_ULG coverage; class-A = nd & (a-δ)∉UE_ULG.
"""
import csv, re, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

PRBS=[93,123,153,183,213,243,273]
RAW="toy_experiment/raw_data/%dPRB_016_1_100Mudp-UE.log"
DEC="toy_experiment/p%d.csv"; SAMP="output/toy_p%d/scheduled_ul_backlog_samples.csv"

def process(p):
    TX=set(); ULG=set(); txk=collections.defaultdict(list); wrap=0; prev=None
    for l in open(RAW%p):
        mt=re.search(r'\[UE TX\] (\d+)\.(\d+): harq_pid=\d+, tb_size=(\d+)',l)
        mu=re.search(r'ue_ulgrant\] (\d+)\.(\d+) rnti',l)
        m=mt or mu
        if not m: continue
        f=int(m.group(1))
        if prev is not None and f<prev-500: wrap+=1
        prev=f; a=(f+1024*wrap)*20+int(m.group(2))
        if mt: TX.add(a); txk[(int(m.group(1)),int(m.group(2)),int(m.group(3)))].append(a)
        else: ULG.add(a)
    d=collections.Counter(); gdec=[]
    for r in csv.DictReader(open(DEC%p)):
        a=r.get('scheduled_ul_abs_slot')
        if a in (None,''): continue
        a=int(a); gdec.append(a)
        k=(int(r['scheduled_ul_frame']),int(r['scheduled_ul_slot']),int(r['TBS']) if r.get('TBS') not in (None,'') else -1)
        for ua in txk.get(k,[]): d[a-ua]+=1
    D=d.most_common(1)[0][0]
    ver=100*sum(1 for a in gdec if (a-D) in TX)/max(len(gdec),1)
    lo,hi=min(ULG),max(ULG)
    carry=[]; lab=[]; state=[]; out=0; tot=0
    for r in csv.DictReader(open(SAMP%p)):
        a=r.get('scheduled_ul_abs_slot')
        if a in (None,''): continue
        a=int(a); nd=int(r['target_not_detected']); tot+=nd
        if not (lo<=a-D<=hi):
            out+=nd; continue
        carry.append(float(r['carry_before_us']))
        lab.append(1 if (nd==1 and (a-D) not in ULG) else 0)
        state.append(r.get('source_timeline_stress_level','?'))
    print('%dPRB δ=%d verify=%.1f%% n=%d nd_out_of_coverage=%d/%d'%(p,D,ver,len(carry),out,tot))
    return np.array(carry),np.array(lab),np.array(state)

EDGES=np.array([0,250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3500,4000,5000,8000])
ctr=0.5*(EDGES[:-1]+EDGES[1:])
def curve(carry,lab):
    x=[];y=[]
    for i in range(len(EDGES)-1):
        m=(carry>=EDGES[i])&(carry<EDGES[i+1])
        if m.sum()>=30: x.append(ctr[i]); y.append(lab[m].mean())
    return np.array(x),np.array(y)

data={p:process(p) for p in PRBS}
allc=np.concatenate([data[p][0] for p in PRBS])
alll=np.concatenate([data[p][1] for p in PRBS])
alls=np.concatenate([data[p][2] for p in PRBS])
xx,yy=curve(allc,alll)

fig,ax=plt.subplots(1,2,figsize=(13.5,5.3))
cmap=plt.cm.tab10(np.arange(len(PRBS)))
for c,p in zip(cmap,PRBS):
    x,y=curve(data[p][0],data[p][1])
    ax[0].plot(x,y,'-o',ms=4,color=c,lw=1.6,label='%d PRB'%p,alpha=.85)
ax[0].plot(xx,yy,'k--',lw=2.6,label='pooled',zorder=10)
ax[0].set_xlabel('compute backlog (µs)'); ax[0].set_ylabel(r'$P(\mathrm{deadline\ miss}\mid\mathrm{backlog}{=}x)$')
ax[0].set_title('(a) backlog increased via PRB (93–273)'); ax[0].legend(fontsize=8,ncol=2)
ax[0].grid(alpha=.3); ax[0].set_xlim(0,5000); ax[0].set_ylim(-.02,1.02)

for st,col,lab in [('NO_CACHE','tab:green','NO_CACHE'),('LOW','tab:orange','LOW'),('XXHIGH','tab:red','HIGH')]:
    m=alls==st; x,y=curve(allc[m],alll[m])
    ax[1].plot(x,y,'-o',ms=4,color=col,lw=1.8,label=lab,alpha=.9)
ax[1].plot(xx,yy,'k--',lw=2.6,label='pooled',zorder=10)
ax[1].set_xlabel('compute backlog (µs)'); ax[1].set_ylabel(r'$P(\mathrm{deadline\ miss}\mid\mathrm{backlog}{=}x)$')
ax[1].set_title('(b) backlog increased via cache (NO_CACHE/LOW/HIGH)'); ax[1].legend(fontsize=9)
ax[1].grid(alpha=.3); ax[1].set_xlim(0,5000); ax[1].set_ylim(-.02,1.02)
plt.tight_layout(); plt.savefig('output/toy_collapse.png',dpi=140)
print('saved output/toy_collapse.png  pooled n=%d nd=%d'%(len(allc),int(alll.sum())))
