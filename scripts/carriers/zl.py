import openpyxl,glob,os,collections,pickle
Z={}
for f in glob.glob('/home/claude/au/zones/*.xlsx'):
    name=os.path.basename(f).split(' Zone Export')[0]
    wb=openpyxl.load_workbook(f,read_only=True);ws=wb.worksheets[0]
    bys={};byp=collections.defaultdict(list)
    for i,r in enumerate(ws.iter_rows(values_only=True)):
        if i==0 or r[1] is None: continue
        sub=str(r[0]).strip().upper();pc=str(r[1]).zfill(4);rec=(str(r[3]).strip() if r[3] is not None else None,str(r[4]).strip() if r[4] else None,r[5],int(r[6] or 0))
        bys[(sub,pc)]=rec;byp[pc].append(rec)
    Z[name]=(bys,dict(byp))
    print(name,len(bys))
pickle.dump(Z,open('/home/claude/au/eng2/zones.pkl','wb'))
