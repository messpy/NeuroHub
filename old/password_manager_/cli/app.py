"""
CLIアプリケーション
"""
import click
import sys
import os
from getpass import getpass
from typing import Optional
import json
from tabulate import tabulate

# パッケージパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.password_manager import PasswordManager
from src.config import Config

# グローバルパスワードマネージャー
pm = PasswordManager()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """セキュアパスワードマネージャー CLI"""
    pass

@cli.command()
@click.option('--username', '-u', prompt=True, help='ユーザー名')
def register(username: str):
    """新しいユーザーを登録"""
    click.echo(f"ユーザー '{username}' を登録します")

    master_password = getpass("マスターパスワード: ")
    if len(master_password) < 8:
        click.echo("エラー: マスターパスワードは8文字以上である必要があります", err=True)
        return

    confirm_password = getpass("マスターパスワード（確認）: ")
    if master_password != confirm_password:
        click.echo("エラー: パスワードが一致しません", err=True)
        return

    success = pm.create_user(username, master_password)
    if success:
        click.echo("✅ ユーザー登録が完了しました")
    else:
        click.echo("❌ ユーザー登録に失敗しました。ユーザー名が既に存在している可能性があります", err=True)

@cli.command()
@click.option('--username', '-u', prompt=True, help='ユーザー名')
def login(username: str):
    """ユーザーログイン"""
    master_password = getpass("マスターパスワード: ")

    success = pm.login(username, master_password)
    if success:
        click.echo("✅ ログインしました")
    else:
        click.echo("❌ ログインに失敗しました。ユーザー名またはパスワードが正しくありません", err=True)

@cli.command()
def logout():
    """ログアウト"""
    pm.logout()
    click.echo("✅ ログアウトしました")

@cli.command()
@click.option('--service', '-s', prompt=True, help='サービス名')
@click.option('--username', '-u', help='ユーザー名')
@click.option('--email', '-e', help='メールアドレス')
@click.option('--password', '-p', help='パスワード（空の場合は生成）')
@click.option('--url', help='URL')
@click.option('--notes', '-n', help='メモ')
@click.option('--generate', '-g', is_flag=True, help='パスワードを自動生成')
@click.option('--length', default=16, help='生成パスワードの長さ（デフォルト: 16）')
def add(service: str, username: Optional[str], email: Optional[str],
        password: Optional[str], url: Optional[str], notes: Optional[str],
        generate: bool, length: int):
    """パスワードエントリを追加"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    # パスワード処理
    if generate or not password:
        if generate:
            click.echo("パスワードを生成しています...")
            generated_password = pm.generate_password(length=length)
            password = generated_password
            click.echo(f"生成されたパスワード: {password}")
        else:
            password = getpass("パスワード: ")

    entry_id = pm.add_password(
        service_name=service,
        username=username,
        email=email,
        password=password,
        url=url,
        notes=notes
    )

    if entry_id:
        click.echo(f"✅ パスワードエントリが追加されました (ID: {entry_id})")
    else:
        click.echo("❌ パスワードエントリの追加に失敗しました", err=True)

@cli.command()
@click.option('--search', '-s', help='検索キーワード')
@click.option('--show-passwords', is_flag=True, help='パスワードを表示')
def list(search: Optional[str], show_passwords: bool):
    """パスワード一覧を表示"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    entries = pm.get_passwords(search)

    if not entries:
        if search:
            click.echo(f"検索キーワード '{search}' に一致するエントリが見つかりません")
        else:
            click.echo("パスワードエントリがありません")
        return

    # テーブル形式で表示
    headers = ["ID", "サービス", "ユーザー名", "メール"]
    if show_passwords:
        headers.append("パスワード")
    headers.extend(["URL", "作成日"])

    rows = []
    for entry in entries:
        row = [
            entry["id"],
            entry["service_name"],
            entry["username"] or "",
            entry["email"] or ""
        ]
        if show_passwords:
            row.append(entry["password"])
        row.extend([
            entry["url"] or "",
            entry["created_at"][:10] if entry["created_at"] else ""
        ])
        rows.append(row)

    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

