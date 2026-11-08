# 管業スタディ

管理業務主任者試験の勉強用サイトです。過去問を年度別・分野別に解き、間違えた問題を繰り返せます。

- **過去問**：令和元年度〜令和7年度（令和2年度を除く）の300問。正解・合格基準点・図表の画像つき
- **練習モード**（1問ごとに正誤表示）と **本番モード**（2時間・最後に採点・合格基準点で判定、5問免除にも対応）
- **分野別・ランダム演習**、前回間違えた問題・まだ解いていない問題だけの出題
- **一問一答ドリル**（オリジナルの○×問題）
- **学習記録**（ブラウザに保存。書き出し・読み込み可）
- **分野別ノート**（Markdown で書き足していく）
- 試験の概要、合格基準点・合格率の推移

## 使っている技術

- [Astro](https://astro.build/) 7 + [Starlight](https://starlight.astro.build/)（ドキュメントサイト用のテーマ。サイドバー・検索・ダークモードつき）
- 過去問・ドリルは JSON、ノートは Markdown。Astro のコンテンツコレクションで形式をチェックする
- 問題演習の画面は TypeScript（フレームワークなし）
- GitHub Pages に静的サイトとして公開

## 手元で動かす

```bash
npm install
npm run dev
```

http://localhost:4321/AdministrativeOperationsChiefExam/ を開きます。

## 内容を追加する

ノート、解説、オリジナル問題、新しい年度の過去問の追加方法は [`src/content/docs/contributing.md`](src/content/docs/contributing.md)（サイト上の「コンテンツの追加方法」）を参照してください。

## 公開

`main` ブランチに push すると `.github/workflows/deploy.yml` が GitHub Pages にデプロイします。初回はリポジトリの **Settings → Pages → Source** を **GitHub Actions** にしてください。

## 過去問の出典

一般社団法人マンション管理業協会「管理業務主任者試験問題」各年度（https://www.kanrikyo.or.jp/kanri/siken.html）。協会の「[過去問の使用について](https://www.kanrikyo.or.jp/kanri/pdf/kakomonshiyou.pdf)」により、教育目的での使用は無償・許諾不要で、出典の明記が必要です。各問題に出典を表示しています。

令和8年度試験は、2026年4月1日に施行された改正区分所有法などに基づいて出題されます。過去問は出題当時の法令に基づくため、改正点に関わる問題は現行法では正解が異なる場合があります。
