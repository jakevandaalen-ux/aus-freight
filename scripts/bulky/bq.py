import sys,json,collections,statistics as st,pickle
sys.path.insert(0,'/home/claude/au/eng2');sys.path.insert(0,'/home/claude/au/eng')
from engine import price
CR=json.load(open('/home/claude/au/carriers.json'))
Z=pickle.load(open('/home/claude/au/eng2/zones.pkl','rb'))
P=json.load(open('/home/claude/au/postcodes.json'));WH=json.load(open('/home/claude/au/warehouses.json'))
W=json.load(open('/home/claude/au/webrates.json'));over={int(k):v for k,v in W['over'].items()}
STATE_ONLY={'MORC':'VIC','MORP':'VIC','COCHRX':'SA','COCHP':'SA','FTROAD':'QLD','PEPXP':'WA','PEPEZ1':'WA','PEPEZ2':'WA','PEPEZ3':'WA','PEPEZ5':'WA','CVVCOU':'VIC','CVQCOU':'QLD','CVWCOU':'WA'}
BULKY_OK=['STNROAD','TNTROAD','NLROAD','FTROAD','MORC','COCHRX','PEPEZ1','PEPEZ2','PEPEZ3','PEPEZ5','CVVCOU','CVQCOU','CVWCOU']
def dz(zf,sub,pc):
    if zf.startswith('CIVIC'): return [sub.upper()+str(int(pc))]
    bys,byp=Z[zf];r=bys.get((sub.upper(),pc))
    if not r:
        L=byp.get(pc)
        if not L: return None
        r=collections.Counter(L).most_common(1)[0][0]
    return [c for c in (r[0],r[1]) if c]
def quote(svc,whst,sub,pc,dstst,kg,m3,lg):
    sv=CR['sv'].get(svc)
    if not sv: return None
    if svc in STATE_ONLY and (whst!=STATE_ONLY[svc] or dstst!=STATE_ONLY[svc]): return None
    org=sv['org'].get(whst)
    if not org: return None
    zs=dz(sv['zf'],sub,pc)
    if not zs: return None
    row=next((org[z] for z in zs if z in org),None)
    if not row: return None
    mn,cub,tiers=row
    rr={'min':mn,'cub':cub,'tiers':[tuple(t) for t in tiers]}
    c=price(rr,kg,m3,1)
    if c is None: return None
    lc=3 if lg>=2.4 else 2 if lg>=1.8 else 1 if lg>=1.2 else 0
    return (c*sv['ratio']+(sv['sur'][lc-1] if lc else 0))*1.1
def cheapest(whst,sub,pc,dstst,kg,m3,lg):
    q=[(v,s) for s in BULKY_OK if (v:=quote(s,whst,sub,pc,dstst,kg,m3,lg))]
    return min(q) if q else None
