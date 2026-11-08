---
title: コンテンツの追加方法
description: ノート・過去問・解説・オリジナル問題を追加する手順
---

このサイトは [Astro](https://astro.build/) と、ドキュメント用のテーマ [Starlight](https://starlight.astro.build/) で作っています。**内容（ノートや問題）はすべてファイルで管理**していて、ファイルを追加・編集するだけでページが増えます。

## フォルダの構成

```
src/
├─ content/docs/          … 読み物のページ（Markdown）
│  ├─ index.mdx           … トップページ
│  ├─ exam.md             … 試験の概要
│  └─ notes/              … 分野別ノート（ファイルを足すとサイドバーに自動で並ぶ）
├─ data/
│  ├─ kakomon/r07.json    … 過去問（年度ごとに1ファイル）
│  ├─ drills/*.json       … オリジナル問題（一問一答など）
│  └─ categories.ts       … 分野の一覧
├─ pages/                 … 問題演習の画面（kakomon, practice, drills, record）
└─ lib/quiz.ts            … 問題演習の動き
public/kakomon/           … 図表のある過去問の画像
scripts/import_kakomon.py … 過去問 PDF → JSON の変換
```

## ノートを書く

`src/content/docs/notes/` に `.md` または `.mdx` ファイルを置きます。先頭に次のような設定を書きます。

```md
---
title: 管理組合の会計（仕訳）
description: 発生主義の仕訳のまとめ
sidebar:
  order: 3
---

## 前受金と未収入金

本文は普通の Markdown で書けます。
```

注意書きのボックスは次のように書けます。

```md
:::caution[法改正に注意]
ここに注意書き
:::
```

## 過去問に解説を付ける

`src/data/kakomon/r07.json` などの該当する問題に `explanation` を追加します。

```json
{
  "no": 1,
  "category": "minpo",
  "stem": "……",
  "choices": ["……", "……", "……", "……"],
  "answer": [4],
  "explanation": "1 は誤り。……\n2 は誤り。……\n**正解は4**。民法○条により……",
  "source": "出典：令和7年度 管理業務主任者試験問題 問1"
}
```

- `\n` で改行、`**太字**` で太字になります。
- 分野の振り分けを直したいときは `category` を書き換え、`"categoryLocked": true` を付けます（変換スクリプトを再実行しても戻りません）。
- 問題文そのものを手で直したときは `"manual": true` を付けると、変換スクリプトで上書きされません。

## オリジナル問題（一問一答）を追加する

`src/data/drills/` に JSON ファイルを追加します。形式は過去問と同じで、○×問題は選択肢を `["正しい", "誤り"]` にします。

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

既存の JSON に書いた `explanation` は、スクリプトを再実行しても引き継がれます。

## 手元で動かす・公開する

```bash
npm install
npm run dev      # http://localhost:4321/AdministrativeOperationsChiefExam/ で確認
npm run build    # dist/ に静的サイトを出力
```

GitHub に push すると、`.github/workflows/deploy.yml` によって GitHub Pages に自動で公開されます（リポジトリの Settings → Pages で Source を「GitHub Actions」にしておく）。
