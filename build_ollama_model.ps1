# Ollama Modelfile ビルドスクリプト (PowerShell用)

param(
    [string]$ModelfileKey = "db",
    [switch]$Test
)

$ErrorActionPreference = "Stop"

# 利用可能なModelfile定義
$Modelfiles = @{
    "db" = @{
        "Path" = "modelfiles\db_sample_assistant.Modelfile"
        "Name" = "neurohub-db-assistant"
        "Description" = "DatabaseManagerサンプルコード参照アシスタント"
    }
}

Write-Host ""
Write-Host "🤖 NeuroHub Ollama Modelfile ビルドシステム" -ForegroundColor Cyan
Write-Host ""

# Modelfile選択
if (-not $Modelfiles.ContainsKey($ModelfileKey)) {
    Write-Host "❌ エラー: '$ModelfileKey' は無効な選択です" -ForegroundColor Red
    Write-Host ""
    Write-Host "利用可能なModelfile:" -ForegroundColor Yellow
    foreach ($key in $Modelfiles.Keys) {
        $info = $Modelfiles[$key]
        Write-Host "  [$key] $($info.Description)"
        Write-Host "      ファイル: $($info.Path)"
        Write-Host "      モデル名: $($info.Name)"
    }
    exit 1
}

$Selected = $Modelfiles[$ModelfileKey]
$ModelfilePath = $Selected.Path
$ModelName = $Selected.Name

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🔨 Ollama カスタムモデルビルド" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "📄 Modelfile: $ModelfilePath"
Write-Host "🏷️  モデル名: $ModelName"
Write-Host "--------------------------------------------------------------------------------"

# Modelfileの存在確認
if (-not (Test-Path $ModelfilePath)) {
    Write-Host "❌ エラー: Modelfileが見つかりません: $ModelfilePath" -ForegroundColor Red
    exit 1
}

# Ollamaのインストール確認
try {
    $null = Get-Command ollama -ErrorAction Stop
} catch {
    Write-Host "❌ エラー: ollamaコマンドが見つかりません" -ForegroundColor Red
    Write-Host "Ollamaをインストールしてください: https://ollama.com/"
    exit 1
}

Write-Host "🚀 モデルをビルド中..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------------------------"

try {
    # モデルビルド
    $output = ollama create $ModelName -f $ModelfilePath 2>&1

    Write-Host ""
    Write-Host "✅ モデルビルド成功!" -ForegroundColor Green
    Write-Host "--------------------------------------------------------------------------------"
    Write-Host $output
    Write-Host "--------------------------------------------------------------------------------"

    # モデル一覧表示
    Write-Host ""
    Write-Host "📋 登録されているモデル一覧:" -ForegroundColor Cyan
    Write-Host "--------------------------------------------------------------------------------"
    ollama list

    # テスト実行
    if ($Test) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Cyan
        Write-Host "🧪 モデルテスト: $ModelName" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Cyan
        $testPrompt = "usersテーブル(id, name, email)を作成して、2件データを挿入して、全件取得するコードを書いて"
        Write-Host "プロンプト: $testPrompt"
        Write-Host "--------------------------------------------------------------------------------"

        ollama run $ModelName $testPrompt
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "🎉 完了!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  ollama run $ModelName `"プロンプト`""
    Write-Host ""
    Write-Host "  または、LLMAgentで:" -ForegroundColor Yellow
    Write-Host "    llm = LLMAgent(provider='ollama', model='$ModelName')"

} catch {
    Write-Host ""
    Write-Host "❌ モデルビルド失敗" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
