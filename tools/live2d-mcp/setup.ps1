# Live2D 用 MCP サーバー 3 つを このパソコンに入れて、Claude Code に登録する
# 使い方（PowerShell）：  powershell -ExecutionPolicy Bypass -File setup.ps1
# 先に Live2D Cubism Editor を 公式サイトから入れておくこと（5.3.03 / 5.3.04、または 5.4）
# このファイルは UTF-8（BOM つき）で保存すること。BOM が ないと Windows PowerShell 5.1 が 日本語を 読みまちがえる
# -Workspace（モデルの作業フォルダ）を 指定すると Setup.cmd を 質問なしで 動かす（入力できない ターミナル用）
param([string]$Dir = "D:\Claude\live2d-mcp", [string]$Workspace = "", [string]$EditorHome = "C:\Program Files\Live2D Cubism 5.3")
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"                                   # Invoke-WebRequest が 遅くならないように
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12   # PowerShell 5.1 で GitHub に つなぐため
New-Item -ItemType Directory -Force $Dir | Out-Null
function Need($cmd, $hint) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd がありません：$hint" } }
function Ok($what) { if ($LASTEXITCODE) { throw "$what が 失敗しました（終了コード $LASTEXITCODE）" } }
Need git    "https://git-scm.com/ から入れてください"
Need claude "Claude Code を入れてください"
# claude.ps1（npm の shim）だと PowerShell が「--」を 食べてしまうので、exe か cmd を 直接使う
$claude = (Get-Command claude -CommandType Application | Select-Object -First 1).Source
# 登録が まだ ないときの エラー表示（stderr）で 止まらないように（5.1 は Stop だと stderr で 例外になる）
function Unreg($name) { $ErrorActionPreference = "Continue"; & $claude mcp remove $name -s user 2>&1 | Out-Null }

# ---- 0. uv（Python を自動で用意する道具） ----
if (-not (Get-Command uvx -ErrorAction SilentlyContinue)) {
  Write-Host "uv を入れます"; powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
# Claude デスクトップアプリ（MSIX）から 動かすと AppData が 仮想化され、uv の Python のリンクが こわれるので、$Dir の中に 入れる
if (-not $env:UV_PYTHON_INSTALL_DIR) { $env:UV_PYTHON_INSTALL_DIR = Join-Path $Dir "uv-python" }
$uvx = (Get-Command uvx).Source   # Claude Code が 古い PATH のままでも 動くように フルパスで登録

# ---- 1. cubism-mcp（nana7chi / Cubism Editor 5.4 の 外部連携 API） ----
Unreg cubism-mcp
& $claude mcp add cubism-mcp -s user -e NO_PROXY=localhost,127.0.0.1 -- $uvx cubism-mcp; Ok "cubism-mcp の登録"
Write-Host "[1/3] cubism-mcp を登録しました"

# ---- 2. cubism53-native-mcp（OranImp / Cubism Editor 5.3.03・5.3.04、メッシュとテクスチャを編集できる） ----
$zip = Join-Path $Dir "Cubism53-Native-MCP-win-x64.zip"; $nat = Join-Path $Dir "cubism53-native-mcp"
$rel = "https://github.com/OranImp/cubism53-native-mcp/releases/latest/download/Cubism53-Native-MCP-win-x64.zip"
Invoke-WebRequest $rel -OutFile $zip -UseBasicParsing
Invoke-WebRequest "$rel.sha256" -OutFile "$zip.sha256" -UseBasicParsing
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash
$want = ((Get-Content "$zip.sha256" -Raw) -split '\s+')[0]
Write-Host "SHA-256: $hash"
Write-Host "公開値 : $want"
if ($hash -ine $want) { throw "SHA-256 が リリースページの .sha256 と ちがいます。中止します" }
Expand-Archive $zip $nat -Force
$setup = Get-ChildItem $nat -Recurse -Filter Setup.cmd | Select-Object -First 1
if ($Workspace) { New-Item -ItemType Directory -Force $Workspace | Out-Null; $setupArgs = @("--non-interactive", "--editor-home", $EditorHome, "--workspace", $Workspace) } else { $setupArgs = @() }
Push-Location $setup.DirectoryName; & .\Setup.cmd @setupArgs; $code = $LASTEXITCODE; Pop-Location   # ここで Editor の場所と モデルの作業フォルダを 聞かれる
if ($code) { throw "Setup.cmd が 失敗しました（終了コード $code）" }
# Setup.cmd は 設定を %LOCALAPPDATA%\Cubism53MCP\profiles\default\client-configs\mcp.json に 書く（ZIP の中ではない）
$cfg = Join-Path $env:LOCALAPPDATA "Cubism53MCP\profiles\default\client-configs\mcp.json"
if (Test-Path $cfg) {
  $j = Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json; $p = $j.mcpServers.PSObject.Properties | Select-Object -First 1
  # add-json に JSON を 渡すと 5.1 が「"」を 消すので、command と args で 登録する
  Unreg $p.Name
  & $claude mcp add $p.Name -s user -- $p.Value.command @($p.Value.args); Ok "$($p.Name) の登録"
  Write-Host "[2/3] $($p.Name) を登録しました"
} else { Write-Host "[2/3] $cfg が 見つかりません。Setup.cmd の 表示を 確認してください" }

# ---- 3. live2d-automation（J621111 / 写真から 下書きモデル。作者いわく 実用前の段階） ----
$la = Join-Path $Dir "live2d-automation"
if (-not (Test-Path $la)) { git clone https://github.com/J621111/live2d-automation $la } else { git -C $la pull }
Ok "git（live2d-automation）"
Push-Location $la
if (-not (Test-Path ".venv")) { uv venv --python 3.12; Ok "uv venv" }      # mediapipe が 使える 3.12 に そろえる
uv pip install -e ".[vision-cpu]"; Ok "uv pip install"
Pop-Location
$py = Join-Path $la ".venv\Scripts\python.exe"
Unreg live2d-automation
# サーバーは 自分の場所から 出力先を 決めるので、cd は いらない（cmd /c の 入れ子の「"」は 5.1 で こわれる）
& $claude mcp add live2d-automation -s user -e "PYTHONPATH=$la" -e "LIVE2D_OUTPUT_ROOT=$la\output" -- $py -m mcp_server.server; Ok "live2d-automation の登録"
Write-Host "[3/3] live2d-automation を登録しました"

Write-Host ""; & $claude mcp list
Write-Host "`n次：Cubism Editor を開き、ファイル → 外部アプリケーション連携 を ON（ポート 22033）。Claude Code を 起動しなおす。"
