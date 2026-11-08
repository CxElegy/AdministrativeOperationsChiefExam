---
title: コンテンツの追加方法
description: ノート・過去問・解説・オリジナル問題を追加する手順
order: 9
---

このサイトは [Astro](https://astro.build/) で作った静的サイトです。**内容（ノートや問題）はすべてファイルで管理**していて、ファイルを追加・編集するだけでページが増えます。

## フォルダの構成

```
src/
├─ content/guide/         … 読み物（Markdown）
│  ├─ exam.md             … 試験の概要
│  ├─ scope.md            … 出題分野と遊び方
│  └─ notes/              … 各階（分野）のノート
├─ data/
│  ├─ kakomon/r07.json    … 過去問（年度ごとに1ファイル。解説もここ）
│  ├─ drills/*.json       … オリジナル問題（各階の最初の部屋に入る）
│  └─ categories.ts       … 階（分野）の順番と、1部屋あたりの問題数
├─ lib/
│  ├─ build-data.ts       … 問題を「階・部屋」にまとめる
│  ├─ app.ts              … 攻略マップ・レッスン・メモ帳・総会・記録の画面
│  └─ store.ts            … 学習記録（ブラウザに保存）
├─ pages/                 … index（アプリ本体）と guide（読み物）
└─ styles/global.css      … 見た目
public/kakomon/           … 図表のある過去問の画像
scripts/import_kakomon.py … 過去問 PDF → JSON の変換
```

## ノートを書く

`src/content/guide/notes/` に `.md` ファイルを置きます。先頭に次のような設定を書きます。

```md
---
title: 管理組合の会計（仕訳）
description: 発生主義の仕訳のまとめ
order: 3
category: kaikei   # 階（分野）の id。書くと、その階の部屋の一覧がページの下に出る
---

## 前受金と未収入金

本文は普通の Markdown で書けます。
```

注意書きのボックスは次のように書けます。

```md
<div class="callout callout-caution">
<p class="callout-title">法改正に注意</p>

ここに注意書き

</div>
```

## 過去問に解説を付ける

`src/data/kakomon/r07.json` などの該当する問題に、次の項目を追加します。間違えたときに管理人さんが表示する内容です。

```json
{
  "no": 46,
  "category": "tekiseika",
  "stem": "……最も不適切なものはどれか。",
  "choices": ["……", "……", "……", "……"],
  "answer": [3],
  "explanation": "この問題のポイント（2〜3文）",
  "choiceNotes": ["選択肢1の正誤と理由", "選択肢2…", "選択肢3…", "選択肢4…"],
  "statementNotes": [{ "label": "ア", "correct": true, "note": "記述アの正誤と理由" }],
  "law": "根拠条文（例：マンション管理適正化法 3条の2第2項）",
  "amendment": "令和8年4月施行の法改正で結論が変わりうるときの注意（なければ書かない）",
  "needsCheck": "まだ確認が必要な点（サイトには「確認中の点があります」とだけ出る）"
}
```

- `choiceNotes` は選択肢と同じ順番・同じ数で書きます。選んだ選択肢の解説が「◯を選んだね」の下に出ます。
- `statementNotes` はア〜エの記述がある問題（個数問題・組合せ問題）だけ書きます。
- 文中の `**太字**` は太字、`\n` は改行になります。
- 分野の振り分けを直したいときは `category` を書き換え、`"categoryLocked": true` を付けます。
- 問題文そのものを手で直したときは `"manual": true` を付けると、変換スクリプトで上書きされません。

## オリジナル問題（一問一答）を追加する

`src/data/drills/` に JSON ファイルを追加します。形式は過去問と同じで、○×問題は選択肢を `["正しい", "誤り"]` にします。オリジナル問題は、その分野の階の最初の部屋に入ります。

```json
{
  "title": "区分所有法の数字（○×）",
  "description": "集会・規約の数字を確認する",
  "order": 2,
  "questions": [
    {
      "no": 1,
      "category": "kubun",
      "stem": "……である。",
      "choices": ["正しい", "誤り"],
      "answer": [1],
      "explanation": "正しい。……"
    }
  ]
}
```

`category` に使える値は `minpo` `itaku` `kaikei` `kenchiku` `kubun` `kiyaku` `tekiseika` `sonota` です（`src/data/categories.ts`）。形式が間違っているとビルド時にエラーで教えてくれます。

## 新しい年度の過去問を取り込む

1. [協会の試験ページ](https://www.kanrikyo.or.jp/kanri/siken.html)から「試験問題・正解」の PDF（`mondai_011.pdf`）と「結果報告」の PDF（`goukakugaiyou.pdf`）をダウンロードし、`r08_mondai.pdf`、`r08_kekka.pdf` のような名前で1つのフォルダに置く。
2. 変換スクリプトを実行する。

   ```bash
   pip install pdfplumber pypdfium2
   python3 scripts/import_kakomon.py <PDFを置いたフォルダ>
   ```

3. `src/data/kakomon/r08.json` と、図表の画像（`public/kakomon/r08/`）ができる。サイトで表示を確認し、おかしい問題は JSON を直接直す。

既存の JSON に書いた解説（`explanation`・`choiceNotes` など）は、スクリプトを再実行しても引き継がれます。

## 手元で動かす・公開する

```bash
npm install
npm run dev      # http://localhost:4321/AdministrativeOperationsChiefExam/ で確認
npm run build    # dist/ に静的サイトを出力
```

GitHub に push すると、`.github/workflows/deploy.yml` によって GitHub Pages に自動で公開されます（リポジトリの Settings → Pages で Source を「GitHub Actions」にしておく）。
