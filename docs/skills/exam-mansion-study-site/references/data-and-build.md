# データ形式とビルド

## 問題（src/data/kakomon/r07.json）
```json
{ "id": "r07", "year": 2025, "label": "令和7年度", "examDate": "2025-12-07", "passMark": 36,
  "questions": [ { "no": 1, "category": "minpo", "stem": "…", "choices": ["…","…","…","…"], "answer": [4],
    "statements": [{"label":"ア","text":"…"}], "statementNotes": [{"label":"ア","correct":true,"note":"…"}],
    "explanation": "…", "choiceNotes": ["…","…","…","…"], "law": "民法940条1項 …",
    "amendment": "法改正の注意（あれば）", "needsCheck": "要確認（あれば）", "source": "出典：…" } ] }
```
問題 ID は `<年度id>-<no>`、オリジナル問題は `drill-<ファイル名>-<no>`。

## 分野＝階（src/data/categories.ts）
並び順が 1F→8F。過去問の `category` はこの id。

## 部屋割り（src/data/rooms.json）
`{ "<分野id>": [ { "title": "用語・基本方針", "qids": ["r07-46", …] } ] }`。部屋番号＝階×100＋位置。rooms.json に無い新しい問題は「新着の相談」部屋へ。同じ問題を 2 部屋に入れたらビルドを止める。

## ヒント（src/data/hints/<年度>.json）
`{ "r07-1": ["30秒の一言", "1分の一言", "2分の一言"] }`。答えは言わない。猫語。

## 知識のポイント（src/data/points/<年度>.json）
`{ "r07-1": ["要点1", "要点2", …] }` 2〜4 行、各 80 字以内、`**最重要**` は 1 か所まで。問題文・選択肢番号を書かない。解説にある事実だけ。法改正は現行ルールで。要確認は断定しない。

## 章立て（src/data/syllabus/ch<N>-<id>.json）
```json
{ "order": 1, "id": "minpo", "title": "民法・その他の法令",
  "sections": [ { "title": "代理", "items": [ { "t": "要点", "q": ["r07-4", "drill-…-6"] } ] } ] }
```
全章がそろうまでは使わない（ビルドで判定）。全問題が どこかの `q` に入っていることを検証。

## ビルド（william/build.py）
- `tpl.html` の `__DATA__`（floors・q・syl）、画像 `__BLDG__` `__ROOM__` `__MAJI__` `__PHOTOS__` などを置換して `public/index.html`。
- 実写真は 4:3（560×420、webp q76、1 枚 15〜30KB）に切り抜き、猫が枠に入る位置を 1 枚ずつ指定。
- `public/` は生成物なのでコミットしない。デプロイは GitHub Actions。

## 確認
- Playwright：`python3 -m http.server` で `public/` を出し、PC 1440×900 とスマホ（Pixel 7）で通しテスト。
- 回帰：答える → 窓の明かり → 点灯パネル → 再読み込みで記録が残る、まで。
