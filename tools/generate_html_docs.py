#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/generate_html_docs.py

Markdownドキュメントを HTML に変換するツール
"""

import os
import re
from pathlib import Path
from typing import List, Dict
import markdown
from datetime import datetime


class HTMLDocGenerator:
    """HTML ドキュメント生成クラス"""
    
    def __init__(self, docs_dir: str = "docs/jp", output_dir: str = "docs/html"):
        """
        初期化
        
        Args:
            docs_dir: ソースMarkdownディレクトリ
            output_dir: 出力HTMLディレクトリ
        """
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Markdownパーサー設定
        self.md = markdown.Markdown(
            extensions=[
                'extra',
                'codehilite',
                'toc',
                'tables',
                'fenced_code'
            ]
        )
    
    def generate_all(self):
        """全Markdownファイルを HTML に変換"""
        print("🚀 HTML ドキュメント生成開始...")
        
        # トップページ生成
        self._generate_index()
        
        # 全Markdownファイル変換
        md_files = list(self.docs_dir.rglob("*.md"))
        print(f"📄 {len(md_files)}個のMarkdownファイルを検出")
        
        for md_file in md_files:
            self._convert_md_to_html(md_file)
        
        # CSS生成
        self._generate_css()
        
        # JavaScript生成
        self._generate_js()
        
        print(f"✅ HTML生成完了: {self.output_dir}")
    
    def _convert_md_to_html(self, md_path: Path):
        """
        Markdownファイルを HTML に変換
        
        Args:
            md_path: Markdownファイルパス
        """
        # 相対パス計算
        rel_path = md_path.relative_to(self.docs_dir)
        html_path = self.output_dir / rel_path.with_suffix('.html')
        html_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Markdown読み込み
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # HTML変換
        html_content = self.md.convert(md_content)
        
        # タイトル抽出
        title = self._extract_title(md_content)
        
        # HTMLテンプレート適用
        full_html = self._apply_template(html_content, title, rel_path)
        
        # HTML保存
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"  ✓ {md_path.name} → {html_path.name}")
    
    def _extract_title(self, md_content: str) -> str:
        """Markdownからタイトル抽出"""
        match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        return match.group(1) if match else "NeuroHub Documentation"
    
    def _apply_template(self, content: str, title: str, rel_path: Path) -> str:
        """
        HTMLテンプレート適用
        
        Args:
            content: 本文HTML
            title: ページタイトル
            rel_path: 相対パス（ナビゲーション用）
        """
        # ルートからの相対パス計算
        depth = len(rel_path.parts) - 1
        root_path = "../" * depth if depth > 0 else "./"
        
        # ナビゲーション生成
        nav_html = self._generate_nav(rel_path)
        
        # テンプレート
        template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - NeuroHub Documentation</title>
    <link rel="stylesheet" href="{root_path}style.css">
</head>
<body>
    <div class="container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>📚 NeuroHub Docs</h2>
            </div>
            <nav class="sidebar-nav">
                {nav_html}
            </nav>
        </aside>
        
        <main class="content">
            <div class="breadcrumb">
                {self._generate_breadcrumb(rel_path)}
            </div>
            <article>
                {content}
            </article>
            <footer class="page-footer">
                <p>最終更新: {datetime.now().strftime("%Y年%m月%d日")}</p>
                <p>© 2025 NeuroHub Project</p>
            </footer>
        </main>
    </div>
    <script src="{root_path}script.js"></script>
</body>
</html>"""
        return template
    
    def _generate_nav(self, current_path: Path) -> str:
        """ナビゲーションメニュー生成"""
        nav_items = {
            "🏠 トップ": "index.html",
            "📖 プロジェクト概要": "OVERVIEW.html",
            "🏗️ アーキテクチャ": "ARCHITECTURE_DESIGN.html",
            "🗄️ データベース設計": "DATABASE_DESIGN.html",
            "📋 タスク管理": "TASK_MANAGEMENT.html",
            "🤖 エージェント": {
                "LLM": "agents/llm/README.html",
                "Git": "agents/git/README.html",
                "MCP": "agents/mcp/README.html",
                "Discord": "agents/discord/README.html",
                "Config": "agents/config/README.html",
                "Command": "agents/command/README.html"
            }
        }
        
        html = "<ul>"
        for label, link in nav_items.items():
            if isinstance(link, dict):
                # サブメニュー
                html += f'<li class="nav-category">{label}<ul>'
                for sub_label, sub_link in link.items():
                    html += f'<li><a href="{sub_link}">{sub_label}</a></li>'
                html += '</ul></li>'
            else:
                html += f'<li><a href="{link}">{label}</a></li>'
        html += "</ul>"
        
        return html
    
    def _generate_breadcrumb(self, rel_path: Path) -> str:
        """パンくずリスト生成"""
        parts = rel_path.parts[:-1]  # ファイル名除く
        breadcrumb = '<a href="index.html">ホーム</a>'
        
        path_accumulator = ""
        for part in parts:
            path_accumulator += part + "/"
            breadcrumb += f' &gt; <a href="{path_accumulator}README.html">{part}</a>'
        
        return breadcrumb
    
    def _generate_index(self):
        """トップページ生成"""
        index_content = """
# NeuroHub ドキュメント

## 📚 ドキュメント一覧

### 総合ドキュメント
- [プロジェクト概要](OVERVIEW.html) - NeuroHubの目的、アーキテクチャ、主要機能
- [アーキテクチャ設計](ARCHITECTURE_DESIGN.html) - システム全体の設計思想
- [データベース設計](DATABASE_DESIGN.html) - DB構造、テーブル定義
- [タスク管理](TASK_MANAGEMENT.html) - 課題一覧、進捗状況

### エージェント別設計書
- [LLMエージェント](agents/llm/README.html) - 複数LLM統合管理
- [Gitエージェント](agents/git/README.html) - Git操作自動化
- [MCPエージェント](agents/mcp/README.html) - 自動プロジェクト生成
- [Discordエージェント](agents/discord/README.html) - Discord Bot機能

---

*このドキュメントはMarkdownから自動生成されています*
"""
        
        index_html = self.md.convert(index_content)
        full_html = self._apply_template(
            index_html,
            "NeuroHub Documentation",
            Path("index.html")
        )
        
        with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print("  ✓ index.html 生成")
    
    def _generate_css(self):
        """CSS生成"""
        css = """/* NeuroHub Documentation CSS */

:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --bg-color: #ecf0f1;
    --sidebar-bg: #34495e;
    --text-color: #2c3e50;
    --border-color: #bdc3c7;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
}

.container {
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    width: 280px;
    background-color: var(--sidebar-bg);
    color: white;
    padding: 20px;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
}

.sidebar-header h2 {
    margin-bottom: 20px;
    font-size: 1.5rem;
}

.sidebar-nav ul {
    list-style: none;
}

.sidebar-nav li {
    margin: 10px 0;
}

.sidebar-nav a {
    color: #ecf0f1;
    text-decoration: none;
    transition: color 0.3s;
}

.sidebar-nav a:hover {
    color: var(--secondary-color);
}

.nav-category {
    font-weight: bold;
    margin-top: 15px;
}

.nav-category ul {
    margin-left: 15px;
    font-weight: normal;
}

/* Main Content */
.content {
    margin-left: 280px;
    padding: 40px;
    max-width: 1200px;
    background-color: white;
    min-height: 100vh;
}

.breadcrumb {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-bottom: 20px;
}

.breadcrumb a {
    color: var(--secondary-color);
    text-decoration: none;
}

article {
    margin-bottom: 40px;
}

article h1 {
    color: var(--primary-color);
    border-bottom: 3px solid var(--secondary-color);
    padding-bottom: 10px;
    margin-bottom: 20px;
}

article h2 {
    color: var(--primary-color);
    margin-top: 30px;
    margin-bottom: 15px;
    border-left: 4px solid var(--secondary-color);
    padding-left: 10px;
}

article h3 {
    color: var(--primary-color);
    margin-top: 20px;
    margin-bottom: 10px;
}

article p {
    margin-bottom: 15px;
}

article code {
    background-color: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

article pre {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    margin-bottom: 20px;
}

article pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}

article table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

article th, article td {
    border: 1px solid var(--border-color);
    padding: 10px;
    text-align: left;
}

article th {
    background-color: var(--primary-color);
    color: white;
}

article tr:nth-child(even) {
    background-color: #f9f9f9;
}

article ul, article ol {
    margin-left: 30px;
    margin-bottom: 15px;
}

article a {
    color: var(--secondary-color);
    text-decoration: none;
}

article a:hover {
    text-decoration: underline;
}

.page-footer {
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
    text-align: center;
    color: #7f8c8d;
    font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
    .sidebar {
        width: 100%;
        position: relative;
        height: auto;
    }
    
    .content {
        margin-left: 0;
        padding: 20px;
    }
}
"""
        
        with open(self.output_dir / "style.css", 'w', encoding='utf-8') as f:
            f.write(css)
        
        print("  ✓ style.css 生成")
    
    def _generate_js(self):
        """JavaScript生成"""
        js = """// NeuroHub Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // コードブロックにコピーボタン追加
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(function(block) {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.addEventListener('click', function() {
            navigator.clipboard.writeText(block.textContent);
            button.textContent = 'Copied!';
            setTimeout(function() {
                button.textContent = 'Copy';
            }, 2000);
        });
        block.parentElement.appendChild(button);
    });
    
    // 目次ハイライト
    const headers = document.querySelectorAll('h2, h3');
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    
    window.addEventListener('scroll', function() {
        let current = '';
        headers.forEach(function(header) {
            const sectionTop = header.offsetTop;
            if (pageYOffset >= sectionTop - 60) {
                current = header.getAttribute('id');
            }
        });
        
        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });
});
"""
        
        with open(self.output_dir / "script.js", 'w', encoding='utf-8') as f:
            f.write(js)
        
        print("  ✓ script.js 生成")


# メイン実行
if __name__ == "__main__":
    generator = HTMLDocGenerator()
    generator.generate_all()
    print("\n🎉 完了！docs/html/index.html を開いてください")
