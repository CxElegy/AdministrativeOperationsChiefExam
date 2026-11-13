# アナちゃん（playground）：一枚絵から Live2D を作り直す

Tororo のテクスチャを塗り替える方法は やめた（毛の質感も体型もちがう猫なので、似ない）。
Live2D の作り方どおり、**一枚絵 → 部品分け → PSD → メッシュ・デフォーマ・パラメータ → 書き出し** の順で 0 から作る。
Tororo は「猫のモデルは どんな部品と動きで できているか」の参考にだけ使い、モデル自体は使わない。

## 参考にした作り方

- GMO「See-Through × Kaggle × Claude Code で1枚絵からLive2Dモデルを（ほぼ）自動生成する」
  https://recruit.group.gmo/engineer/jisedai/blog/see-through-x-kaggle-x-claude-code/
- See-through（一枚絵を 重なり順つきの部品に分けて PSD にする。SIGGRAPH 2026、Apache-2.0）
  https://github.com/shitagaki-lab/see-through ／ ComfyUI 版 https://github.com/jtydhr88/ComfyUI-See-through

## 工程

| # | 工程 | 道具 | どこで動かすか |
|---|---|---|---|
| 1 | 一枚絵（正面で座っているアナちゃんのイラスト） | 画像生成 AI か 手描き | ― |
| 2 | 部品分け（かくれた所も描き足す） | See-through（GPU が要る。T4×2 で 1 回 25〜30 分、seed を 3 つほど試す） | Kaggle |
| 3 | PSD を作る（部品をグループにまとめる。グループが Cubism のパーツになる） | GIMP + スクリプト | PC か この環境 |
| 4 | メッシュ・顔のデフォーマ・顔の動きの自動生成、目と口の開閉、しっぽ・耳・呼吸 | Live2D Cubism Editor 5 | PC（Windows / Mac の画面つきソフト） |
| 5 | moc3 を書き出して、ページに組み込む | pixi-live2d-display（今の William と同じ） | この環境 |

## Tororo から参考にすること（猫のモデルの部品と動き）

- 部品：しっぽ／せなか・おしり／前足・うしろ足（上・下・足先）／胸／顔の土台／口（上あご・下あご・舌・歯）／耳（外・内・耳の毛）／目（白目・まぶた・ひとみ・ハイライト）／ひげ／鼻
- 動き：頭の向き XYZ、体の向き、目の開閉、目玉、口の開閉と形、舌、耳、しっぽ、呼吸、ほお、ひげ、前足
