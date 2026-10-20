import csv,glob,collections,re
CARDS=collections.defaultdict(lambda:collections.defaultdict(dict))  # svc -> from -> to -> row
def num(x):
    try: return float(x)
    except: return None
for f in glob.glob('/home/claude/au/cards/att/*.csv'):
    for r in csv.DictReader(open(f,encoding='utf-8-sig')):
        tiers=[]
        for i in range(1,10):
            t=r.get(f'Type{i}')
            if not t: break
            tiers.append((t,num(r[f'Break{i}']),num(r[f'Basic{i}']) or 0,num(r[f'Rate{i}']) or 0))
        row=dict(cub=num(r['CubicRate']) or 250,min=num(r['Minimum']) or 0,climit=num(r['Cubic Limit']),wlimit=num(r['Weight Limit']),tiers=tiers,recip=r['Reciprocal']=='TRUE')
        CARDS[r['Service']][r['ZoneFrom'].strip()][r['ZoneTo'].strip()]=row
        if row['recip']: CARDS[r['Service']][r['ZoneTo'].strip()].setdefault(r['ZoneFrom'].strip(),row)
def price(row,kg,m3,items=1):
    items=max(1,int(items or 1))
    ch=max(kg,m3*row['cub'])
    t0=row['tiers'][0][0] if row['tiers'] else 'KG'
    if t0=='ITM':
        for t,br,ba,ra in row['tiers']:
            if items<=br: return max(row['min'],ba+ra*items)
        return None
    for t,br,ba,ra in row['tiers']:
        if ch<=br+1e-9: return max(row['min'],ba+ra*ch)
    return None
