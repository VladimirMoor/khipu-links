"""Частичные совпадения групп по всему корпусу 2026: ≥ 4 позиции с одинаковым некруглым значением ≥ 50 в группах (≥ 8 шнуров) разных кипу с разными музейными номерами; фон — значения, сдвинутые на ±1…±3."""
import csv,json,re
from collections import defaultdict, Counter
G=defaultdict(lambda: defaultdict(list))
for r in csv.DictReader(open('extracted/plus2026_cords.csv')):
    if r['parent_id']=='': G[r['inv_num']][r['group']].append((int(r['order']),int(r['value'])))
gr={k:[[v for _,v in sorted(x)] for _,x in sorted(d.items(),key=lambda kv:min(o for o,_ in kv[1]))] for k,d in G.items()}
norm=lambda s: re.sub(r'[^0-9A-Z]','',str(s or '').upper())
mus={}
for k in json.load(open('site/data.json'))['khipus']: mus[k['id']]=norm(k['num'])
for k,v in json.load(open('extracted/kfg2026_meta.json')).items(): mus.setdefault(k,norm(v.get('museum_num')))
idx=defaultdict(list)
for k,gs in gr.items():
    for gi,g in enumerate(gs):
        if len(g)>=8:
            for p,v in enumerate(g):
                if v>=50 and v%10: idx[(p,v)].append((k,gi))   # non-round >= 50
def scan(d):
    out=[]
    for k,gs in gr.items():
        for gi,g in enumerate(gs):
            if len(g)<8: continue
            c=Counter()
            for p,v in enumerate(g):
                if v>=50 and v%10:
                    for (k2,g2) in idx.get((p,v+d),[]):
                        if k2!=k: c[(k2,g2)]+=1
            for (k2,g2),n in c.items():
                if n>=4 and (d!=0 or k<k2) and not (mus.get(k) and mus.get(k)==mus.get(k2)): out.append((n,k,gi+1,k2,g2+1))
    return out
real=scan(0); null=[len(scan(d)) for d in (-3,-2,-1,1,2,3)]
print('real',len(real),'null',null)
for x in sorted(real,reverse=True)[:25]: print(x)
