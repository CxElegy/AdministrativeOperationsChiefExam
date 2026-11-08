# 問題・解説の追加方法

問題はすべて JSON ファイルで管理しています。ファイルを追加・編集して `npm run build` すると、マンションの部屋に相談が増えます。新しい問題は `src/data/rooms.json` のどの部屋に入れるかも書いてください（書かないと、その階の「新着の相談」の部屋に入ります）。

```
src/data/
├─ kakomon/r07.json    … 過去問（年度ごとに1ファイル。解説もここ）
├─ drills/*.json       … オリジナル問題（各階の最初の窓に入る）
├─ categories.ts       … 階（分野）の順番
└─ rooms.json          … 部屋（同じテーマの相談のまとまり）。階ごとに 4〜8 室
public/kakomon/        … 図表のある過去問の画像
scripts/import_kakomon.py … 過去問 PDF → JSON の変換
william/               … ページ本体（tpl.html）と、データを埋め込む build.py
```

## 過去問に解説を付ける

`src/data/kakomon/r07.json` などの該当する問題に、次の項目を追加します。答えたあと、相談票に出る内容です。

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
  "needsCheck": "まだ確認が必要な点（「要確認」として出る）"
}
```

- `choiceNotes` は選択肢と同じ順番・同じ数で書きます。答えたあと、全部の選択肢の下に「管理人さん」の解説として出ます。
- `statementNotes` はア〜エの記述がある問題（個数問題・組合せ問題）だけ書きます。
- 文中の `**太字**` は太字、`\n` は改行になります。
- 分野の振り分けを直したいときは `category` を書き換え、`"categoryLocked": true` を付けます。
- 問題文そのものを手で直したときは `"manual": true` を付けると、変換スクリプトで上書きされません。

## オリジナル問題（一問一答）を追加する

`src/data/drills/` に JSON ファイルを追加します。形式は過去問と同じで、○×問題は選択肢を `["正しい", "誤り"]` にします。オリジナル問題は、その分野の階の最初の窓（x01号室〜）に入ります。

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

`category` に使える値は `minpo` `itaku` `kaikei` `kenchiku` `kubun` `kiyaku` `tekiseika` `sonota` です（`src/data/categories.ts`）。

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
npm run build            # william/build.py で public/index.html を作り、dist/ にコピー
npm run progress-server  # http://localhost:8787/AdministrativeOperationsChiefExam/ で確認
```

GitHub に push すると、`.github/workflows/deploy.yml` によって GitHub Pages に自動で公開されます（リポジトリの Settings → Pages で Source を「GitHub Actions」にしておく）。
