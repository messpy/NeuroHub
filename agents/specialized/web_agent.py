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

    def execute(self, prompt: str) -> str:
        """統一インターフェース用のexecuteメソッド"""
        try:
            # プロンプトからURLを抽出または検索クエリとして処理
            import re

            # URL抽出
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, prompt)

            if urls:
                # URLがある場合は解析
                url = urls[0]
                question = re.sub(url_pattern, '', prompt).strip()
                if not question:
                    question = "このページの内容を要約してください。"

                result = self.answer_question(url, question)
                if isinstance(result, dict) and 'answer' in result:
                    return result['answer']
                else:
                    return str(result)
            else:
                # URLがない場合は検索として処理
                return self.search_web(prompt)

        except Exception as e:
            return f"❌ Web処理エラー: {e}"

    def search_web(self, query: str) -> str:
        """Web検索機能（改良版・リダイレクト対応）"""
        try:
            import httpx
            import urllib.parse

            # URL エンコード
            encoded_query = urllib.parse.quote_plus(query)

            # DuckDuckGoのHTMLページを直接使用（リダイレクト対応）
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {
                "User-Agent": DEFAULT_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            with httpx.Client(
                follow_redirects=True,
                timeout=self.timeout * 2,  # タイムアウト延長
                headers=headers
            ) as client:
                try:
                    response = client.get(search_url)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []

                    # DuckDuckGoの結果要素を検索
                    result_divs = soup.find_all('div', class_='result')
                    if not result_divs:
                        # 別の可能性を試す
                        result_divs = soup.find_all('div', class_='web-result')

                    for result in result_divs[:5]:
                        title_elem = result.find('a', class_='result__a') or result.find('h2')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')

                            snippet_elem = (
                                result.find('a', class_='result__snippet') or
                                result.find('span', class_='result__snippet') or
                                result.find('div', class_='snippet')
                            )
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                            if title:  # タイトルがある場合のみ追加
                                # URL要求チェック
                                if self._is_url_requested(query):
                                    results.append(f"• {title}\n  {snippet}\n  {link}")
                                else:
                                    results.append(f"• {title}\n  {snippet}")

                    if results:
                        if self._is_url_requested(query):
                            return f"🔍 検索結果: {query}\n\n" + "\n\n".join(results)
                        else:
                            # URL非表示の場合、内容をAIで解析
                            content_summary = "\n".join(results)
                            return self._analyze_content_with_ai(query, content_summary)
                    else:
                        # 検索結果が取得できない場合は簡易回答を提供
                        return self._provide_basic_answer(query)

                except httpx.HTTPStatusError as e:
                    return f"🔍 Web検索が利用できません。基本的な回答: {self._provide_basic_answer(query)}"

        except Exception as e:
            return f"🔍 Web検索エラーが発生しました。基本的な回答: {self._provide_basic_answer(query)}"

    def _is_url_requested(self, query: str) -> bool:
        """ユーザーがURLを求めているかを判定"""
        url_request_keywords = [
            "url教えて", "リンクを教えて", "サイトのアドレス", "ページのurl",
            "ウェブサイトのurl", "どこのサイト", "リンク先", "url", "link"
        ]

        query_lower = query.lower()
        for keyword in url_request_keywords:
            if keyword in query_lower:
                return True
        return False

    def _analyze_content_with_ai(self, query: str, content: str) -> str:
        """Web検索内容をAIで解析して回答"""
        try:
            # プロジェクトルートからLLMエージェントを呼び出し
            import sys
            import subprocess
            from pathlib import Path

            # AI解析用プロンプト作成
            analysis_prompt = f"""以下のWeb検索結果を参考に、「{query}」について詳しく説明してください。

検索結果:
{content}

要求:
- 検索結果の内容を整理し、要点をまとめて説明
- 正確で分かりやすい日本語で回答
- URLは含めず、内容のみに焦点を当てる
- ユーザーの質問に直接答える形式で"""

            # LLMエージェント呼び出し
            root_dir = Path(__file__).resolve().parents[2]
            cmd = f'cd {root_dir} && python agents/agent_llm.py "{analysis_prompt}"'

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'  # エンコーディングエラーを無視
            )

            if result.returncode == 0 and result.stdout:
                ai_response = result.stdout.strip()
                # プロバイダー情報などの不要部分を除去
                clean_response = self._clean_ai_response(ai_response)
                return f"📝 {query}について:\n\n{clean_response}"
            else:
                return f"📝 検索結果の概要: {content[:500]}..."

        except Exception as e:
            return f"📝 検索結果の概要: {content[:500]}..."

    def _clean_ai_response(self, response: str) -> str:
        """AI応答から不要な部分を除去"""
        lines = response.split('\n')
        cleaned_lines = []

        skip_patterns = [
            "="*60, "🔧 プロバイダー情報", "📡 Provider:", "🤖 Model:",
            "provider_", "model_", "Provider:", "Model:"
        ]

        for line in lines:
            skip = False
            for pattern in skip_patterns:
                if pattern in line:
                    skip = True
                    break
            if not skip and line.strip():
                cleaned_lines.append(line.strip())

        return '\n'.join(cleaned_lines)

    def _provide_basic_answer(self, query: str) -> str:
        """Web検索が失敗した場合の基本的な回答"""
        # 基本的な質問に対する回答を提供
        basic_answers = {
            "こんにちは": "「こんにちは」は日本語の挨拶です。漢字では「今日は」と書き、英語では「Hello」や「Good day」に相当します。",
            "何語": "言語に関するご質問ですね。具体的にどの言語についてお知りになりたいでしょうか？",
            "python": "Pythonは1991年にGuido van Rossumによって開発されたプログラミング言語です。シンプルで読みやすい構文が特徴で、AI開発、Web開発、データサイエンスなど幅広い分野で使用されています。"
        }

        query_lower = query.lower()
        for key, answer in basic_answers.items():
            if key in query_lower:
                return answer

        return f"申し訳ございませんが、「{query}」について詳細な情報を取得できませんでした。より具体的な質問をしていただけますか？"

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
