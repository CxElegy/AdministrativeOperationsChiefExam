# Live2D 用 MCP（Claude Code から Cubism Editor を動かす）

アナちゃんの モデル（頭の部品・ほおの毛・メッシュ）を Cubism Editor で 直すための 道具。
**この 3 つは Cubism Editor と同じパソコンで 動く**ので、クラウドのセッションからは 使えない。

| 名前 | 対応 Editor | できること |
|---|---|---|
| `cubism-mcp`（[nana7chi](https://github.com/nana7chi/CubismExternalEditMCP)） | 5.4 Alpha（Windows / Mac） | パラメータ・パーツ・デフォーマの 追加と編集（42 ツール）。テクスチャ・メッシュの頂点編集は なし |
| `cubism53-native-mcp`（[OranImp](https://github.com/OranImp/cubism53-native-mcp)） | 5.3.03 / 5.3.04（Windows のみ） | テクスチャ差し替え、メッシュ作りなおし・頂点編集、PSD 読み込み、書き出し（84 ツール）。**アナちゃんに いちばん 役立つ** |
| `live2d-automation`（[J621111](https://github.com/J621111/live2d-automation)） | — | 写真から 下書き。作者いわく 本番用モデルは 出ない |

## 入れ方（Windows）

1. Live2D 公式サイトから Cubism Editor を入れる（native-mcp を使うなら 5.3.03 か 5.3.04）。
2. このフォルダの `install.cmd` を ダブルクリック（Editor・git・claude を 確かめてから setup.ps1 を 動かす）。または：`powershell -ExecutionPolicy Bypass -File setup.ps1`（入れる場所は `-Dir` で変えられる。既定 `D:\Claude\live2d-mcp`）
3. Cubism Editor：ファイル → 外部アプリケーション連携 を ON（ポート 22033）、`cubism-mcp` / `Cubism53 Native MCP` を「許可・編集」。Editor を 再起動するたびに 必要。
4. Claude Code を 起動しなおし、`claude mcp list` で 3 つが出ることを確認。

## 注意

- 3 つとも 個人が作ったもので、Live2D 社の公式ではない。
- 5.4 Alpha は 2026-09-14 が期限と書かれている。期限切れなら `cubism-mcp` は 新しい 5.4 版が出るまで 使えないかもしれない。
- native-mcp の ZIP は setup.ps1 が リリースの `.sha256` と SHA-256 を 照らし合わせ、ちがえば 止まる（v0.3.0 の値：`f69bda420f8c481e502fb5568c34d32baf0e582e257d814882c6e3691acd34a2`）。
- Tororo を 編集するには 元データ（`.cmo3`）が いる。公式サンプル（Tororo & Hijiki）の ダウンロードには `.cmo3`（モデル）と `.can3`（モーション）が 入っている（2026-11 時点、サンプルデータ利用規約に 同意が 必要）。
