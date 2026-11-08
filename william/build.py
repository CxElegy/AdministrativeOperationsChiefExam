#!/usr/bin/env python3
"""William の部屋（サイト本体）を作る：william/tpl.html ＋ 問題データ ＋ 絵 → public/index.html

  python3 william/build.py

- 問題は src/data（過去問 kakomon/*.json とオリジナル問題 drills/*.json）から読む
- 階＝出題分野（1F 適正化法 … 8F その他）、窓（部屋）＝1問ずつ（オリジナル問題→新しい年度の順）
- 絵（部屋・キャットタワー・カットイン）は william/assets から埋め込む
- William の Live2D モデルは public/w/（テクスチャだけ William の柄に塗り替えた公式サンプル Tororo）
"""
import base64, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'william')
DATA = os.path.join(ROOT, 'src', 'data')

def categories():
    src = open(os.path.join(DATA, 'categories.ts'), encoding='utf-8').read()
    return [dict(id=m[0], label=m[1], short=m[2]) for m in re.findall(r"\{ id: '([^']+)', label: '([^']+)', short: '([^']+)' \}", src)]

def item(qid, set_label, q):
    keep = ['no', 'stem', 'statements', 'choices', 'answer', 'explanation', 'choiceNotes', 'statementNotes', 'law', 'amendment', 'needsCheck', 'source', 'images']
    d = {k: q[k] for k in keep if q.get(k) not in (None, '', [])}
    d['id'] = qid; d['set'] = set_label; d['cat'] = q['category']
    d['answer'] = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
    return d

def build_data():
    cats = categories(); by = {c['id']: [] for c in cats}; qs = {}
    drills = sorted((json.load(open(f, encoding='utf-8')) | {'id': os.path.basename(f)[:-5]} for f in glob.glob(os.path.join(DATA, 'drills', '*.json'))), key=lambda d: d.get('order', 0))
    for d in drills:
        for q in d['questions']:
            qid = f"drill-{d['id']}-{q['no']}"; qs[qid] = item(qid, d['title'], q); by[q['category']].append(qid)
    exams = sorted((json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(DATA, 'kakomon', '*.json'))), key=lambda e: -e['year'])
    for e in exams:
        for q in e['questions']:
            qid = f"{e['id']}-{q['no']}"; qs[qid] = item(qid, e['label'], q); by[q['category']].append(qid)
    # 階＝分野。窓＝相談（1問 1部屋。701号室＝7階の1問目）
    floors = [{'id': c['id'], 'floor': i + 1, 'label': c['label'], 'short': c['short'], 'qids': by[c['id']]} for i, c in enumerate(cats)]
    return {'floors': floors, 'q': qs}

def data_uri(name):
    return 'data:image/webp;base64,' + base64.b64encode(open(os.path.join(W, 'assets', name), 'rb').read()).decode()

def main():
    s = open(os.path.join(W, 'tpl.html'), encoding='utf-8').read()
    data = json.dumps(build_data(), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    s = s.replace('__DATA__', data)
    s = s.replace('__ROOM__', json.dumps(data_uri('room.webp'))).replace('__TALL__', json.dumps(data_uri('tall.webp')))
    s = s.replace('__CUTIN__', json.dumps(data_uri('cutin.webp'))).replace('__POSES__', '{}')
    i = s.index('</style>') + len('</style>')
    head = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
    out = head + s[:i] + '\n</head>\n<body>\n' + s[i:] + '\n</body>\n</html>\n'
    open(os.path.join(ROOT, 'public', 'index.html'), 'w', encoding='utf-8').write(out)
    print('public/index.html', len(out) // 1024, 'KB')

if __name__ == '__main__':
    main()
