import sys,json,collections,statistics as st;sys.path.insert(0,'/home/claude/au/bulky')
from bq import *
SUBS=json.load(open('/home/claude/au/subs.json'));sub_of={}
for n,i in SUBS: sub_of.setdefault(i,n)
M=json.load(open('/home/claude/au/matched.json'))
demand=collections.Counter(r[0] for r in M)
STS=['ACT','NSW','NT','QLD','SA','TAS','VIC','WA'];WHS=['SA','VIC','QLD','WA','ACT','TAS','NSW']
KG,M3,LG=25,0.70,2.0
# representative postcodes per (state tab, zone): top 25 by orders, else a spread of delivery postcodes
rep={}
for i,p in enumerate(P):
    if p[9]!='D' or not (0<=p[7]<=2): continue
    dst=over.get(i,p[3]);rep.setdefault((dst,p[7]),[]).append(i)
G={};N={}
for (dst,z),L in rep.items():
    L.sort(key=lambda i:-demand[i]);pick=[i for i in L if demand[i]][:25]
    if len(pick)<10: pick=(pick+L[::max(1,len(L)//15)])[:20]
    w=[max(1,demand[i]) for i in pick]
    for fr in WHS:
        vals=[];ws=[]
        for i,wt in zip(pick,w):
            q=cheapest(fr,sub_of.get(i,''),P[i][0],P[i][3],KG,M3,LG)
            if q: vals.append(q[0]);ws.append(wt)
        if vals: G[f'{dst}|{fr}|{z}']=round(sum(v*x for v,x in zip(vals,ws))/sum(ws),2);N[f'{dst}|{fr}|{z}']=len(vals)
json.dump({'cost':G,'n':N,'profile':[KG,M3,LG]},open('/home/claude/au/bulky/bulky_grid.json','w'))
for d in STS: print(d,{fr:[G.get(f'{d}|{fr}|{z}') and round(G.get(f'{d}|{fr}|{z}')) for z in range(3)] for fr in WHS})
