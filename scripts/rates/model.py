import json,collections,math,statistics as st
A='/home/claude/au/'
M=json.load(open(A+'matched.json'));P=json.load(open(A+'postcodes.json'));WH=json.load(open(A+'warehouses.json'));W=json.load(open(A+'webrates.json'))
over={int(k):v for k,v in W['over'].items()}
STS=['ACT','NSW','NT','QLD','SA','TAS','VIC','WA']
WHST={w[0]:w for w in WH}
def km(a,b):
    r=math.pi/180;dl=(b[0]-a[0])*r;dn=(b[1]-a[1])*r
    x=math.sin(dl/2)**2+math.cos(a[0]*r)*math.cos(b[0]*r)*math.sin(dn/2)**2;return 2*6371*math.asin(math.sqrt(x))
CAP={'ACT':(-35.28,149.13),'NSW':(-33.87,151.21),'NT':(-12.46,130.84),'QLD':(-27.47,153.03),'SA':(-34.93,138.6),'TAS':(-42.88,147.33),'VIC':(-37.81,144.96),'WA':(-31.95,115.86)}
def tmean(v):
    v=sorted(v);k=int(len(v)*0.1);v=v[k:len(v)-k] if len(v)-2*k>0 else v;return sum(v)/len(v)
rows=[]
for r in M:
    pi,wi,ci,ch,co=r[0],r[1],r[2],r[3],r[4];sz=r[16]
    if r[8]!=1 or r[9]!=1 or not sz or wi<0 or co<=0 or (len(r)>23 and r[23]): continue
    z=P[pi][7]
    if z<0 or z>2: continue
    dst=over.get(pi,P[pi][3]);fr=WH[wi][0]
    rows.append(dict(dst=dst,fr=fr,sz=sz-1,z=z,c=co*1.1,ch=ch,loc=dst==fr))
# 1. base cells loc x size x zone, smoothed with log-linear model
cell=collections.defaultdict(list)
for x in rows: cell[(x['loc'],x['sz'],x['z'])].append(x['c'])
# log-linear: log c = a_loc + b_sz(loc) + c_z(loc)  fit by weighted means iteratively
eff={}
for loc in (True,False):
    S=[0]*5;Z=[0]*3
    for it in range(50):
        for s in range(5):
            num=den=0
            for z in range(3):
                v=cell.get((loc,s,z),[])
                if v: n=len(v);num+=n*(math.log(tmean(v))-Z[z]);den+=n
            if den: S[s]=num/den
        for z in range(1,3):
            num=den=0
            for s in range(5):
                v=cell.get((loc,s,z),[])
                if v: n=len(v);num+=n*(math.log(tmean(v))-S[s]);den+=n
            Z[z]=num/den
    eff[loc]=(S,Z)
base={}
for loc in (True,False):
    S,Z=eff[loc]
    for s in range(5):
        for z in range(3):
            m=math.exp(S[s]+Z[z]);v=cell.get((loc,s,z),[]);n=len(v)
            base[(loc,s,z)]=(n*tmean(v)+15*m)/(n+15) if n else m
# 2. lane factors
lane=collections.defaultdict(list)
for x in rows: lane[(x['dst'],x['fr'])].append(x['c']/base[(x['loc'],x['sz'],x['z'])])
LF={}
pts=[]
for k,v in lane.items():
    F=st.median(v);n=len(v);LF[k]=(F,n)
    if k[0]!=k[1] and n>=8: pts.append((math.log(km(CAP[k[0]],(WHST[k[1]][4],WHST[k[1]][5]))),math.log(F),n))
# regression of interstate lane factor on log distance
sw=sum(n for *_,n in pts);mx=sum(x*n for x,_,n in pts)/sw;my=sum(y*n for _,y,n in pts)/sw
b=sum(n*(x-mx)*(y-my) for x,y,n in pts)/sum(n*(x-mx)**2 for x,_,n in pts);a=my-b*mx
def lanef(dst,fr):
    if dst==fr:
        F,n=LF.get((dst,fr),(1,0));return (n*F+10)/(n+10),n
    prior=math.exp(a+b*math.log(km(CAP[dst],(WHST[fr][4],WHST[fr][5]))))
    F,n=LF.get((dst,fr),(prior,0));return (n*F+30*prior)/(n+30),n   # thin interstate lanes lean on distance
# lane factor by size group (Small / Medium / Large and up), shrunk toward the lane's overall factor and kept within 0.6-1.6x
G=lambda s:0 if s==0 else 1 if s==1 else 2
lg_=collections.defaultdict(list)
for x in rows: lg_[(x['dst'],x['fr'],G(x['sz']))].append(x['c']/base[(x['loc'],x['sz'],x['z'])])
def lanefg(dst,fr,s):
    F0,nl=lanef(dst,fr);v=lg_.get((dst,fr,G(s)),[]);n=len(v)
    F=(n*st.median(v)+20*F0)/(n+20) if n else F0
    return min(1.6,max(0.6,F)),nl
lcell=collections.defaultdict(list)
for x in rows: lcell[(x['dst'],x['fr'],x['sz'],x['z'])].append(x['c'])
EST={};INFO={}
for dst in STS:
    for fr in WHST:
        loc=dst==fr
        for s in range(5):
            F,nl=lanefg(dst,fr,s)
            for z in range(3):
                e=base[(loc,s,z)]*F;v=lcell.get((dst,fr,s,z),[]);n=len(v)
                if n: e=(n*tmean(v)+(10 if loc else 20)*e)/(n+(10 if loc else 20))
                EST[(dst,fr,s,z)]=e;INFO[(dst,fr,s,z)]=(n,nl,F)
# a warehouse's own state should never cost more than shipping in from another state: cap same-state at the cheapest interstate lane
CAPPED=set()
for dst in STS:
    if dst not in WHST: continue
    for s in range(5):
        for z in range(3):
            other=min(EST[(d,f,s,z)] for (d,f,s2,z2) in [(dst,f,s,z) for f in WHST if f!=dst])
            if EST[(dst,dst,s,z)]>other: EST[(dst,dst,s,z)]=other;CAPPED.add((dst,s,z))
# monotone: sizes then zones
for dst in STS:
    for fr in WHST:
        for z in range(3):
            m=0
            for s in range(5): m=max(m,EST[(dst,fr,s,z)]);EST[(dst,fr,s,z)]=m
        for s in range(5):
            m=0
            for z in range(3): m=max(m,EST[(dst,fr,s,z)]);EST[(dst,fr,s,z)]=m
if __name__=='__main__':
    print('rows',len(rows),'dist reg a,b',round(a,3),round(b,3))
    for k in sorted(LF): print(k,round(LF[k][0],2),LF[k][1],'->',round(lanef(*k)[0],2))
    for dst in ['QLD','NSW','WA','NT']:
        for fr in [dst if dst!='NT' else 'SA','VIC']:
            print(dst,fr,[[round(EST[(dst,fr,s,z)]) for z in range(3)] for s in range(5)])
