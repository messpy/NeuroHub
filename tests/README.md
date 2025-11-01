# 🧪 NeuroHub LLM Test Suite

このディレクトリには、NeuroHub プロジェクトの LLM 各プロバイダ（Gemini / Hugging Face / Ollama）の
動作確認を行うスクリプト群が含まれています。

---

## 📁 構成

| ファイル名 | 概要 |
|-------------|------|
| `test_llm_suite.py` | まとめて / 単体指定で LLM テストを実行する統合ハーネス |
| `test_llm_run.py`   | 旧版：Ollama / Gemini / HuggingFace を順にテスト |
| `test_env_load.py`  | `.env` の読込確認用（キーが正しく反映されているか） |
| `test_provider_gemini.py` | Gemini 単体テスト |
| `test_provider_hf.py`     | Hugging Face Router 単体テスト |
| `test_provider_ollama.py` | Ollama 単体テスト |
| `test_config_preview.py`  | `_archive/gen_config_preview.sh` の出力検査 |
| `run_smoke.sh`       | 一括スモークテスト実行（Makefile 代用） |

---

## 🚀 実行準備

```bash
cd ~/work/NeuroHub
source venv/bin/activate   # 仮想環境を有効化
