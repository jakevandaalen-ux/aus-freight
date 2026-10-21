import re,json
L=open('/home/claude/au/ap/ap.txt').read().split('\n')
sec=[];cur=None;group=None
CATS=[('Same State','Local'),('Same State','Metro'),('Same State','Remote'),('Near State','Capital'),('Near State','Metro'),('Near State','Remote'),('Distant State','Capital'),('Distant State','Metro'),('Distant State','Remote')]
for i,l in enumerate(L):
    m=re.search(r'Lodgement Zone: (.*)\((\w+)\)',l)
    if m: cur={'zone':m.group(2),'name':m.group(1).strip(),'rows':[]};continue
    if cur and l.strip() in('Parcel Post','Express Post'): cur['svc']=l.strip();sec.append(cur);continue
    if cur and 'svc' in cur:
        m=re.match(r'\s*(Same State|Near State|Distant State)?\s*(Local|Metro|Remote|Capital)\s+(.*)$',l)
        if m and ('$' in l or 'N/A' in l):
            vals=re.findall(r'\$([\d.]+)|N/A',m.group(3))
            nums=[float(x) if x else None for x in re.findall(r'\$([\d.]+)|(N/A)',m.group(3)) and [a if a else None for a,b in re.findall(r'\$([\d.]+)|(N/A)',m.group(3))]]
            cur['rows'].append((m.group(2),nums))
out=[]
for s in sec:
    rows=s['rows']
    assert len(rows)==9,(s['zone'],len(rows))
    t={f'{CATS[i][0]}|{CATS[i][1]}':rows[i][1] for i in range(9)}
    out.append({'zone':s['zone'],'svc':s['svc'],'t':t})
for o in out: print(o['zone'],o['svc'],o['t']['Same State|Local'],o['t']['Distant State|Remote'])
json.dump(out,open('ap_tables.json','w'))
