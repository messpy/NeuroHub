#!/usr/bin/env bash
# ============================================
# NeuroHub プロジェクト構成作成スクリプト
# カレントディレクトリが /home/kennypi/apps/NeuroHub である前提
# ============================================

BASE=$(pwd)

# ① 基本構成フォルダ
mkdir -p $BASE/{config,lib,logs,scripts,tools}

# ② モデル格納フォルダ（各種AIモデル用）
mkdir -p $BASE/models/{ollama,piper,whisper}

# ③ データ関連（キャッシュ・DL用）
mkdir -p $BASE/data/{cache/{asr,tts,mpv,llm},downloads}

# ④ サービス層（機能ごとに分割）
mkdir -p $BASE/services/{llm,audio,api,discord_bot/handlers}

# ⑤ ドキュメント関連（手順書・設計書）
mkdir -p $BASE/docs
cat <<'EOF' > $BASE/docs/README.md
# 🧠 NeuroHub Docs
このフォルダには設計書や手順書を保存します。
- `architecture.md`: 全体構成やモジュール設計
- `setup_guide.md`: セットアップ・実行方法
EOF

# ⑥ アーカイブ（旧構成・実験スクリプトなど）
mkdir -p $BASE/_archive
cat <<'EOF' > $BASE/_archive/README.md
# _archive
過去の構成・一時スクリプト・検証用データを保管します。
実運用には使用しません。
EOF

# ⑦ 設定ファイルを作成
touch $BASE/config/{config.yaml,.env}

# ⑧ 完了メッセージ
echo "✅ NeuroHub 構成を作成しました。"
echo "📁 ルート: $BASE"
echo "┣ config, lib, logs, scripts, tools"
echo "┣ models/{ollama,piper,whisper}"
echo "┣ data/{cache,downloads}"
echo "┣ services/{llm,audio,api,discord_bot}"
echo "┣ docs/, _archive/"
echo "┗ config.yaml, .env 初期化済"
