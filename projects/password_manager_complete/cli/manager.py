#!/usr/bin/env python3
"""
Click CLIパスワードマネージャー

コマンドライン インターフェースでパスワード管理機能を提供
完全なエラーハンドリング、ドキュメント、型ヒントを含む

Created by Ollama MCP Agent
"""

import os
import sys
import getpass
from typing import Optional, List
from pathlib import Path

# プロジェクトルートをpathに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
except ImportError as e:
    print(f"Click インポートエラー: {e}")
    print("pip install click を実行してください")
    sys.exit(1)

# ローカルモジュールのインポート
try:
    from src.main import PasswordManager
    from src.models import PasswordEntry
    from src.encryption import EncryptionManager
except ImportError as e:
    print(f"ローカルモジュール インポートエラー: {e}")
    print("src/ ディレクトリのモジュールが見つかりません")
    sys.exit(1)

# グローバル設定
DEFAULT_DB_PATH = "data/passwords.db"

def get_master_password() -> str:
    """
    マスターパスワードの取得

    Returns:
        str: マスターパスワード
    """
    # 環境変数から取得を試行
    master_password = os.getenv("MASTER_PASSWORD")

    if master_password:
        return master_password

    # 対話的に入力
    try:
        master_password = getpass.getpass("マスターパスワードを入力してください: ")
        if not master_password:
            click.echo("❌ マスターパスワードは必須です", err=True)
            sys.exit(1)
        return master_password
    except KeyboardInterrupt:
        click.echo("\n中断されました")
        sys.exit(1)

def create_password_manager(db_path: str = DEFAULT_DB_PATH) -> PasswordManager:
    """
    パスワードマネージャーの作成

    Args:
        db_path: データベースファイルのパス

    Returns:
        PasswordManager: パスワードマネージャーインスタンス
    """
    try:
        master_password = get_master_password()
        return PasswordManager(db_path=db_path, master_password=master_password)
    except Exception as e:
        click.echo(f"❌ パスワードマネージャー初期化エラー: {e}", err=True)
        sys.exit(1)

# メインCLIグループ
@click.group()
@click.option('--db-path', default=DEFAULT_DB_PATH, help='データベースファイルのパス')
@click.option('--verbose', '-v', is_flag=True, help='詳細出力')
@click.pass_context
def cli(ctx: click.Context, db_path: str, verbose: bool):
    """
    パスワードマネージャー CLI

    Ollama MCP で生成されたパスワードマネージャーのコマンドライン インターフェース
    """
    # コンテキストオブジェクトの初期化
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db_path
    ctx.obj['verbose'] = verbose

    if verbose:
        click.echo(f"📂 データベースパス: {db_path}")

