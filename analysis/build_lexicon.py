"""Word statistics for the lexicon page.
Writes lexicon/corpus.json (form text, loaded by the page) and data/lexicon.json (per-word counts by grade, embedded in the page).
Usage: HOLC_AD=path/to/ad_data.json python analysis/build_lexicon.py
"""
import json, os, re, collections
SRC = os.environ.get('HOLC_AD', 'HOLC_Area_Description_Data/ad_data.json')
HERE = os.path.dirname(__file__)
F = {'T': 'description_of_terrain', 'F': 'favorable_influences', 'X': 'detrimental_influences', 'O': 'occupation_or_type',
     'N': 'foreign_born_nationality', 'R': 'negro_yes_or_no', 'I': 'infiltration_of', 'C': 'clarifying_remarks', 'D': 'trend_of_desirability'}
STOP = set('''a about above after again against all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its itself just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up very was we were what when where which while who whom why will with would you your yes per etc approximately approx ave st av blvd street streets avenue rd road area areas section sections portion part located also within near along around across beyond toward towards one two three four five six seven eight nine ten first second third north south east west northern southern eastern western mr'''.split())
docs = []
for x in json.load(open(SRC)):
    g = (x.get('grade') or '').strip().upper()
    if g not in ('A', 'B', 'C', 'D'): continue
    t = {k: ' '.join(str(x.get(v, '')).split()) for k, v in F.items()}
    docs.append([x['city'], x['state'], ' '.join(str(x.get('label', '')).split()), g, {k: v for k, v in t.items() if v}])
json.dump(docs, open(os.path.join(HERE, '..', 'lexicon', 'corpus.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
tok = re.compile(r"[a-z]+(?:'[a-z]+)?"); gi = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
N = [0, 0, 0, 0]; df = collections.defaultdict(lambda: [0, 0, 0, 0])
for c, s, l, g, t in docs:
    N[gi[g]] += 1
    for w in {w for v in t.values() for w in tok.findall(v.lower()) if len(w) > 2 and w not in STOP}:
        df[w][gi[g]] += 1
lex = []
for w, c in df.items():
    tot = sum(c)
    if tot < 15: continue
    r = [(c[i] + 0.5) / (N[i] + 1) for i in range(4)]            # rate per grade, lightly smoothed
    mean = sum((i + 1) * r[i] for i in range(4)) / sum(r)          # 1 = A ... 4 = D, adjusted for grade sizes
    exp = [tot * N[i] / sum(N) for i in range(4)]
    chi = sum((c[i] - exp[i]) ** 2 / exp[i] for i in range(4))     # how far from chance the spread is
    lex.append([w, c, round(mean, 3), round(chi, 1)])
lex.sort(key=lambda x: (-sum(x[1]), x[0]))
json.dump({'N': N, 'lex': lex}, open(os.path.join(HERE, '..', 'data', 'lexicon.json'), 'w'), separators=(',', ':'))
print(N, len(lex))
