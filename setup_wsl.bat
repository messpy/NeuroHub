@echo off
REM NeuroHub Windows to WSL Migration Script
REM WindowsからWSL Linuxへの移行スクリプト

echo ============================================
echo  NeuroHub Linux Environment Setup (WSL)
echo ============================================
echo.

echo [INFO] NeuroHubはLinuxベースで設計されています
echo [INFO] Windows環境では以下の問題が発生します:
echo   - パス区切り文字の混在 (/usr/bin\python.exe)
echo   - Linuxコマンドの非対応 (ls -la, which, python3)
echo   - 権限管理の違い (chmod, etc.)
echo.

echo [推奨] WSL (Windows Subsystem for Linux) を使用してください
echo.

REM WSLの確認
echo [1/4] WSL環境チェック...
wsl --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] WSLがインストール済みです
    goto :wsl_setup
) else (
    echo [WARNING] WSLがインストールされていません
    goto :wsl_install
)

:wsl_install
echo.
echo [2/4] WSLインストール手順:
echo   1. PowerShellを管理者として開く
echo   2. 以下のコマンドを実行:
echo      wsl --install -d Ubuntu-22.04
echo   3. 再起動後、Ubuntuが自動起動
echo   4. 新しいユーザー名とパスワードを設定
echo.
echo [INFO] WSLインストール後、このスクリプトを再実行してください
pause
exit /b 1

:wsl_setup
echo [2/4] NeuroHubプロジェクトをWSLにコピー...
if not exist "%CD%\copy_to_wsl.sh" (
    echo #!/bin/bash > copy_to_wsl.sh
    echo # NeuroHub to WSL Copy Script >> copy_to_wsl.sh
    echo echo "NeuroHub プロジェクトをWSL環境にセットアップ中..." >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # プロジェクトディレクトリ作成 >> copy_to_wsl.sh
    echo mkdir -p ~/projects >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # Windowsからファイルコピー >> copy_to_wsl.sh
    echo echo "ファイルをコピー中..." >> copy_to_wsl.sh
    echo cp -r /mnt/c/Users/kenny/sandbox/NeuroHub ~/projects/neurohub >> copy_to_wsl.sh
    echo cd ~/projects/neurohub >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # システム更新 >> copy_to_wsl.sh
    echo echo "システムパッケージを更新中..." >> copy_to_wsl.sh
    echo sudo apt update ^&^& sudo apt upgrade -y >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # 必要パッケージインストール >> copy_to_wsl.sh
    echo echo "Python環境をセットアップ中..." >> copy_to_wsl.sh
    echo sudo apt install -y python3 python3-pip python3-venv git curl build-essential >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # 仮想環境セットアップ >> copy_to_wsl.sh
    echo echo "Python仮想環境を作成中..." >> copy_to_wsl.sh
    echo python3 -m venv venv >> copy_to_wsl.sh
    echo source venv/bin/activate >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # 依存関係インストール >> copy_to_wsl.sh
    echo echo "Python依存関係をインストール中..." >> copy_to_wsl.sh
    echo pip install --upgrade pip >> copy_to_wsl.sh
    echo pip install -r requirements.txt >> copy_to_wsl.sh
    echo pip install -r requirements-dev.txt >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # 実行権限設定 >> copy_to_wsl.sh
    echo echo "実行権限を設定中..." >> copy_to_wsl.sh
    echo chmod +x quick_start_linux.sh run_tests_linux.sh >> copy_to_wsl.sh
    echo chmod +x tools/git_commit_ai 2^>/dev/null ^|^| true >> copy_to_wsl.sh
    echo find . -name "*.py" -exec chmod +x {} \; 2^>/dev/null ^|^| true >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # 環境変数設定 >> copy_to_wsl.sh
    echo echo "環境変数を設定中..." >> copy_to_wsl.sh
    echo echo 'export NEUROHUB_HOME=~/projects/neurohub' ^>^> ~/.bashrc >> copy_to_wsl.sh
    echo echo 'export PYTHONPATH=$NEUROHUB_HOME:$PYTHONPATH' ^>^> ~/.bashrc >> copy_to_wsl.sh
    echo echo 'export LC_ALL=C.UTF-8' ^>^> ~/.bashrc >> copy_to_wsl.sh
    echo echo 'export LANG=C.UTF-8' ^>^> ~/.bashrc >> copy_to_wsl.sh
    echo source ~/.bashrc >> copy_to_wsl.sh
    echo. >> copy_to_wsl.sh
    echo # セットアップ完了メッセージ >> copy_to_wsl.sh
    echo echo "=================================" >> copy_to_wsl.sh
    echo echo "✅ NeuroHub WSL セットアップ完了!" >> copy_to_wsl.sh
    echo echo "=================================" >> copy_to_wsl.sh
    echo echo >> copy_to_wsl.sh
    echo echo "次のコマンドでNeuroHubを実行できます:" >> copy_to_wsl.sh
    echo echo "  ./quick_start_linux.sh" >> copy_to_wsl.sh
    echo echo "  python3 agents/git_agent.py --status" >> copy_to_wsl.sh
    echo echo "  python3 agents/llm_agent.py --prompt 'Hello Linux!'" >> copy_to_wsl.sh
    echo echo "  ./run_tests_linux.sh" >> copy_to_wsl.sh
    echo echo >> copy_to_wsl.sh
    echo echo "詳細なコマンドガイド: LINUX_COMMANDS.md" >> copy_to_wsl.sh
)

echo [3/4] WSLでセットアップスクリプトを実行...
wsl bash copy_to_wsl.sh

echo.
echo [4/4] 完了! WSL Ubuntuでの使用方法:
echo   1. WSL Ubuntu を開く: wsl
echo   2. プロジェクトに移動: cd ~/projects/neurohub
echo   3. 仮想環境アクティベート: source venv/bin/activate
echo   4. クイックスタート: ./quick_start_linux.sh
echo.

echo ============================================
echo  Windows PowerShell での実行は非対応です
echo  必ずWSL Ubuntu環境で実行してください
echo ============================================
echo.

set /p choice="WSL Ubuntu を今すぐ起動しますか？ (y/N): "
if /i "%choice%"=="y" (
    echo WSL Ubuntu を起動中...
    wsl -d Ubuntu-22.04 -e bash -c "cd ~/projects/neurohub && exec bash"
) else (
    echo.
    echo 手動でWSLを起動する場合:
    echo   wsl
    echo   cd ~/projects/neurohub
    echo   source venv/bin/activate
    echo   ./quick_start_linux.sh
)

pause