@cli.command()
@click.option('--site', '-s', prompt='サイト名', help='サイト名')
@click.option('--username', '-u', prompt='ユーザー名', help='ユーザー名')
@click.option('--password', '-p', help='パスワード（省略時は自動生成）')
@click.option('--notes', '-n', default='', help='備考')
@click.option('--generate', '-g', is_flag=True, help='安全なパスワードを自動生成')
@click.pass_context
def add(ctx: click.Context, site: str, username: str, password: Optional[str], notes: str, generate: bool):
    """パスワードエントリの追加"""
    try:
        manager = create_password_manager(ctx.obj['db_path'])

        # パスワードの処理
        if generate or not password:
            if generate:
                password = generate_secure_password()
                click.echo(f"🔐 生成されたパスワード: {password}")
            else:
                password = getpass.getpass("パスワードを入力してください: ")

        if not password:
            click.echo("❌ パスワードは必須です", err=True)
            return

        # エントリの追加
        success = manager.add_password(site, username, password, notes)

        if success:
            click.echo(f"✅ パスワードエントリを追加しました: {site}/{username}")
        else:
            click.echo(f"❌ パスワードエントリの追加に失敗しました: {site}/{username}", err=True)

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.option('--site', '-s', prompt='サイト名', help='サイト名')
@click.option('--username', '-u', help='ユーザー名（省略時は最初のエントリ）')
@click.option('--show-password', '-p', is_flag=True, help='パスワードを表示')
@click.option('--copy', '-c', is_flag=True, help='パスワードをクリップボードにコピー')
@click.pass_context
def get(ctx: click.Context, site: str, username: Optional[str], show_password: bool, copy: bool):
    """パスワードエントリの取得"""
    try:
        manager = create_password_manager(ctx.obj['db_path'])

        # エントリの取得
        entry_data = manager.get_password(site, username)

        if entry_data is None:
            click.echo(f"❌ パスワードエントリが見つかりません: {site}", err=True)
            return

        # 基本情報の表示
        click.echo(f"📋 サイト: {entry_data['site']}")
        click.echo(f"👤 ユーザー名: {entry_data['username']}")
        click.echo(f"📝 備考: {entry_data.get('notes', '')}")
        click.echo(f"📅 作成日時: {entry_data['created_at']}")
        click.echo(f"🔄 更新日時: {entry_data['updated_at']}")

        # パスワードの処理
        password = entry_data['password']

        if show_password:
            click.echo(f"🔐 パスワード: {password}")
        else:
            click.echo(f"🔐 パスワード: {'*' * len(password)}")

        if copy:
            try:
                import pyperclip
                pyperclip.copy(password)
                click.echo("📋 パスワードをクリップボードにコピーしました")
            except ImportError:
                click.echo("⚠️  クリップボード機能には pyperclip が必要です: pip install pyperclip")
            except Exception as e:
                click.echo(f"⚠️  クリップボードへのコピーに失敗しました: {e}")

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.option('--search', '-s', help='検索キーワード')
@click.option('--limit', '-l', default=50, help='表示件数の上限')
@click.pass_context
def list(ctx: click.Context, search: Optional[str], limit: int):
    """パスワードエントリの一覧表示"""
    try:
        manager = create_password_manager(ctx.obj['db_path'])

        # エントリの取得
        entries = manager.list_entries()

        if not entries:
            click.echo("📭 パスワードエントリがありません")
            return

        # 検索フィルタリング（簡単な実装）
        if search:
            search_lower = search.lower()
            entries = [
                entry for entry in entries
                if search_lower in entry.get('site', '').lower()
                or search_lower in entry.get('username', '').lower()
                or search_lower in entry.get('notes', '').lower()
            ]

        # 件数制限
        if len(entries) > limit:
            entries = entries[:limit]
            click.echo(f"⚠️  表示件数を {limit} 件に制限しました")

        # 一覧表示
        click.echo(f"📋 パスワードエントリ一覧 ({len(entries)}件)")
        click.echo("-" * 60)

        for i, entry in enumerate(entries, 1):
            click.echo(f"{i:3d}. {entry.get('site'):30s} | {entry.get('username'):20s}")
            if entry.get('notes'):
                click.echo(f"     📝 {entry.get('notes')}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.option('--site', '-s', prompt='サイト名', help='サイト名')
@click.option('--username', '-u', help='ユーザー名（省略時は全ユーザー）')
@click.confirmation_option(prompt='本当に削除しますか？')
@click.pass_context
def delete(ctx: click.Context, site: str, username: Optional[str]):
    """パスワードエントリの削除"""
    try:
        manager = create_password_manager(ctx.obj['db_path'])

        # 削除前に確認
        entry_data = manager.get_password(site, username)
        if entry_data is None:
            click.echo(f"❌ パスワードエントリが見つかりません: {site}", err=True)
            return

        # エントリの削除
        success = manager.delete_password(site, username)

        if success:
            click.echo(f"✅ パスワードエントリを削除しました: {site}/{username or 'all'}")
        else:
            click.echo(f"❌ パスワードエントリの削除に失敗しました: {site}", err=True)

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.option('--query', '-q', prompt='検索キーワード', help='検索キーワード')
@click.pass_context
def search(ctx: click.Context, query: str):
    """パスワードエントリの検索"""
    try:
        # 簡単な実装：listコマンドと同様の処理
        ctx.invoke(list, search=query)

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.option('--length', '-l', default=16, help='パスワードの長さ')
@click.option('--no-symbols', is_flag=True, help='記号を使用しない')
@click.option('--no-numbers', is_flag=True, help='数字を使用しない')
def generate(length: int, no_symbols: bool, no_numbers: bool):
    """安全なパスワードの生成"""
    try:
        password = generate_secure_password(
            length=length,
            use_symbols=not no_symbols,
            use_numbers=not no_numbers
        )

        click.echo(f"🔐 生成されたパスワード: {password}")

        # クリップボードにコピー
        try:
            import pyperclip
            pyperclip.copy(password)
            click.echo("📋 パスワードをクリップボードにコピーしました")
        except ImportError:
            click.echo("💡 クリップボード機能には pyperclip が必要です: pip install pyperclip")
        except Exception:
            pass  # エラーは無視

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

@cli.command()
@click.pass_context
def stats(ctx: click.Context):
    """データベース統計情報の表示"""
    try:
        manager = create_password_manager(ctx.obj['db_path'])

        # 統計情報の取得（簡単な実装）
        entries = manager.list_entries()

        sites = set(entry.get('site', '') for entry in entries)

        click.echo("📊 データベース統計情報")
        click.echo("-" * 30)
        click.echo(f"総エントリ数: {len(entries)}")
        click.echo(f"ユニークサイト数: {len(sites)}")

        if ctx.obj['verbose'] and entries:
            click.echo(f"最新エントリ: {max(entries, key=lambda x: x.get('created_at', ''))['site']}")
            click.echo(f"最古エントリ: {min(entries, key=lambda x: x.get('created_at', ''))['site']}")

    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)

def generate_secure_password(length: int = 16, use_symbols: bool = True, use_numbers: bool = True) -> str:
    """
    安全なパスワードの生成

    Args:
        length: パスワードの長さ
        use_symbols: 記号を使用するか
        use_numbers: 数字を使用するか

    Returns:
        str: 生成されたパスワード
    """
    try:
        import secrets
        import string

        # 文字セットの構築
        chars = string.ascii_letters
        if use_numbers:
            chars += string.digits
        if use_symbols:
            chars += "!@#$%^&*"

        # パスワード生成
        password = ''.join(secrets.choice(chars) for _ in range(length))

        return password

    except Exception as e:
        # フォールバック実装
        import random
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if use_numbers:
            chars += "0123456789"
        if use_symbols:
            chars += "!@#$%^&*"

        return ''.join(random.choice(chars) for _ in range(length))

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 予期しないエラー: {e}", err=True)
        sys.exit(1)
