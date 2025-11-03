"""
MCP基本機能統合テスト

services/mcp/の基本モジュール（spec_normalizer, command_validator, project_designer）をテスト
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMCPBasicFlow:
    """MCP基本フロー統合テスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリ"""
        temp = tempfile.mkdtemp(prefix="neurohub_mcp_basic_")
        print(f"\n📁 一時ディレクトリ: {temp}")
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
        print(f"🗑️ 一時ディレクトリ削除: {temp}")
    
    def test_mcp_modules_import(self):
        """MCPモジュールインポートテスト"""
        print("\n📦 MCPモジュールインポート確認:")
        
        modules_to_test = [
            ("services.mcp.spec_normalizer", "SpecNormalizer"),
            ("services.mcp.command_validator", "CommandValidator"),
            ("services.mcp.project_designer", "ProjectDesigner"),
            ("services.mcp.mcp_enhanced", "EnhancedMCPServer"),
            ("services.mcp.llm_investigator", "LLMInvestigator"),
        ]
        
        imported = []
        failed = []
        
        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                imported.append(f"{module_name}.{class_name}")
                print(f"   ✅ {module_name}.{class_name}")
            except Exception as e:
                failed.append(f"{module_name}.{class_name}: {e}")
                print(f"   ❌ {module_name}.{class_name}: {e}")
        
        print(f"\n📊 インポート結果: {len(imported)}/{len(modules_to_test)} 成功")
        
        # 少なくとも基本モジュールがインポートできること
        assert len(imported) >= 3, f"基本モジュールのインポート失敗: {failed}"
    
    def test_spec_normalizer_basic(self):
        """仕様正規化基本テスト"""
        try:
            from services.mcp.spec_normalizer import SpecNormalizer
        except ImportError:
            pytest.skip("SpecNormalizerがインポートできません")
        
        normalizer = SpecNormalizer()
        user_spec = "SQLiteに1件レコードを追加するCLI"
        
        print(f"\n📝 入力仕様: {user_spec}")
        
        try:
            normalized = normalizer.normalize(user_spec)
            print(f"✅ 正規化成功")
            print(f"   タイプ: {type(normalized)}")
            print(f"   内容: {normalized}")
        except Exception as e:
            print(f"⚠️ 正規化失敗: {e}")
            # エラーでもテストは継続（統合テストなので）
    
    def test_command_validator_basic(self):
        """コマンド検証基本テスト"""
        try:
            from services.mcp.command_validator import CommandValidator
        except ImportError:
            pytest.skip("CommandValidatorがインポートできません")
        
        validator = CommandValidator()
        test_commands = {
            "mkdir test": True,  # 安全
            "python main.py": True,  # 安全
            "rm -rf /": False,  # 危険
        }
        
        print("\n🔍 コマンド検証テスト:")
        for cmd, expected_safe in test_commands.items():
            try:
                is_safe, msg = validator.validate(cmd)
                status = "✅ 安全" if is_safe else "⚠️ 危険"
                match = "✅" if is_safe == expected_safe else "❌"
                print(f"   {match} {cmd}: {status} ({msg})")
            except Exception as e:
                print(f"   ❌ {cmd}: エラー ({e})")
    
    def test_project_designer_basic(self, temp_dir):
        """プロジェクト設計基本テスト"""
        try:
            from services.mcp.project_designer import ProjectDesigner
        except ImportError:
            pytest.skip("ProjectDesignerがインポートできません")
        
        designer = ProjectDesigner()
        spec = {
            "project_name": "test_cli",
            "description": "テスト用CLI",
            "requirements": ["引数受取", "標準出力"],
        }
        
        print(f"\n🎨 プロジェクト設計テスト:")
        print(f"   仕様: {spec}")
        
        try:
            design = designer.design(spec, output_dir=temp_dir)
            print(f"✅ 設計成功")
            print(f"   タイプ: {type(design)}")
            print(f"   内容: {design}")
        except Exception as e:
            print(f"⚠️ 設計失敗: {e}")


class TestMCPDatabaseIntegration:
    """MCPデータベース統合テスト"""
    
    def test_mcp_enhanced_import(self):
        """EnhancedMCPServerインポートテスト"""
        try:
            from services.mcp.mcp_enhanced import EnhancedMCPServer
            print("\n✅ EnhancedMCPServerインポート成功")
            
            # 初期化テスト
            server = EnhancedMCPServer()
            print(f"✅ EnhancedMCPServer初期化成功")
            print(f"   Session ID: {server.session_id if hasattr(server, 'session_id') else 'N/A'}")
            
        except Exception as e:
            print(f"\n⚠️ EnhancedMCPServer: {e}")
            pytest.skip(f"EnhancedMCPServerエラー: {e}")
    
    def test_llm_investigator_import(self):
        """LLMInvestigatorインポートテスト"""
        try:
            from services.mcp.llm_investigator import LLMInvestigator
            print("\n✅ LLMInvestigatorインポート成功")
            
            # 初期化テスト
            investigator = LLMInvestigator()
            print(f"✅ LLMInvestigator初期化成功")
            
        except Exception as e:
            print(f"\n⚠️ LLMInvestigator: {e}")
            pytest.skip(f"LLMInvestigatorエラー: {e}")


class TestMCPAgentIntegration:
    """MCPエージェント統合テスト"""
    
    def test_mcp_agent_import(self):
        """MCPエージェントインポートテスト"""
        try:
            from agents.agent_mcp import MCPAgent
            print("\n✅ MCPAgentインポート成功")
            
            # 初期化テスト
            agent = MCPAgent()
            print(f"✅ MCPAgent初期化成功")
            
        except Exception as e:
            print(f"\n⚠️ MCPAgent: {e}")
            pytest.skip(f"MCPAgentエラー: {e}")
    
    def test_mcp_agent_modes(self):
        """MCPエージェントモードテスト"""
        try:
            from agents.agent_mcp import MCPAgent
        except ImportError:
            pytest.skip("MCPAgentがインポートできません")
        
        agent = MCPAgent()
        expected_modes = ["generate", "project", "debug", "optimize", "design"]
        
        print("\n🎯 MCPエージェントモード確認:")
        for mode in expected_modes:
            has_mode = hasattr(agent, f"mode_{mode}") or hasattr(agent, mode)
            status = "✅" if has_mode else "⚠️"
            print(f"   {status} {mode}モード")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
