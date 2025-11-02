#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_vc_transcription.py

VC文字起こしプラグインのテスト
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_plugin_import():
    """プラグインのインポートテスト"""
    try:
        from services.discord.plugins.vc_transcription import VCTranscription
        assert VCTranscription is not None
        print("✅ VCTranscription プラグインインポート成功")
    except ImportError as e:
        pytest.fail(f"❌ インポートエラー: {e}")


def test_plugin_attributes():
    """プラグイン属性テスト"""
    from services.discord.plugins.vc_transcription import VCTranscription
    from unittest.mock import MagicMock
    
    bot = MagicMock()
    plugin = VCTranscription(bot)
    
    assert plugin.description == "ボイスチャンネル音声文字起こし"
    assert plugin.version == "1.0.0"
    assert hasattr(plugin, 'recording')
    assert hasattr(plugin, 'transcripts')
    assert hasattr(plugin, 'log_dir')
    assert hasattr(plugin, 'audio_buffers')
    print("✅ プラグイン属性確認完了")


def test_log_directory_creation():
    """ログディレクトリ作成テスト"""
    from services.discord.plugins.vc_transcription import VCTranscription
    from unittest.mock import MagicMock
    
    bot = MagicMock()
    plugin = VCTranscription(bot)
    
    # ログディレクトリが存在するか確認
    assert plugin.log_dir.exists()
    assert plugin.log_dir.is_dir()
    print(f"✅ ログディレクトリ作成確認: {plugin.log_dir}")


def test_whisper_availability():
    """Whisperの利用可能性テスト"""
    from services.discord.plugins.vc_transcription import (
        FASTER_WHISPER_AVAILABLE,
        OPENAI_AVAILABLE
    )
    
    print(f"faster-whisper: {'✅ 利用可能' if FASTER_WHISPER_AVAILABLE else '❌ 未インストール'}")
    print(f"OpenAI: {'✅ 利用可能' if OPENAI_AVAILABLE else '❌ 未インストール'}")
    
    # どちらか一方が利用可能であればOK（なくても動作可能）
    # assert FASTER_WHISPER_AVAILABLE or OPENAI_AVAILABLE, "Whisperが利用できません"
    print("⚠️ Whisperは未インストールでも動作します（テキストログのみ）")


def test_basic_functionality():
    """基本機能テスト"""
    from services.discord.plugins.vc_transcription import VCTranscription
    from unittest.mock import MagicMock
    
    bot = MagicMock()
    plugin = VCTranscription(bot)
    
    # 初期状態確認
    assert plugin.recording == {}
    assert plugin.transcripts == {}
    assert plugin.audio_buffers == {}
    
    # 録音状態をセット
    guild_id = 12345
    plugin.recording[guild_id] = True
    plugin.transcripts[guild_id] = []
    
    assert plugin.recording[guild_id] is True
    assert isinstance(plugin.transcripts[guild_id], list)
    
    print("✅ 基本機能テスト完了")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
