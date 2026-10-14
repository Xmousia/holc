"""Parse the free-text economic and race fields of HOLC area description forms into numbers."""
import json,re,math,statistics,collections
import os
# Path to ad_data.json from https://github.com/americanpanorama/HOLC_Area_Description_Data
SRC=os.environ.get('HOLC_AD','HOLC_Area_Description_Data/ad_data.json')
MONTHS=r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?'
def clean(s):
    s=str(s or '').lower()
    s=re.sub(r'\([^)]*\)','',s)
    s=re.sub(r'\b\w+ \d{1,2}, ?18\d\d','',s)    # spreadsheet zero-dates
    s=re.sub(MONTHS+r'[ ,./-]*\d{0,4}','',s)
    return s
def nums(s):
    out=[]
    for m in re.finditer(r'\$?\s*(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(m\b|m(?=[-\s,$]|$)|k\b)?',s):
        v=float(m.group(1).replace(',',''))
        if m.group(2): v*=1000
        out.append(v)
    return out
def money(s, kind):
    s=clean(s)
    if not s.strip() or re.search(r'n/?a|none|no sales|nothing|owner',s) and not re.search(r'\d',s): return None
    thousand = bool(re.search(r'\d\s*m\b|\d\s*m[-\s]|\d\s*m$',s))
    v=nums(s)
    if len(v)>=2 and v[0]<100 and v[1]>=1000: v[0]*=1000
    v=[x*1000 if (x<100 and (thousand or kind=='price')) else x for x in v]
    v=[x for x in v if not (1925<=x<=1941 and float(x).is_integer() and kind=='price' and len(v)>1)]
    lo,hi=(200,100000) if kind=='income' else (300,200000)
    v=[x for x in v if lo<=x<=hi]
    if not v: return None
    v=v[:2]
    return math.exp(sum(math.log(x) for x in v)/len(v))   # geometric midpoint of range
def pct(s):
    s=clean(s)
    if '18' in s and re.search(r'18\d\d',s): return None
    v=[x for x in nums(s) if 0<=x<=100]
    if not v: return None
    return sum(v[:2])/len(v[:2])
def age(s):
    s=clean(s)
    if re.search(r'18\d\d|19[0-4]\d',s): return None
    v=[x for x in nums(s) if 0<=x<=120]
    if not v: return None
    return sum(v[:2])/len(v[:2])
REP=[('excellent',5),('very good',4.5),('fairly good',3.5),('good',4),('fair',3),('very poor',1.5),('dilapidated',1),('bad',1.2),('poor',2)]
def repair(s):
    s=clean(s); found=[]
    for k,v in REP:
        if k in s: found.append(v); s=s.replace(k,' ')
    return sum(found)/len(found) if found else None
NONE=re.compile(r'^\s*(no|none|none known|0|0%|-+|n/?a|nil|no negroes|not any)\s*\.?\s*$')
def black(yes, p):
    y=str(yes or '').strip().lower(); pp=pct(p) if p else None
    if pp and pp>0: return 1, pp
    if not y: return (None, None) if pp is None else (0 if pp==0 else 1, pp)
    if NONE.match(y) or y.startswith('no ') or y.startswith('none'): return 0, 0.0
    if re.search(r'yes|few|scattered|nominal|many|negro|famil|some|\d',y): return 1, pp
    return None, pp
def load():
    d=json.load(open(SRC)); rows=[]
    for x in d:
        g=(x.get('grade') or '').strip().upper()
        if g not in ('A','B','C','D'): continue
        r={'id':x['area_id'],'city':x['city'],'state':x['state'],'label':' '.join(str(x.get('label','')).split()),'grade':'ABCD'.index(g)+1,'form':x.get('form_id')}
        r['income']=money(x.get('estimated_annual_family_income'),'income')
        p_last=money(x.get('price_predominating_dollars_last_year'),'price') or money(x.get('price_range_dollars_last_year'),'price')
        p29=money(x.get('price_predominating_1929'),'price') or money(x.get('price_range_dollars_1929'),'price')
        r['price']=p_last; r['price29']=p29
        r['age']=age(x.get('average_age')); r['repair']=repair(x.get('repair'))
        r['occupancy']=pct(x.get('occupancy')); r['owner']=pct(x.get('home_ownership'))
        r['black'],r['black_pct']=black(x.get('negro_yes_or_no'),x.get('negro_percent'))
        r['foreign_pct']=pct(x.get('foreign_born_percent'))
        r['raw']={k:' '.join(str(x.get(k,'')).split()) for k in ['estimated_annual_family_income','price_range_dollars_last_year','price_predominating_dollars_last_year','price_range_dollars_1929','average_age','repair','occupancy','home_ownership','negro_yes_or_no','negro_percent','infiltration_of','foreign_born_nationality','foreign_born_percent','occupation_or_type','favorable_influences','detrimental_influences','clarifying_remarks','trend_of_desirability','relief_families']}
        rows.append(r)
    return rows
if __name__=='__main__':
    rows=load(); n=len(rows)
    for k in ['income','price','price29','age','repair','occupancy','owner','black','foreign_pct']:
        v=[r[k] for r in rows if r[k] is not None]
        print(k, len(v), f'{100*len(v)/n:.0f}%', 'median', round(statistics.median(v),1) if v else None)
    import random; random.seed(5)
    for r in random.sample(rows,12):
        print(r['raw']['estimated_annual_family_income'],'->',r['income'],'|',r['raw']['price_range_dollars_last_year'],r['raw']['price_predominating_dollars_last_year'],'->',r['price'],'|',r['raw']['repair'],'->',r['repair'],'|',r['raw']['negro_yes_or_no'],r['raw']['negro_percent'],'->',r['black'])
