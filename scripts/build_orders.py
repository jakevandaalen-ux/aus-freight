import pickle,json,collections,re,datetime
A='/home/claude/au/'
R=pickle.load(open(A+'om/rows.pkl','rb'));sku2pid=pickle.load(open(A+'om/sku2pid.pkl','rb'))
P,inv=pickle.load(open(A+'prod/sized.pkl','rb'))
PCS=json.load(open(A+'postcodes.json'));PI={}
for i,p in enumerate(PCS):
    if p[0] not in PI or (p[9]=='D' and PCS[PI[p[0]]][9]!='D'): PI[p[0]]=i
WH=json.load(open(A+'warehouses.json'));WI={w[0]:i for i,w in enumerate(WH)}
W=json.load(open(A+'webrates.json'));RATES=W['R'];over={int(k):v for k,v in W['over'].items()}
CARS=json.load(open(A+'orders.json'))['CARS']
OUT={'Brisbane_Online':'QLD','Victoria_Online':'VIC','NSW_Online':'NSW','Moorebank':'NSW','WA_Online':'WA','Adelaide City':'SA','Adelaide_Online':'SA','Hobart':'TAS','Canberra':'ACT'}
BT={'Roof Boxes','Roof Top Tents'}
SERV={'RRDGUARANTEE-FIT-SILVER','RRDGUARANTEE-FIT-GOLD','NOCHARGE','PACKERROR','PRICEMATCH','COURIERISSUE','RRGCS-ISSUE','MISC1'}
def f(x):
    try:return float(x)
    except:return 0.0
def carname(c):
    c=c.strip().upper()
    if c.startswith('AUSTRALIA POST'): c='AUSTRALIA POST'
    if c not in CARS: CARS.append(c)
    return CARS.index(c)
rows=[];skip=collections.Counter();sizes=collections.Counter()
for r in R:
    pc=str(r[11] or '').strip().zfill(4)
    if pc not in PI: skip['postcode']+=1;continue
    wh=None
    for o in str(r[6] or r[5] or '').split(','):
        o=o.strip()
        if o in OUT: wh=OUT[o];break
    if not wh: wh=OUT.get(str(r[5]).strip())
    if not wh: skip['warehouse']+=1;continue
    multi_wh=len({OUT[o.strip()] for o in str(r[6] or '').split(',') if o.strip() in OUT})>1
    cars=[c for c in str(r[29] or '').split(',') if c.strip()]
    ci=carname(cars[0]) if cars else -1
    # products
    skus=[s.strip() for s in str(r[15] or '').split(',') if s.strip()]
    prods=[x.strip() for x in str(r[14] or '').split('|')]
    qty=[]
    for k,s in enumerate(skus):
        m=re.match(r'(\d+)\s*x\s',prods[k]) if k<len(prods) else None
        qty.append(int(m.group(1)) if m else 1)
    sz=0;lg=0;vol=0;bk=0;unknown=0;nodata=0
    for s,q in zip(skus,qty):
        if s.upper() in SERV: continue
        pid=sku2pid.get(s.upper());p=P.get(pid) if pid else None
        if not p: unknown=1;continue
        if not (p['dims'] or p['w']): nodata=1;continue
        sz=max(sz,p['s']);lg=max(lg,p['L'],p['D'],p['B']);vol+=q*p['L']*p['D']*p['B']
        if p['type'] in BT: bk=1
    fl=2 if unknown else 1 if nodata else 0
    i=PI[pc];z=PCS[i][7];dst=over.get(i,PCS[i][3])
    ws=wp=None
    if sz and 0<=z<=2 and wh in RATES.get(dst,{}):
        ws=RATES[dst][wh]['standard'][sz-1][z];wp=RATES[dst][wh]['priority'][sz-1][z]
    ch=f(r[23]);svc='s' if ws is not None and abs(ch-ws)<0.01 else 'p' if wp is not None and abs(ch-wp)<0.01 else ''
    date=r[28] or r[10] or r[9];date=date.strftime('%Y-%m-%d') if hasattr(date,'strftime') else ''
    nsh=int(f(r[26]) or 1)
    rows.append([i,WI[wh],ci,round(ch,2),round(f(r[30]),2),round(f(r[22]),2),round(f(r[21]),2),date,1,nsh,', '.join(f'{s}×{q}' if q>1 else s for s,q in zip(skus,qty))[:160],round(f(r[18]),2),round(vol,4),round(vol*250,2),'',str(r[0]),sz,ws,wp,svc,fl,round(lg,2),bk,1 if multi_wh else 0])
    sizes[sz]+=1
print(len(rows),skip,sizes,'bulky',sum(r[22] for r in rows),'multi-wh',sum(r[23] for r in rows))
json.dump(rows,open(A+'matched.json','w'),separators=(',',':'))
oj=json.load(open(A+'orders.json'));oj['CARS']=CARS;json.dump(oj,open(A+'orders.json','w'),separators=(',',':'))
print('charged',round(sum(r[3] for r in rows)),'cost incl',round(sum(r[4]*1.1 for r in rows)))
