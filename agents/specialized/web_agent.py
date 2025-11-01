#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
web_agent.py - Web解析エージェント
- URLからHTML取得 → BeautifulSoupで要約 → LLMに投げて回答
- bs_coreの機能を統合
- git_agentと同様のインターフェース
"""

import argparse
import subprocess
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable
from urllib.parse import urljoin, urlparse
from datetime import datetime
import unicodedata

# HTTP client and BeautifulSoup
try:
    import httpx
    from bs4 import BeautifulSoup
    import yaml
except ImportError as e:
    print(f"[error] Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install httpx beautifulsoup4 pyyaml", file=sys.stderr)
    sys.exit(1)

# プロジェクトルート
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)

class WebAgent:
    """Web解析エージェント"""
    
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
    
    def fetch_html(self, url: str, ua: Optional[str] = None) -> str:
        """HTMLを取得"""
        headers = {"User-Agent": ua or DEFAULT_UA, "Accept": "text/html,application/xhtml+xml"}
        with httpx.Client(follow_redirects=True, headers=headers, timeout=self.timeout) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.text
    
    def absolutize_urls(self, base_url: str, rel_urls: Iterable[str]) -> List[str]:
        """相対URLを絶対URLに変換"""
        return [urljoin(base_url, rel) for rel in rel_urls]
    
    def extract_links(self, soup: BeautifulSoup, base_url: str, max_hits: int = 100) -> List[str]:
        """リンクを抽出"""
        rels = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href and not href.startswith(("javascript:", "mailto:", "tel:")):
                rels.append(href)
                if len(rels) >= max_hits:
                    break
        return self.absolutize_urls(base_url, rels)
    
    def extract_images(self, soup: BeautifulSoup, base_url: str, max_hits: int = 100) -> List[str]:
        """画像URLを抽出"""
        rels = []
        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            if src:
                rels.append(src)
                if len(rels) >= max_hits:
                    break
        return self.absolutize_urls(base_url, rels)
    
    def clean_text(self, text: str) -> str:
        """テキストをクリーニング"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """メインコンテンツを抽出"""
        # 不要なタグを削除
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        
        # メインコンテンツを検索
        main_selectors = ["main", "article", ".content", "#content", ".main"]
        for selector in main_selectors:
            main = soup.select_one(selector)
            if main:
                return self.clean_text(main.get_text())
        
        # フォールバック: body全体
        body = soup.find("body")
        if body:
            return self.clean_text(body.get_text())
        
        return self.clean_text(soup.get_text())
    
    def analyze_page(self, url: str) -> Dict[str, Any]:
        """ページを解析してメタデータと内容を返す"""
        try:
            html = self.fetch_html(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # メタデータ抽出
            title = soup.find("title")
            title_text = title.get_text().strip() if title else "No title"
            
            description = soup.find("meta", attrs={"name": "description"})
            description_text = description.get("content", "").strip() if description else ""
            
            canonical = soup.find("link", attrs={"rel": "canonical"})
            canonical_url = canonical.get("href", url) if canonical else url
            
            # コンテンツ抽出
            main_content = self.extract_main_content(soup)
            sample_text = main_content[:500] + "..." if len(main_content) > 500 else main_content
            
            # リンクと画像
            links = self.extract_links(soup, url, 10)
            images = self.extract_images(soup, url, 5)
            
            return {
                "url": url,
                "title": title_text,
                "description": description_text,
                "canonical": canonical_url,
                "main_content": main_content,
                "sample_text": sample_text,
                "links": links,
                "images": images,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
    
    def run_llm_query(self, prompt: str, model: Optional[str] = None, provider: Optional[str] = None) -> str:
        """LLMでクエリを実行"""
        cmd = ["python", str(ROOT / "services/llm/llm_cli.py"), "--smart", prompt]
        if model:
            cmd.extend(["--model", model])
        if provider:
            cmd.extend(["--provider", provider])
        try:
            result = subprocess.check_output(cmd, text=True, cwd=ROOT)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return f"[LLM error] {e.output.strip() if e.output else e}"
    
    def answer_question(self, url: str, question: str, model: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """URLに対する質問に答える"""
        page_data = self.analyze_page(url)
        
        if "error" in page_data:
            return {
                "url": url,
                "question": question,
                "error": page_data["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        # LLMプロンプト構築
        prompt = f"""あなたはWebページの要約と質問回答を行うアシスタントです。
次のページのメタ情報と本文サマリを読み、ユーザーの質問に答えてください。
必要なら根拠となる抜粋も示してください。箇条書きは簡潔に。

[ページ情報]
title: {page_data['title']}
description: {page_data['description']}
canonical: {page_data['canonical']}
sample_text: {page_data['sample_text']}

[質問]
{question}
"""
        
        answer = self.run_llm_query(prompt, model, provider)
        
        return {
            "url": url,
            "question": question,
            "answer": answer,
            "page_title": page_data['title'],
            "page_description": page_data['description'],
            "timestamp": datetime.now().isoformat()
        }

def make_safe_filename(text: str, max_len: int = 50) -> str:
    """安全なファイル名を生成"""
    # Unicode正規化
    text = unicodedata.normalize('NFKC', text)
    # 不正文字を除去
    text = re.sub(r'[^\w\s\-_.]', '', text)
    # スペースをアンダースコアに
    text = re.sub(r'\s+', '_', text)
    # 長さ制限
    if len(text) > max_len:
        text = text[:max_len]
    return text.strip('_')

def main():
    parser = argparse.ArgumentParser(description="Web解析エージェント")
    parser.add_argument("url", help="解析するURL")
    parser.add_argument("question", nargs="?", help="質問（位置引数、非推奨）")
    parser.add_argument("--prompt", help="質問文")
    parser.add_argument("--model", help="LLMモデル指定")
    parser.add_argument("--provider", help="LLMプロバイダー指定")
    parser.add_argument("--output", action="store_true", help="結果をファイルに保存")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTPタイムアウト（秒）")
    
    args = parser.parse_args()
    
    # 質問の処理
    question = args.prompt or args.question
    if not question:
        question = "このページの内容を3行で要約してください。"
    
    # Web解析実行
    agent = WebAgent(timeout=args.timeout)
    result = agent.answer_question(args.url, question, args.model, args.provider)
    
    # 出力
    if args.output:
        # ファイル名生成
        if "page_title" in result:
            title_part = make_safe_filename(result["page_title"])
        else:
            title_part = "web_analysis"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title_part}_{timestamp}.yaml"
        
        # 重複チェック
        counter = 1
        original_filename = filename
        while Path(filename).exists():
            name_part = original_filename.replace('.yaml', '')
            filename = f"{name_part}_{counter:03d}.yaml"
            counter += 1
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"結果を保存しました: {filename}")
    else:
        yaml.dump(result, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()