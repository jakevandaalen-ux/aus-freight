import sys,csv,pickle,collections
sys.path.insert(0,'/home/claude/au/eng')
from engine import CARDS,price
Z=pickle.load(open('/home/claude/au/eng2/zones.pkl','rb'))
S=list(csv.DictReader(open('/root/.claude/uploads/7482834f-b21e-50de-907c-df914ce1f654/2ec0edec-20261020_022936.csv',encoding='utf-8-sig')))
def f(x):
    try:return float(x)
    except:return 0.0
def zfile(svc):
    for p,n in [('STN','STARTRACK'),('TNT','TNT EXPRESS'),('ARAMX','ARAMEX'),('NL','NORTHLINE'),('HITRA','HI-TRANS'),('FT','FOLLOWMONT'),('COCH','COCHRANES'),('MOR','MORROWS FREIGHTLINES'),('PEPT','PEP COURIER'),('PEP','PEP'),('CVN','CIVIC NSW'),('CVQ','CIVIC QLD'),('CVV','CIVIC VIC'),('CVW','CIVIC WA'),('JCAD','JET COURIERS ADELAIDE')]:
        if svc.startswith(p): return n
def zrec(zf,town,pc):
    bys,byp=Z[zf];r=bys.get((town.strip().upper(),pc.zfill(4)))
    if r: return r
    L=byp.get(pc.zfill(4))
    if L: return collections.Counter(L).most_common(1)[0][0]
def cands(rec,mode,res):
    z,par,hub,rem=rec;out=[]
    order=[z,par] if mode=='zp' else [par,z]
    for c in order:
        if not c: continue
        if res: out.append(c+'-R')
        out.append(c)
    return out
def lookup(svc,zf,o,d,mode,res):
    dd=None
    for oc in cands(o,mode,False):
        if oc in CARDS[svc]: dd=CARDS[svc][oc];break
    if dd is None: return None,None
    for dc in cands(d,mode,res):
        if dc in dd: return dd[dc],(oc,dc)
    return None,None
def run(svc,mode='zp',resrule=None):
    zf=zfile(svc);rows=[];per=collections.defaultdict(collections.Counter)
    for s in S:
        if s['Service Code']!=svc: continue
        est=f(s['Est. Cost Ex G.S.T'])
        if est<=0: continue
        o=zrec(zf,s['Sender Town'],s['Sender Postcode']);d=zrec(zf,s['Receiver Town'],s['Receiver Postcode'])
        if not o or not d: rows.append((s,None));continue
        res=resrule(s,d) if resrule else False
        row,codes=lookup(svc,zf,o,d,mode,res)
        p=price(row,f(s['Weight']),f(s['Volume']),f(s['Items'])) if row else None
        rows.append((s,p))
        if p: per[s['Despatch Date'][:7]][round(est/p,3)]+=1
    fuel={m:c.most_common(1)[0][0] for m,c in per.items()}
    ok=sum(1 for s,p in rows if p and abs(est_:=f(s['Est. Cost Ex G.S.T']))>0 and abs(est_/p-fuel[s['Despatch Date'][:7]])<=0.01)
    priced=sum(1 for s,p in rows if p)
    return dict(n=len(rows),priced=priced,ok=ok,fuel=dict(sorted(fuel.items())))
if __name__=='__main__':
    for svc in sys.argv[1:]:
        for mode in ('zp','pz'):
            for rn,rr in [('none',None),('remote',lambda s,d:d[3]==1),('resid',lambda s,d:s['Receiver Type']=='Residential')]:
                r=run(svc,mode,rr);print(svc,mode,rn,r['n'],r['priced'],r['ok'],r['fuel'])
