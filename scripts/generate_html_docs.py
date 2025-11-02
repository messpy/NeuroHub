#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML Documentation Generator - Markdown設計書をHTMLに変換

NeuroHubの全Markdown設計書をHTMLに変換し、docs/html/配下に配置
"""

import os
import sys
from pathlib import Path
import re

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def md_to_html(md_content: str, title: str = "NeuroHub Documentation") -> str:
    """
    Markdownコンテンツを基本的なHTMLに変換

    Args:
        md_content: Markdownコンテンツ
        title: HTMLページタイトル

    Returns:
        HTMLコンテンツ
    """
    # 基本的なMarkdown→HTML変換
    html_body = md_content

    # コードブロック変換（```で囲まれた部分）
    html_body = re.sub(
        r'```(\w+)?\n(.*?)```',
        r'<pre><code class="language-\1">\2</code></pre>',
        html_body,
        flags=re.DOTALL
    )

    # ヘッダー変換（# → <h1>, ## → <h2>, etc.）
    html_body = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

    # リスト変換
    html_body = re.sub(r'^\- (.*?)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)

    # 強調変換
    html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_body)
    html_body = re.sub(r'`(.*?)`', r'<code>\1</code>', html_body)

    # リンク変換
    html_body = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html_body)

    # 段落変換（2行以上の改行を<p>で囲む）
    paragraphs = html_body.split('\n\n')
    html_body = '\n'.join(
        f'<p>{p.strip()}</p>' if p.strip() and not p.strip().startswith('<') else p
        for p in paragraphs
    )

    # HTML全体構造
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #546e7a;
            margin-top: 20px;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre code {{
            background: transparent;
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #777;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
        <div class="footer">
            <p>Generated from Markdown | NeuroHub Documentation</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def generate_html_docs():
    """全Markdown設計書をHTMLに変換"""
    docs_dir = project_root / "docs"
    html_dir = docs_dir / "html"
    html_dir.mkdir(exist_ok=True)

    # 変換対象のMarkdownファイル
    md_files = [
        docs_dir / "ARCHITECTURE_DESIGN.md",
        docs_dir / "DATABASE_DESIGN.md",
        docs_dir / "FILE_DESIGN.md",
        docs_dir / "INTERFACE_DESIGN.md",
        docs_dir / "README.md",
        docs_dir / "PROJECT_OVERVIEW.md",
        docs_dir / "TASK_MANAGEMENT.md",
        docs_dir / "TESTING.md",
        docs_dir / "DEPENDENCIES.md",
        docs_dir / "DOCKER_SETUP.md",
    ]

    # 日本語版
    jp_files = [
        docs_dir / "jp" / "ARCHITECTURE_DESIGN.md",
        docs_dir / "jp" / "DATABASE_DESIGN.md",
    ]

    converted_count = 0

    print("🔧 Markdown → HTML 変換開始")

    # 英語版変換
    for md_file in md_files:
        if md_file.exists():
            print(f"  📄 {md_file.name}...", end=" ")
            try:
                md_content = md_file.read_text(encoding="utf-8")
                html_content = md_to_html(md_content, title=f"NeuroHub - {md_file.stem}")

                html_file = html_dir / f"{md_file.stem}.html"
                html_file.write_text(html_content, encoding="utf-8")

                print(f"✅ {html_file.name}")
                converted_count += 1
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"  ⚠️  {md_file.name} not found")

    # 日本語版変換
    jp_html_dir = html_dir / "jp"
    jp_html_dir.mkdir(exist_ok=True)

    for md_file in jp_files:
        if md_file.exists():
            print(f"  📄 jp/{md_file.name}...", end=" ")
            try:
                md_content = md_file.read_text(encoding="utf-8")
                html_content = md_to_html(md_content, title=f"NeuroHub - {md_file.stem} (日本語)")

                html_file = jp_html_dir / f"{md_file.stem}.html"
                html_file.write_text(html_content, encoding="utf-8")

                print(f"✅ {html_file.name}")
                converted_count += 1
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"  ⚠️  jp/{md_file.name} not found")

    print(f"\n✅ 変換完了: {converted_count}ファイル")
    print(f"📂 出力先: {html_dir}")

    # index.html作成
    create_index_html(html_dir, md_files, jp_files)


def create_index_html(html_dir: Path, en_files: list, jp_files: list):
    """インデックスHTML作成"""
    index_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroHub Documentation Index</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1000px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
        }
        a {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
            padding: 8px 12px;
            display: inline-block;
            border-radius: 5px;
            transition: background 0.3s;
        }
        a:hover {
            background: #ecf0f1;
        }
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #777;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 NeuroHub Documentation</h1>
        <p>Welcome to NeuroHub documentation. Select a document to view:</p>

        <h2>🇬🇧 English Documentation</h2>
        <ul>
"""

    for md_file in en_files:
        if md_file.exists():
            html_name = f"{md_file.stem}.html"
            index_content += f'            <li>📄 <a href="{html_name}">{md_file.stem}</a></li>\n'

    index_content += """
        </ul>

        <h2>🇯🇵 日本語ドキュメント</h2>
        <ul>
"""

    for md_file in jp_files:
        if md_file.exists():
            html_name = f"jp/{md_file.stem}.html"
            index_content += f'            <li>📄 <a href="{html_name}">{md_file.stem}</a></li>\n'

    index_content += """
        </ul>

        <div class="footer">
            <p>Generated: 2025-11-02 | NeuroHub Project</p>
        </div>
    </div>
</body>
</html>
"""

    index_file = html_dir / "index.html"
    index_file.write_text(index_content, encoding="utf-8")
    print(f"📄 index.html created: {index_file}")


if __name__ == "__main__":
    generate_html_docs()
