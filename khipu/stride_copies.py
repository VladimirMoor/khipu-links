"""Инкавази: каждая p-я запись (группа) кипу X против подряд идущих записей Y (шаг 2–8, все фазы и сдвиги); лучшее число общих некруглых значений ≥ 100 по паре."""
import csv, json, random
from collections import defaultdict
D=json.load(open('site/data.json'))
ink=sorted(k['id'] for k in D['khipus'] if k['site']=='inkawasi')
G=defaultdict(lambda: defaultdict(list))
for r in csv.DictReader(open('extracted/plus_cords.csv')):
    if r['inv_num'] in ink and r['parent_id']=='':
        G[r['inv_num']][r['group']].append((int(r['order']),int(r['value'])))
gr={k:[[v for _,v in sorted(x)] for _,x in sorted(d.items(),key=lambda kv:min(o for o,_ in kv[1]))] for k,d in G.items()}
nr=lambda v: v>=100 and v%100!=0
S={k:[frozenset(v for v in g if nr(v)) for g in gr[k]] for k in gr}
def best(X,Y,pmax=8):
    out=(0,None)
    for p in range(2,pmax+1):
        for s in range(p):
            sub=X[s::p]
            if len(sub)<4: continue
            for c in range(-len(sub)+2,len(Y)-1):
                h=sum(1 for b,x in enumerate(sub) if x and 0<=b+c<len(Y) and x&Y[b+c])
                if h>out[0]: out=(h,(p,s,c))
    return out
res=[]
for a in ink:
    for b in ink:
        if a==b or len(S[a])<12: continue
        h,arg=best(S[a],S[b])
        if h>=3: res.append((h,a,b,arg))
res.sort(reverse=True)
for r in res[:15]: print(r)
json.dump(res,open('extracted/stride_copies.json','w'))
