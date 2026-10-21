import json,csv,collections,math
T=json.load(open('/home/claude/au/ap/ap_tables.json'))
TAB={}
for s in T: TAB.setdefault((s['zone'],s['svc']),s['t'])
def price(t,cat,kg):
    r=t[cat]
    if not r or r[0] is None: return None
    if kg<=0.25: return r[0]
    if kg<=0.5: return r[1]
    if kg<=1: return r[2]
    if kg<=3: return r[3]
    if kg<=5: return r[4]
    if kg<=22: return r[5]+r[7]*math.ceil(kg)
    return None
FUEL={'2026-06':1.195,'2026-07':1.123,'2026-08':1.099,'2026-09':1.069,'2026-10':1.115}
LZ={'NSW':'N0','VIC':'V0','QLD':'Q0','SA':'S0','WA':'W0','TAS':'T0','ACT':'CB'}
WHPC={'2170':'NSW','4500':'QLD','3061':'VIC','5000':'SA','6065':'WA','2609':'ACT','7009':'TAS'}
S=list(csv.DictReader(open('/root/.claude/uploads/7482834f-b21e-50de-907c-df914ce1f654/2ec0edec-20261020_022936.csv',encoding='utf-8-sig')))
def f(x):
    try:return float(x)
    except:return 0
P={p[0]:p for p in json.load(open('/home/claude/au/postcodes.json'))}
obs=collections.defaultdict(collections.Counter);tot=0;ok=0
for s in S:
    sc=s['Service Code']
    if not sc.startswith('AP') or s['Sender Postcode'] not in WHPC: continue
    svc='Parcel Post' if '3D' in sc else 'Express Post'
    it=max(1,int(f(s['Items'])));est=f(s['Est. Cost Ex G.S.T']);kg=max(f(s['Weight']),f(s['Volume'])*250)/it;fu=FUEL.get(s['Despatch Date'][:7])
    if est<=0 or not fu: continue
    lz={'APM':'V0','APB':'Q0','APA':'S0','APP':'W0'}[sc[:3]];t=TAB[(lz,svc)];tot+=1
    m=[c for c in t if (p:=price(t,c,kg)) and abs(est-p*it/1.1*fu)<=0.03]
    if m: ok+=1
    for c in m: obs[(lz,s['Receiver Postcode'])][c]+=1/len(m)
print(tot,ok)
# relation per (lz, dest state) and class per dest postcode
rel=collections.defaultdict(collections.Counter);cls=collections.defaultdict(collections.Counter)
for (lz,pc),cn in obs.items():
    if pc not in P: continue
    c=cn.most_common(1)[0][0];r,k=c.split('|')
    rel[(lz,P[pc][3])][r if k!='Local' else 'Local']+=1
    cls[pc]['Capital' if k in('Capital','Local') else k]+=1
for k in sorted(rel): print(k,dict(rel[k]))
cz=collections.Counter()
for pc,cn in cls.items(): cz[(P[pc][7],cn.most_common(1)[0][0])]+=1
print(sorted(cz.items()))
json.dump({f'{a}|{b}':dict(c) for (a,b),c in obs.items()},open('ap_obs.json','w'))
