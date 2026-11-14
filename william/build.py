#!/usr/bin/env python3
"""William の部屋（サイト本体）を作る：william/tpl.html ＋ 問題データ ＋ 絵 → public/index.html

  python3 william/build.py

- 問題は src/data（過去問 kakomon/*.json とオリジナル問題 drills/*.json）から読む
- 階＝出題分野（1F 適正化法 … 8F その他）、部屋（窓）＝同じテーマの相談のまとまり（src/data/rooms.json）
- 絵（マンション・部屋・キャットタワー・カットイン）は william/assets から埋め込む
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
    if qid in HINTS: d['hints'] = HINTS[qid]
    return d

# 考える時間が長いときにウィリアムが言うヒント（src/data/hints/*.json：問題ID → [30秒, 1分, 2分]）
HINTS = {}
for _f in sorted(glob.glob(os.path.join(DATA, 'hints', '*.json'))): HINTS.update(json.load(open(_f, encoding='utf-8')))

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
    # 階＝分野。部屋（窓）＝同じテーマの相談のまとまり（src/data/rooms.json）。701-1, 701-2 … と番号をつける
    plan = json.load(open(os.path.join(DATA, 'rooms.json'), encoding='utf-8')) if os.path.exists(os.path.join(DATA, 'rooms.json')) else {}
    floors = []
    for i, c in enumerate(cats):
        ids = by[c['id']]
        rooms = [{'title': r['title'], 'qids': [q for q in r['qids'] if q in qs]} for r in plan.get(c['id'], [])]
        placed = [q for r in rooms for q in r['qids']]
        dup = {q for q in placed if placed.count(q) > 1}
        if dup: raise SystemExit(f"rooms.json: {c['id']} で2回出てくる問題 {sorted(dup)}")
        rest = [q for q in ids if q not in placed]
        if rest:  # rooms.json に無い問題（新しい年度など）は「新着」の部屋へ
            print(f"注意: {c['id']} の {len(rest)} 問は rooms.json に無いので「新着の相談」の部屋に入れました")
            rooms.append({'title': '新着の相談', 'qids': rest})
        rooms = [r for r in rooms if r['qids']]
        floors.append({'id': c['id'], 'floor': i + 1, 'label': c['label'], 'short': c['short'], 'rooms': rooms})
    return {'floors': floors, 'q': qs}

def data_uri(name):
    return 'data:image/webp;base64,' + base64.b64encode(open(os.path.join(W, 'assets', name), 'rb').read()).decode()

def main():
    s = open(os.path.join(W, 'tpl.html'), encoding='utf-8').read()
    data = json.dumps(build_data(), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    import hashlib, time
    build_id = time.strftime('%Y%m%d%H%M%S')  # 版の番号（新しい版が出たら、開いているページが自動で読み込み直すのに使う）
    s = s.replace('__BUILD__', build_id)
    s = s.replace('__DATA__', data)
    s = s.replace('__ROOM__', json.dumps(data_uri('room.webp'))).replace('__TALL__', json.dumps(data_uri('tall.webp')))
    maji = sorted(os.path.basename(f) for f in glob.glob(os.path.join(W, 'assets', 'maji*.webp'))) or ['cutin.webp']  # 全問正解のアイコン（ランダムで1枚。無ければカットインの絵）
    s = s.replace('__MAJI__', json.dumps([data_uri(m) for m in maji]))
    s = s.replace('__BLDG__', data_uri('bldg.webp')).replace('__CUTIN__', json.dumps(data_uri('cutin.webp'))).replace('__POSES__', '{}')
    i = s.index('</style>') + len('</style>')
    head = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
    out = head + s[:i] + '\n</head>\n<body>\n' + s[i:] + '\n</body>\n</html>\n'
    # playground.html：試し中の機能（アナちゃん）を入れたページ。本番（index.html）には出さない
    open(os.path.join(ROOT, 'public', 'playground.html'), 'w', encoding='utf-8').write(out.replace('__PLAY__', 'true').replace('__ANA__', json.dumps({k: data_uri('ana_' + k + '.webp') for k in ('back', 'mane', 'tail')})).replace('<title>', '<title>[playground] ', 1))
    out = out.replace('__PLAY__', 'false').replace('__ANA__', '{}')
    open(os.path.join(ROOT, 'public', 'index.html'), 'w', encoding='utf-8').write(out)
    print('public/index.html', len(out) // 1024, 'KB')
    # 進度ダッシュボード（dashboard.html?u=<ID>）：部屋の並びと、問題の年度・番号だけ入れる
    full = build_data()
    dash = {'floors': [{'floor': f['floor'], 'label': f['label'], 'short': f['short'], 'rooms': [{'title': r['title'], 'qids': r['qids']} for r in f['rooms']]} for f in full['floors']],
            'q': {k: [v['set'], v['no']] for k, v in full['q'].items()}}
    d = open(os.path.join(W, 'dashboard.html'), encoding='utf-8').read().replace('__DASH__', json.dumps(dash, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    open(os.path.join(ROOT, 'public', 'dashboard.html'), 'w', encoding='utf-8').write(d)
    print('public/dashboard.html', len(d) // 1024, 'KB')

if __name__ == '__main__':
    main()
