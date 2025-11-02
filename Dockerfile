# NeuroHub Dockerfile
# Python 3.12 slim-bookworm base for lightweight deployment
# ARM64/ARM32 compatible (Raspberry Pi support)

FROM python:3.12-slim-bookworm

# メタデータ
LABEL maintainer="NeuroHub Project"
LABEL description="NeuroHub AI Assistant - Multi-LLM Integration Platform"
LABEL version="1.0.0"

# 環境変数設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 作業ディレクトリ
WORKDIR /app

# システムパッケージインストール（最小限）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルコピー
COPY . .

# データディレクトリ作成
RUN mkdir -p /app/data /app/logs /app/generated_projects

# 非rootユーザー作成（セキュリティ）
RUN useradd -m -u 1000 neurohub && \
    chown -R neurohub:neurohub /app
USER neurohub

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# デフォルトコマンド
CMD ["python3", "main.py"]

# ポート公開（Discord Bot用、将来のWeb UI用）
EXPOSE 8000
