import sys,json,collections,pickle,statistics as st
sys.path.insert(0,'/home/claude/au/eng2')
from val import S,f,zfile,zrec,lookup,price,CARDS,Z
LG=json.load(open('/home/claude/au/eng2/sn_longest.json'))
WHS={'SA':('ADELAIDE','5000'),'VIC':('CAMPBELLFIELD','3061'),'QLD':('BRENDALE','4500'),'WA':('WANGARA','6065'),'ACT':('FYSHWICK','2609'),'TAS':('MOONAH','7009'),'NSW':('MOOREBANK','2170')}
NAMES={'STNROAD':'StarTrack Road Express','STNFPP':'StarTrack Premium (next day)','TNTROAD':'TNT Road Express','ARAMX':'Aramex','NLROAD':'Northline','COCHRX':'Cochranes','FTROAD':'Followmont','PEPXP':'PEP metro','PEPEZ1':'PEP country zone 1','PEPEZ2':'PEP country zone 2','PEPEZ3':'PEP country zone 3','PEPEZ4':'PEP country zone 4','PEPEZ5':'PEP country zone 5','MORC':'Morrows','CVVCOU':'Civic courier (VIC)','CVQCOU':'Civic courier (QLD)','CVWCOU':'Civic courier (WA)','CVNCOU':'Civic courier (NSW)','JCADCG':'Jet Couriers (Adelaide)','HITRAG':'Hi-Trans'}
used=collections.Counter(s['Service Code'] for s in S)
out={};files=set()
for svc,name in NAMES.items():
    if svc not in CARDS: continue
    zf=zfile(svc);org={}
    for st_,(sub,pc) in WHS.items():
        o=zrec(zf,sub,pc)
        if not o: continue
        dd=None
        for oc in [o[0],o[1]]:
            if oc and oc in CARDS[svc]: dd=CARDS[svc][oc];break
        if dd: org[st_]={k:[round(v['min'],2),v['cub'],[[t[0],t[1],round(t[2],3),round(t[3],4)] for t in v['tiers']]] for k,v in dd.items()}
    if not org: continue
    # calibration: ratio from no-long shipments; surcharges by length class
    ys=collections.defaultdict(list)
    for s in S:
        if s['Service Code']!=svc or s['Despatch Date'][:7] not in ('2026-08','2026-09','2026-10'): continue
        c=f(s['Invoiced Cost Ex. GST']) or f(s['Est. Cost Ex G.S.T'])
        if c<=0: continue
        o=zrec(zf,s['Sender Town'],s['Sender Postcode']);d=zrec(zf,s['Receiver Town'],s['Receiver Postcode'])
        if not o or not d: continue
        row,_=lookup(svc,zf,o,d,'zp',False)
        if not row: continue
        p=price(row,f(s['Weight']),f(s['Volume']),f(s['Items']))
        if not p: continue
        lg=LG.get(s['Shipment Number'],None)
        k='?' if lg is None else 0 if lg<1.2 else 1 if lg<1.8 else 2 if lg<2.4 else 3
        ys[k].append((p,c))
    base=ys[0] if len(ys[0])>=5 else [x for k in ys for x in ys[k]]
    ratio=st.median([c/p for p,c in base]) if len(base)>=5 else None
    if not ratio: print('skip',svc);continue
    sur=[0,0,0]
    if ratio:
        prev=0
        for k in (1,2,3):
            v=[c-ratio*p for p,c in ys[k]]
            if len(v)>=5: prev=max(prev,st.median(v))
            sur[k-1]=round(prev,2)
    allv=[(p,c) for k in ys for p,c in ys[k]]
    out[svc]={'name':name,'zf':zf,'org':org,'ratio':round(ratio,3) if ratio else None,'sur':sur,'n':len(allv),'used':used.get(svc,0)}
    files.add(zf)
    print(svc,name,list(org),'ratio',out[svc]['ratio'],'sur',sur,'n',len(allv),'used',used.get(svc,0))
# zones per carrier file: postcode majority + suburb overrides
ZO={}
for zf in files:
    if zf.startswith('CIVIC'): ZO[zf]={'civic':1};print(zf,'derived');continue
    bys,byp=Z[zf];maj={};ov={}
    for pc,L in byp.items():
        m=collections.Counter((r[0],r[1]) for r in L).most_common(1)[0][0];maj[pc]=m[0] if not m[1] else [m[0],m[1]]
    for (sub,pc),r in bys.items():
        v=r[0] if not r[1] else [r[0],r[1]]
        if v!=maj[pc]: ov[sub+'|'+pc]=v
    ZO[zf]={'p':maj,'s':ov}
    print(zf,len(maj),len(ov))
json.dump({'sv':out,'z':ZO},open('/home/claude/au/carriers.json','w'),separators=(',',':'))
print(len(open('/home/claude/au/carriers.json').read()))
