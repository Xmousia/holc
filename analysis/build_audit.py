"""Economics-only model of HOLC grades, like-for-like comparison, flip test, and disagreement cases.
Writes data/audit.json, which audit/index.html embeds.
Usage: HOLC_AD=path/to/ad_data.json python analysis/build_audit.py
"""
import json, os, sys
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold
sys.path.insert(0, os.path.dirname(__file__))
from parse import load

ECON = ['rel_lp', 'rel_li', 'chg', 'age', 'repair', 'occupancy', 'owner']
G = 'ABCD'

rows = load()
raw = {r['id']: r['raw'] for r in rows}
df = pd.DataFrame([{k: v for k, v in r.items() if k != 'raw'} for r in rows])
df['lp'], df['li'], df['lp29'] = np.log(df.price), np.log(df.income), np.log(df.price29)
# prices and income relative to the median of the same city (HOLC graded within cities)
for c in ['lp', 'li']:
    med = df.groupby('city')[c].transform('median'); cnt = df.groupby('city')[c].transform('count')
    df['rel_' + c] = np.where(cnt >= 4, df[c] - med, np.nan)
df['chg'] = df.lp - df.lp29
df['n_econ'] = df[ECON].notna().sum(axis=1)
el = df[df.rel_lp.notna() & (df.n_econ >= 4)].copy()

def design(d, race=False):
    X = pd.DataFrame(index=d.index)
    for c in ECON:
        X[c] = d[c].fillna(el[c].median()); X[c + '_na'] = d[c].isna().astype(int)
    if race: X['black'] = d.black
    return X

def model():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))

# 1. economics-only, out-of-fold by city
y = el.grade.values; X = design(el); P = np.zeros((len(el), 4))
for tr, te in GroupKFold(5).split(X, y, el.city.values):
    P[te] = model().fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])
el['exp'] = P @ np.arange(1, 5); el['pred'] = P.argmax(1) + 1; el['resid'] = y - el.exp
pred = el.pred.values
conf = [[int(((y == a) & (pred == p)).sum()) for p in range(1, 5)] for a in range(1, 5)]
m = model().fit(X, y)
coef = dict(zip(X.columns, (m[-1].coef_[3] - m[-1].coef_[0]).round(2)))
feat = [{'k': c, 'w': float(coef[c])} for c in ECON]

# 2. like-for-like bins, areas where the race field is filled in
k = el[el.black.notna()].copy()
bins = [1, 1.75, 2.25, 2.6, 2.9, 3.2, 3.5, 4.01]
k['bin'] = pd.cut(k.exp, bins, right=False, labels=False)
B = []
for i in range(len(bins) - 1):
    for b in [0, 1]:
        t = k[(k.bin == i) & (k.black == b)]
        B.append({'bin': i, 'lo': bins[i], 'hi': min(bins[i + 1], 4), 'black': b, 'n': int(len(t)),
                  'D': int((t.grade == 4).sum()), 'CD': int((t.grade >= 3).sum())})

# 3. flip test: economics + race model, score each area with race field set to 1 and to 0
Xk = design(k, race=True); yk = k.grade.values
d1 = np.zeros(len(k)); d0 = np.zeros(len(k))
for tr, te in GroupKFold(5).split(Xk, yk, k.city.values):
    mm = model().fit(Xk.iloc[tr], yk[tr])
    a = Xk.iloc[te].copy(); a['black'] = 1; b = Xk.iloc[te].copy(); b['black'] = 0
    d1[te] = mm.predict_proba(a)[:, 3]; d0[te] = mm.predict_proba(b)[:, 3]
bands = []
for lo, hi, name in [(1, 2.5, 'Numbers look like A or B'), (2.5, 3.2, 'Numbers look like C'), (3.2, 4.1, 'Numbers look like D')]:
    msk = ((k.exp >= lo) & (k.exp < hi)).values
    bands.append({'name': name, 'n': int(msk.sum()), 'p0': round(float(d0[msk].mean()), 3), 'p1': round(float(d1[msk].mean()), 3)})
flip = {'p0': round(float(d0.mean()), 3), 'p1': round(float(d1.mean()), 3), 'bands': bands}

# 4. disagreement cases (|actual - expected| >= 0.75)
def case(r):
    rw = raw[r.id]
    return {'id': int(r.id), 'city': r.city, 'st': r.state, 'label': r.label, 'g': G[int(r.grade) - 1], 'exp': round(float(r.exp), 2),
            'p': [round(float(v), 3) for v in P[el.index.get_loc(r.Index)]],
            'black': None if pd.isna(r.black) else int(r.black),
            'f': {kk: v for kk, v in rw.items() if v and v not in ('-', '--')},
            'rel_price': None if pd.isna(r.rel_lp) else round(float(np.exp(r.rel_lp)), 2),
            'repair': None if pd.isna(r.repair) else float(r.repair)}
cases = {'down': [case(r) for r in el[el.resid >= 0.75].sort_values('resid', ascending=False).itertuples()],
         'up': [case(r) for r in el[el.resid <= -0.75].sort_values('resid').itertuples()]}

summ = {'n_forms': len(rows), 'n_used': int(len(el)), 'n_cities': int(el.city.nunique()), 'n_black_known': int(len(k)),
        'acc': round(float((pred == y).mean()), 3), 'within1': round(float((abs(pred - y) <= 1).mean()), 3), 'baseline': round(float((y == 3).mean()), 3),
        'share_black_by_grade': [round(float(k[k.grade == i].black.mean()), 3) for i in range(1, 5)],
        'n_black_by_grade': [int(k[k.grade == i].black.sum()) for i in range(1, 5)], 'n_by_grade': [int((k.grade == i).sum()) for i in range(1, 5)],
        'resid_black': round(float(k[k.black == 1].resid.mean()), 3), 'resid_noblack': round(float(k[k.black == 0].resid.mean()), 3)}
out = os.path.join(os.path.dirname(__file__), '..', 'data', 'audit.json')
json.dump({'summ': summ, 'conf': conf, 'bins': B, 'flip': flip, 'feat': feat, 'cases': cases}, open(out, 'w'), separators=(',', ':'), ensure_ascii=False)
print(summ)
