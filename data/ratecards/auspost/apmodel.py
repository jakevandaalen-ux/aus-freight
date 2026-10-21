import json,csv,collections,math
T=json.load(open('/home/claude/au/ap/ap_tables.json'))
TAB={}
for s in T: TAB.setdefault((s['zone'],s['svc']),s['t'])
P=json.load(open('/home/claude/au/postcodes.json'));PI={p[0]:i for i,p in enumerate(P)}
obs=json.load(open('ap_obs.json'))
NEAR={'Q0':{'NSW','VIC','ACT'},'S0':{'NSW','VIC','ACT'},'V0':{'NSW','ACT','QLD','SA','TAS'},'W0':set()}
HOME={'Q0':'QLD','S0':'SA','V0':'VIC','W0':'WA'}
cls=collections.defaultdict(collections.Counter)
for k,cn in obs.items():
    lz,pc=k.split('|')
    c=max(cn,key=cn.get);r,kk=c.split('|')
    cls[pc]['Capital' if kk in('Capital','Local') else kk]+=cn[c]
C={pc:max(cn,key=cn.get) for pc,cn in cls.items() if pc in PI}
known=[(pc,C[pc]) for pc in C]
def guess(i):
    p=P[i];best=None
    for pc,c in known:
        q=P[PI[pc]]
        if q[3]!=p[3] or min(q[7],2)!=min(p[7],2): continue
        d=(q[1]-p[1])**2+((q[2]-p[2])*0.85)**2
        if best is None or d<best[0]: best=(d,c)
    if best: return best[1]
    return ['Capital','Metro','Remote','Remote'][max(0,p[7])] 
CLS=[]
for i,p in enumerate(P):
    CLS.append(C.get(p[0]) or guess(i))
def cat(lz,i):
    p=P[i];c=CLS[i];st=p[3]
    if st==HOME[lz]: return 'Same State|Local' if c=='Capital' else 'Same State|'+c
    rel='Near State' if st in NEAR[lz] else 'Distant State'
    return rel+'|'+c
def price(lz,svc,i,kg):
    r=TAB[(lz,svc)][cat(lz,i)]
    if not r or r[0] is None: return None
    if kg<=0.25: return r[0]
    if kg<=0.5: return r[1]
    if kg<=1: return r[2]
    if kg<=3: return r[3]
    if kg<=5: return r[4]
    if kg<=22: return r[5]+r[7]*math.ceil(kg)
    return None
if __name__=='__main__':
    FUEL={'2026-06':1.195,'2026-07':1.123,'2026-08':1.099,'2026-09':1.069,'2026-10':1.115}
    S=list(csv.DictReader(open('/root/.claude/uploads/7482834f-b21e-50de-907c-df914ce1f654/2ec0edec-20261020_022936.csv',encoding='utf-8-sig')))
    def f(x):
        try:return float(x)
        except:return 0
    n=ok=0;inv=[];errs=collections.Counter()
    for s in S:
        sc=s['Service Code']
        if not sc.startswith('AP') or s['Receiver Postcode'] not in PI: continue
        est=f(s['Est. Cost Ex G.S.T']);fu=FUEL.get(s['Despatch Date'][:7])
        if est<=0 or not fu: continue
        lz={'APM':'V0','APB':'Q0','APA':'S0','APP':'W0'}[sc[:3]];svc='Parcel Post' if '3D' in sc else 'Express Post'
        it=max(1,int(f(s['Items'])));p=price(lz,svc,PI[s['Receiver Postcode']],max(f(s['Weight']),f(s['Volume'])*250)/it);p=p and p*it
        if p is None: continue
        m=p/1.1*fu;n+=1
        if abs(m-est)/est<0.03: ok+=1
        else: errs[round(est/m,1)]+=1
        iv=f(s['Invoiced Cost Ex. GST'])
        if iv>0: inv.append(iv/m)
    inv.sort()
    print('model vs est within 3%:',ok,'/',n,errs.most_common(8))
    print(collections.Counter(CLS))
    json.dump({'cls':''.join({'Capital':'C','Metro':'M','Remote':'R'}[c] for c in CLS)},open('ap_cls.json','w'))
