import sys,json,collections,statistics as st
import numpy as np
sys.path.insert(0,'/home/claude/au/eng2')
from val import S,f,zfile,zrec,lookup,price,CARDS
LG=json.load(open('/home/claude/au/eng2/sn_longest.json'))
def feats(s,svc):
    zf=zfile(svc)
    o=zrec(zf,s['Sender Town'],s['Sender Postcode']);d=zrec(zf,s['Receiver Town'],s['Receiver Postcode'])
    if not o or not d: return None
    row,codes=lookup(svc,zf,o,d,'zp',False)
    if not row: return None
    kg=f(s['Weight']);m3=f(s['Volume']);it=f(s['Items'])
    p=price(row,kg,m3,it)
    return p
OUT={}
for svc in sys.argv[1:]:
    X=[];y=[];info=[]
    for s in S:
        if s['Service Code']!=svc: continue
        if s['Despatch Date'][:7] not in ('2026-08','2026-09','2026-10'): continue
        c=f(s['Invoiced Cost Ex. GST']) or f(s['Est. Cost Ex G.S.T'])
        if c<=0: continue
        lg=LG.get(s['Shipment Number'])
        if lg is None: continue
        p=feats(s,svc)
        if not p: continue
        it=max(1,int(f(s['Items'])))
        X.append([p,1.0 if lg>=1.2 else 0,1.0 if lg>=1.8 else 0,1.0 if lg>=2.4 else 0, it-1]);y.append(c)
    if len(y)<15: print(svc,'too few',len(y));continue
    X=np.array(X);y=np.array(y)
    coef,*_=np.linalg.lstsq(X,y,rcond=None)
    pred=X@coef;err=np.abs(pred-y)/y
    base=np.abs(X[:,0]*np.median(y/X[:,0])-y)/y
    print(svc,len(y),'coef card×%.3f +L1.2 %.2f +L1.8 %.2f +L2.4 %.2f +per extra item %.2f'%tuple(coef),'median err %.0f%% (card×ratio only %.0f%%)'%(np.median(err)*100,np.median(base)*100))
    OUT[svc]=[round(float(v),3) for v in coef]
json.dump(OUT,open('/home/claude/au/eng2/fit_'+'_'.join(sys.argv[1:2])+'.json','w'))