@cli.command()
@click.argument('entry_id', type=int)
@click.option('--show-password', is_flag=True, help='パスワードを表示')
def get(entry_id: int, show_password: bool):
    """特定のパスワードエントリを表示"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    entry = pm.get_password(entry_id)
    if not entry:
        click.echo(f"❌ ID {entry_id} のエントリが見つかりません", err=True)
        return

    click.echo(f"ID: {entry['id']}")
    click.echo(f"サービス: {entry['service_name']}")
    click.echo(f"ユーザー名: {entry['username'] or 'N/A'}")
    click.echo(f"メール: {entry['email'] or 'N/A'}")

    if show_password:
        click.echo(f"パスワード: {entry['password']}")
    else:
        click.echo("パスワード: *** (--show-passwordで表示)")

    click.echo(f"URL: {entry['url'] or 'N/A'}")
    click.echo(f"メモ: {entry['notes'] or 'N/A'}")
    click.echo(f"作成日: {entry['created_at']}")
    click.echo(f"更新日: {entry['updated_at']}")

@cli.command()
@click.argument('entry_id', type=int)
@click.option('--service', help='サービス名')
@click.option('--username', help='ユーザー名')
@click.option('--email', help='メールアドレス')
@click.option('--password', help='パスワード')
@click.option('--url', help='URL')
@click.option('--notes', help='メモ')
@click.option('--generate-password', is_flag=True, help='新しいパスワードを生成')
@click.option('--length', default=16, help='生成パスワードの長さ')
def update(entry_id: int, service: Optional[str], username: Optional[str],
           email: Optional[str], password: Optional[str], url: Optional[str],
           notes: Optional[str], generate_password: bool, length: int):
    """パスワードエントリを更新"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    updates = {}

    if service is not None:
        updates['service_name'] = service
    if username is not None:
        updates['username'] = username
    if email is not None:
        updates['email'] = email
    if url is not None:
        updates['url'] = url
    if notes is not None:
        updates['notes'] = notes

    if generate_password:
        password = pm.generate_password(length=length)
        click.echo(f"新しいパスワードを生成しました: {password}")
        updates['password'] = password
    elif password is not None:
        updates['password'] = password

    if not updates:
        click.echo("❌ 更新するフィールドが指定されていません", err=True)
        return

    success = pm.update_password(entry_id, **updates)
    if success:
        click.echo(f"✅ パスワードエントリ {entry_id} が更新されました")
    else:
        click.echo(f"❌ パスワードエントリ {entry_id} の更新に失敗しました", err=True)

@cli.command()
@click.argument('entry_id', type=int)
@click.confirmation_option(prompt='このエントリを削除しますか？')
def delete(entry_id: int):
    """パスワードエントリを削除"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    success = pm.delete_password(entry_id)
    if success:
        click.echo(f"✅ パスワードエントリ {entry_id} が削除されました")
    else:
        click.echo(f"❌ パスワードエントリ {entry_id} の削除に失敗しました", err=True)

@cli.command()
@click.option('--length', '-l', default=16, help='パスワードの長さ（デフォルト: 16）')
@click.option('--no-uppercase', is_flag=True, help='大文字を除外')
@click.option('--no-lowercase', is_flag=True, help='小文字を除外')
@click.option('--no-numbers', is_flag=True, help='数字を除外')
@click.option('--no-special', is_flag=True, help='特殊文字を除外')
@click.option('--include-ambiguous', is_flag=True, help='紛らわしい文字を含める')
def generate(length: int, no_uppercase: bool, no_lowercase: bool,
             no_numbers: bool, no_special: bool, include_ambiguous: bool):
    """セキュアなパスワードを生成"""
    password = pm.generate_password(
        length=length,
        include_uppercase=not no_uppercase,
        include_lowercase=not no_lowercase,
        include_numbers=not no_numbers,
        include_special=not no_special,
        exclude_ambiguous=not include_ambiguous
    )

    if password:
        click.echo(f"生成されたパスワード: {password}")
    else:
        click.echo("❌ パスワード生成に失敗しました", err=True)

@cli.command()
@click.option('--output', '-o', help='出力ファイル名（JSONフォーマット）')
def export(output: Optional[str]):
    """パスワードデータをエクスポート"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    entries = pm.export_passwords()
    if entries is None:
        click.echo("❌ エクスポートに失敗しました", err=True)
        return

    if output:
        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2, default=str)
            click.echo(f"✅ {len(entries)}件のエントリを {output} にエクスポートしました")
        except Exception as e:
            click.echo(f"❌ ファイル書き込みエラー: {e}", err=True)
    else:
        click.echo(json.dumps(entries, ensure_ascii=False, indent=2, default=str))

@cli.command()
def stats():
    """統計情報を表示"""
    if not pm.is_logged_in():
        click.echo("❌ ログインが必要です", err=True)
        return

    stats = pm.get_stats()
    if "error" in stats:
        click.echo(f"❌ {stats['error']}", err=True)
        return

    click.echo(f"総エントリ数: {stats['total_entries']}")
    click.echo(f"サービス数: {len(set(stats['services']))}")
    click.echo(f"最終更新: {stats['last_updated']}")

if __name__ == '__main__':
    cli()
