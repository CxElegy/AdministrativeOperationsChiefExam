# Live2D 用 MCP サーバー 3 つを このパソコンに入れて、Claude Code に登録する
# 使い方（PowerShell）：  powershell -ExecutionPolicy Bypass -File setup.ps1
# 先に Live2D Cubism Editor を 公式サイトから入れておくこと（5.3.03 / 5.3.04、または 5.4）
param([string]$Dir = "D:\Claude\live2d-mcp")
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force $Dir | Out-Null
function Need($cmd, $hint) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "$cmd がありません：$hint" } }
Need git    "https://git-scm.com/ から入れてください"
Need claude "Claude Code を入れてください"

# ---- 0. uv（Python を自動で用意する道具） ----
if (-not (Get-Command uvx -ErrorAction SilentlyContinue)) {
  Write-Host "uv を入れます"; powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

# ---- 1. cubism-mcp（nana7chi / Cubism Editor 5.4 の 外部連携 API） ----
claude mcp remove cubism-mcp -s user 2>$null
claude mcp add cubism-mcp -s user -e NO_PROXY=localhost,127.0.0.1 -- uvx cubism-mcp
Write-Host "[1/3] cubism-mcp を登録しました"

# ---- 2. cubism53-native-mcp（OranImp / Cubism Editor 5.3.03・5.3.04、メッシュとテクスチャを編集できる） ----
$zip = Join-Path $Dir "Cubism53-Native-MCP-win-x64.zip"; $nat = Join-Path $Dir "cubism53-native-mcp"
Invoke-WebRequest "https://github.com/OranImp/cubism53-native-mcp/releases/latest/download/Cubism53-Native-MCP-win-x64.zip" -OutFile $zip
Write-Host "SHA-256: $((Get-FileHash $zip -Algorithm SHA256).Hash)  ← リリースページの .sha256 と 同じか 確認してください"
Expand-Archive $zip $nat -Force
$setup = Get-ChildItem $nat -Recurse -Filter Setup.cmd | Select-Object -First 1
Push-Location $setup.DirectoryName; & .\Setup.cmd; Pop-Location     # ここで Editor の場所と モデルの作業フォルダを 聞かれる
$cfg = Get-ChildItem $nat -Recurse -Filter mcp.json | Where-Object { $_.FullName -match "client-configs" } | Select-Object -First 1
if ($cfg) {
  $j = Get-Content $cfg.FullName -Raw | ConvertFrom-Json; $p = $j.mcpServers.PSObject.Properties | Select-Object -First 1
  claude mcp remove $p.Name -s user 2>$null
  claude mcp add-json $p.Name ($p.Value | ConvertTo-Json -Compress -Depth 20) -s user
  Write-Host "[2/3] $($p.Name) を登録しました"
} else { Write-Host "[2/3] client-configs の mcp.json が 見つかりません。Setup.cmd の 表示を 確認してください" }

# ---- 3. live2d-automation（J621111 / 写真から 下書きモデル。作者いわく 実用前の段階） ----
$la = Join-Path $Dir "live2d-automation"
if (-not (Test-Path $la)) { git clone https://github.com/J621111/live2d-automation $la } else { git -C $la pull }
Push-Location $la; uv venv; uv pip install -e ".[vision-cpu]"; Pop-Location
$py = Join-Path $la ".venv\Scripts\python.exe"
claude mcp remove live2d-automation -s user 2>$null
claude mcp add live2d-automation -s user -e "PYTHONPATH=$la" -e "LIVE2D_OUTPUT_ROOT=$la\output" -- cmd /c "cd /d `"$la`" && `"$py`" -m mcp_server.server"
Write-Host "[3/3] live2d-automation を登録しました"

Write-Host ""; claude mcp list
Write-Host "`n次：Cubism Editor を開き、ファイル → 外部アプリケーション連携 を ON（ポート 22033）。Claude Code を 起動しなおす。"
