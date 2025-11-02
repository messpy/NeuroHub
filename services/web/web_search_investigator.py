#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web検索・調査システム
単語検索、サイト解析、情報抽出を統合したシステム
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import quote_plus, urljoin, urlparse
import re

# BeautifulSoup関連
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ BeautifulSoupが見つかりません。pip install beautifulsoup4 lxml でインストールしてください。")

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager


@dataclass
class SearchResult:
    """検索結果データクラス"""
    query: str
    title: str
    url: str
    snippet: str
    domain: str
    search_engine: str
    rank: int
    timestamp: str


@dataclass
class WebPageInfo:
    """Webページ情報データクラス"""
    url: str
    title: str
    content: str
    headings: List[str]
    links: List[str]
    images: List[str]
    meta_description: str
    keywords: List[str]
    language: str
    content_length: int
    status_code: int
    load_time: float
    timestamp: str


@dataclass
class TermDefinition:
    """用語定義データクラス"""
    term: str
    definition: str
    source: str
    url: str
    category: str
    examples: List[str]
    related_terms: List[str]
    confidence: float
    timestamp: str


class WebSearchInvestigator:
    """Web検索・調査クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session = requests.Session()

        # ユーザーエージェント設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 検索エンジン設定
        self.search_engines = {
            'google': 'https://www.google.com/search?q={}',
            'bing': 'https://www.bing.com/search?q={}',
            'duckduckgo': 'https://duckduckgo.com/?q={}'
        }

        # 専門サイト設定
        self.specialized_sites = {
            'python': [
                'https://docs.python.org/3/search.html?q={}',
                'https://stackoverflow.com/search?q=python+{}',
                'https://pypi.org/search/?q={}'
            ],
            'programming': [
                'https://stackoverflow.com/search?q={}',
                'https://github.com/search?q={}',
                'https://developer.mozilla.org/en-US/search?q={}'
            ],
            'general': [
                'https://en.wikipedia.org/wiki/Special:Search?search={}',
                'https://ja.wikipedia.org/wiki/Special:Search?search={}'
            ]
        }

        self._create_tables()

    def _create_tables(self):
        """Web検索用テーブル作成"""
        # 検索結果テーブル
        search_results_sql = """
        CREATE TABLE IF NOT EXISTS web_search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            title TEXT,
            url TEXT,
            snippet TEXT,
            domain TEXT,
            search_engine TEXT,
            rank INTEGER,
            relevance_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Webページ情報テーブル
        web_pages_sql = """
        CREATE TABLE IF NOT EXISTS web_page_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            content TEXT,
            headings TEXT,
            links TEXT,
            images TEXT,
            meta_description TEXT,
            keywords TEXT,
            language TEXT,
            content_length INTEGER,
            status_code INTEGER,
            load_time REAL,
            last_crawled DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 用語定義テーブル
        term_definitions_sql = """
        CREATE TABLE IF NOT EXISTS term_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            definition TEXT,
            source TEXT,
            url TEXT,
            category TEXT,
            examples TEXT,
            related_terms TEXT,
            confidence REAL DEFAULT 0.8,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 検索履歴テーブル
        search_history_sql = """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_count INTEGER,
            search_type TEXT,
            success BOOLEAN DEFAULT TRUE,
            execution_time REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [search_results_sql, web_pages_sql, term_definitions_sql, search_history_sql]:
            self.db_manager._execute_sql(sql)

    def search_term(self, term: str, search_type: str = 'general', max_results: int = 10) -> dict:
        """用語検索（統合）"""
        start_time = time.time()

        try:
            print(f"🔍 '{term}' を検索中...")

            # まず既存の定義をチェック
            existing_definition = self._get_cached_definition(term)
            if existing_definition:
                print(f"💾 キャッシュから定義を取得")
                return {
                    "success": True,
                    "term": term,
                    "definition": existing_definition,
                    "source": "cache",
                    "search_time": time.time() - start_time
                }

            # Web検索実行
            search_results = self._perform_web_search(term, search_type, max_results)

            if not search_results:
                return {
                    "success": False,
                    "error": "検索結果が見つかりませんでした",
                    "term": term
                }

            # 上位結果の詳細取得
            detailed_results = []
            for result in search_results[:5]:  # 上位5件を詳細解析
                page_info = self._analyze_webpage(result.url)
                if page_info:
                    detailed_results.append({
                        "search_result": result,
                        "page_info": page_info
                    })

            # 定義抽出
            definition = self._extract_term_definition(term, detailed_results)

            # 結果をデータベースに保存
            if definition:
                self._save_term_definition(definition)

            # 検索履歴保存
            self._save_search_history(term, len(search_results), search_type, True, time.time() - start_time)

            return {
                "success": True,
                "term": term,
                "definition": definition,
                "search_results": [asdict(r) for r in search_results],
                "detailed_results": detailed_results,
                "search_time": time.time() - start_time
            }

        except Exception as e:
            self._save_search_history(term, 0, search_type, False, time.time() - start_time)
            return {
                "success": False,
                "error": str(e),
                "term": term,
                "search_time": time.time() - start_time
            }

    def _perform_web_search(self, query: str, search_type: str, max_results: int) -> List[SearchResult]:
        """Web検索実行"""
        results = []

        try:
            if search_type in self.specialized_sites:
                # 専門サイト検索
                sites = self.specialized_sites[search_type]
                for i, site_template in enumerate(sites[:3]):  # 最大3サイト
                    site_results = self._search_specific_site(query, site_template, f"specialized_{i}")
                    results.extend(site_results)

            # 一般検索エンジン検索
            if len(results) < max_results:
                google_results = self._search_google(query, max_results - len(results))
                results.extend(google_results)

            # 結果をデータベースに保存
            for result in results:
                self._save_search_result(result)

            return results[:max_results]

        except Exception as e:
            print(f"❌ 検索エラー: {e}")
            return []

    def _search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Google検索（簡易実装）"""
        results = []

        try:
            # Google検索URL構築
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            if not HAS_BS4:
                # BeautifulSoupがない場合の簡易実装
                return self._simple_text_search(response.text, query)

            soup = BeautifulSoup(response.content, 'html.parser')

            # Google検索結果の解析
            search_items = soup.find_all('div', class_='g')

            for i, item in enumerate(search_items[:max_results]):
                try:
                    # タイトル抽出
                    title_elem = item.find('h3')
                    title = title_elem.get_text() if title_elem else "タイトルなし"

                    # URL抽出
                    link_elem = item.find('a')
                    url = link_elem.get('href') if link_elem else ""

                    # スニペット抽出
                    snippet_elem = item.find('span', class_=['aCOpRe', 'hgKElc'])
                    if not snippet_elem:
                        snippet_elem = item.find('div', class_='VwiC3b')
                    snippet = snippet_elem.get_text() if snippet_elem else ""

                    # ドメイン抽出
                    domain = urlparse(url).netloc if url else ""

                    result = SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain=domain,
                        search_engine="google",
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

                except Exception as e:
                    print(f"⚠️ 検索結果解析エラー: {e}")
                    continue

            return results

        except Exception as e:
            print(f"❌ Google検索エラー: {e}")
            return []

    def _search_specific_site(self, query: str, site_template: str, engine_name: str) -> List[SearchResult]:
        """特定サイト検索"""
        results = []

        try:
            search_url = site_template.format(quote_plus(query))
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            if not HAS_BS4:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(search_url).netloc

            # サイト別の解析ロジック
            if 'stackoverflow.com' in domain:
                results = self._parse_stackoverflow_results(soup, query, engine_name)
            elif 'wikipedia.org' in domain:
                results = self._parse_wikipedia_results(soup, query, engine_name)
            elif 'docs.python.org' in domain:
                results = self._parse_python_docs_results(soup, query, engine_name)
            elif 'github.com' in domain:
                results = self._parse_github_results(soup, query, engine_name)

            return results

        except Exception as e:
            print(f"❌ サイト検索エラー ({engine_name}): {e}")
            return []

    def _parse_stackoverflow_results(self, soup: BeautifulSoup, query: str, engine: str) -> List[SearchResult]:
        """StackOverflow結果解析"""
        results = []

        try:
            questions = soup.find_all('div', class_='question-summary')

            for i, question in enumerate(questions[:5]):
                try:
                    title_elem = question.find('h3').find('a')
                    title = title_elem.get_text().strip() if title_elem else "質問"
                    url = urljoin('https://stackoverflow.com', title_elem.get('href')) if title_elem else ""

                    excerpt_elem = question.find('div', class_='excerpt')
                    snippet = excerpt_elem.get_text().strip() if excerpt_elem else ""

                    result = SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain="stackoverflow.com",
                        search_engine=engine,
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

                except Exception as e:
                    continue

            return results

        except Exception as e:
            return []

    def _parse_wikipedia_results(self, soup: BeautifulSoup, query: str, engine: str) -> List[SearchResult]:
        """Wikipedia結果解析"""
        results = []

        try:
            search_results = soup.find_all('div', class_='mw-search-result-heading')

            for i, result_div in enumerate(search_results[:5]):
                try:
                    link_elem = result_div.find('a')
                    title = link_elem.get_text().strip() if link_elem else "記事"
                    url = urljoin('https://ja.wikipedia.org', link_elem.get('href')) if link_elem else ""

                    # スニペット取得
                    snippet_elem = result_div.find_next('div', class_='searchresult')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                    result = SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain="wikipedia.org",
                        search_engine=engine,
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

                except Exception as e:
                    continue

            return results

        except Exception as e:
            return []

    def _parse_python_docs_results(self, soup: BeautifulSoup, query: str, engine: str) -> List[SearchResult]:
        """Python公式ドキュメント結果解析"""
        results = []

        try:
            search_results = soup.find_all('li', class_='search-result')

            for i, result_li in enumerate(search_results[:5]):
                try:
                    link_elem = result_li.find('a')
                    title = link_elem.get_text().strip() if link_elem else "ドキュメント"
                    url = urljoin('https://docs.python.org', link_elem.get('href')) if link_elem else ""

                    snippet_elem = result_li.find('p')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                    result = SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain="docs.python.org",
                        search_engine=engine,
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

                except Exception as e:
                    continue

            return results

        except Exception as e:
            return []

    def _parse_github_results(self, soup: BeautifulSoup, query: str, engine: str) -> List[SearchResult]:
        """GitHub結果解析"""
        results = []

        try:
            repo_items = soup.find_all('div', class_='Box-row')

            for i, item in enumerate(repo_items[:5]):
                try:
                    link_elem = item.find('a', class_='v-align-middle')
                    title = link_elem.get_text().strip() if link_elem else "リポジトリ"
                    url = urljoin('https://github.com', link_elem.get('href')) if link_elem else ""

                    desc_elem = item.find('p', class_='mb-1')
                    snippet = desc_elem.get_text().strip() if desc_elem else ""

                    result = SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        domain="github.com",
                        search_engine=engine,
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

                except Exception as e:
                    continue

            return results

        except Exception as e:
            return []

    def _simple_text_search(self, html_content: str, query: str) -> List[SearchResult]:
        """BeautifulSoupなしの簡易検索"""
        results = []

        try:
            # 簡易的なリンク抽出
            link_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(link_pattern, html_content, re.IGNORECASE)

            for i, (url, title) in enumerate(matches[:5]):
                if query.lower() in title.lower():
                    result = SearchResult(
                        query=query,
                        title=title.strip(),
                        url=url,
                        snippet=f"{query}に関連する結果",
                        domain=urlparse(url).netloc if url.startswith('http') else "unknown",
                        search_engine="simple_text",
                        rank=i + 1,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)

            return results

        except Exception as e:
            return []

    def _analyze_webpage(self, url: str) -> Optional[WebPageInfo]:
        """Webページ詳細解析"""
        start_time = time.time()

        try:
            # 既存の解析結果をチェック
            cached_info = self._get_cached_page_info(url)
            if cached_info:
                return cached_info

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            load_time = time.time() - start_time

            if not HAS_BS4:
                # BeautifulSoupなしの簡易解析
                return self._simple_page_analysis(url, response.text, response.status_code, load_time)

            soup = BeautifulSoup(response.content, 'html.parser')

            # 基本情報抽出
            title = soup.find('title').get_text().strip() if soup.find('title') else url

            # メタ情報
            meta_desc = ""
            meta_elem = soup.find('meta', attrs={'name': 'description'})
            if meta_elem:
                meta_desc = meta_elem.get('content', '')

            # 見出し抽出
            headings = []
            for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = h_tag.get_text().strip()
                if heading_text:
                    headings.append(heading_text)

            # リンク抽出
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and href.startswith('http'):
                    links.append(href)

            # 画像抽出
            images = []
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src:
                    if src.startswith('http'):
                        images.append(src)
                    else:
                        images.append(urljoin(url, src))

            # コンテンツ抽出
            content = ""
            main_content = soup.find('main') or soup.find('article') or soup.find('div', id='content')
            if main_content:
                content = main_content.get_text().strip()
            else:
                # フォールバック: body全体
                body = soup.find('body')
                if body:
                    content = body.get_text().strip()

            # キーワード抽出（簡易）
            keywords = self._extract_keywords(content)

            # 言語検出（簡易）
            language = self._detect_language(content)

            page_info = WebPageInfo(
                url=url,
                title=title,
                content=content[:5000],  # 最初の5000文字
                headings=headings[:20],   # 最初の20個の見出し
                links=links[:50],         # 最初の50個のリンク
                images=images[:20],       # 最初の20個の画像
                meta_description=meta_desc,
                keywords=keywords,
                language=language,
                content_length=len(content),
                status_code=response.status_code,
                load_time=load_time,
                timestamp=datetime.now().isoformat()
            )

            # データベースに保存
            self._save_page_info(page_info)

            return page_info

        except Exception as e:
            print(f"❌ ページ解析エラー ({url}): {e}")
            return None

    def _simple_page_analysis(self, url: str, content: str, status_code: int, load_time: float) -> WebPageInfo:
        """BeautifulSoupなしの簡易ページ解析"""
        # タイトル抽出
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else url

        # 簡易コンテンツ抽出（HTMLタグ除去）
        text_content = re.sub(r'<[^>]+>', ' ', content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        return WebPageInfo(
            url=url,
            title=title,
            content=text_content[:2000],
            headings=[],
            links=[],
            images=[],
            meta_description="",
            keywords=[],
            language="unknown",
            content_length=len(text_content),
            status_code=status_code,
            load_time=load_time,
            timestamp=datetime.now().isoformat()
        )

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（簡易）"""
        if not content:
            return []

        # 単語分割（簡易）
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

        # 頻出単語除外
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }

        # 単語頻度計算
        word_count = {}
        for word in words:
            if word not in stop_words and len(word) >= 3:
                word_count[word] = word_count.get(word, 0) + 1

        # 上位キーワード取得
        keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in keywords[:10]]

    def _detect_language(self, content: str) -> str:
        """言語検出（簡易）"""
        if not content:
            return "unknown"

        # 日本語文字の検出
        japanese_chars = re.findall(r'[ひらがなカタカナ漢字]', content)
        if len(japanese_chars) > 50:
            return "ja"

        # 英語の簡易判定
        english_words = re.findall(r'\b[a-zA-Z]+\b', content)
        if len(english_words) > 100:
            return "en"

        return "unknown"

    def _extract_term_definition(self, term: str, detailed_results: List[dict]) -> Optional[TermDefinition]:
        """用語定義抽出"""
        try:
            # 最も関連性の高い結果から定義を抽出
            best_definition = None
            highest_confidence = 0.0

            for result_data in detailed_results:
                page_info = result_data['page_info']
                search_result = result_data['search_result']

                # コンテンツから定義らしき部分を抽出
                definition_text = self._find_definition_in_content(term, page_info.content)

                if definition_text:
                    confidence = self._calculate_definition_confidence(
                        term, definition_text, page_info, search_result
                    )

                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_definition = TermDefinition(
                            term=term,
                            definition=definition_text,
                            source=search_result.domain,
                            url=search_result.url,
                            category=self._categorize_term(term, definition_text),
                            examples=self._extract_examples(definition_text),
                            related_terms=self._extract_related_terms(term, page_info.content),
                            confidence=confidence,
                            timestamp=datetime.now().isoformat()
                        )

            return best_definition

        except Exception as e:
            print(f"❌ 定義抽出エラー: {e}")
            return None

    def _find_definition_in_content(self, term: str, content: str) -> str:
        """コンテンツから定義を検索"""
        if not content:
            return ""

        # 定義パターンの検索
        patterns = [
            rf'{re.escape(term)}(?:\s+is|\s+とは|\s+means|\s+refers to)\s+([^.。!！?？]+[.。!！?？])',
            rf'(?:Definition|定義|説明)[:：]\s*([^.。!！?？]*{re.escape(term)}[^.。!！?？]*[.。!！?？])',
            rf'{re.escape(term)}\s*[:：]\s*([^.。!！?？]+[.。!！?？])',
            rf'([^.。!！?？]*{re.escape(term)}[^.。!！?？]*[.。!！?？])'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                # 最初のマッチを返す
                definition = matches[0].strip()
                if len(definition) > 20 and len(definition) < 500:  # 適切な長さの定義
                    return definition

        # フォールバック: 用語周辺のテキスト
        term_index = content.lower().find(term.lower())
        if term_index != -1:
            start = max(0, term_index - 100)
            end = min(len(content), term_index + len(term) + 200)
            context = content[start:end].strip()
            return context

        return ""

    def _calculate_definition_confidence(self, term: str, definition: str, page_info: WebPageInfo, search_result: SearchResult) -> float:
        """定義の信頼度計算"""
        confidence = 0.5  # ベース信頼度

        # ドメインによる信頼度調整
        trusted_domains = {
            'wikipedia.org': 0.3,
            'docs.python.org': 0.3,
            'stackoverflow.com': 0.2,
            'github.com': 0.1,
            '.edu': 0.2,
            '.gov': 0.2
        }

        for domain, bonus in trusted_domains.items():
            if domain in search_result.domain:
                confidence += bonus
                break

        # 定義の質による調整
        if len(definition) > 50 and len(definition) < 300:  # 適切な長さ
            confidence += 0.1

        if any(keyword in definition.lower() for keyword in ['is', 'とは', 'means', 'refers to']):
            confidence += 0.1

        # 検索順位による調整
        if search_result.rank <= 3:
            confidence += 0.1

        return min(1.0, confidence)

    def _categorize_term(self, term: str, definition: str) -> str:
        """用語カテゴリ分類"""
        programming_keywords = ['function', 'method', 'class', 'variable', 'library', 'framework', 'api']
        technical_keywords = ['algorithm', 'protocol', 'system', 'technology', 'software', 'hardware']

        term_lower = term.lower()
        definition_lower = definition.lower()

        if any(keyword in term_lower or keyword in definition_lower for keyword in programming_keywords):
            return "programming"
        elif any(keyword in term_lower or keyword in definition_lower for keyword in technical_keywords):
            return "technical"
        else:
            return "general"

    def _extract_examples(self, text: str) -> List[str]:
        """例の抽出"""
        examples = []

        # 例のパターン検索
        example_patterns = [
            r'(?:例|example|for example|e\.g\.):?\s*([^.。!！?？]+)',
            r'(?:such as|like)\s+([^.。!！?？]+)',
        ]

        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                example = match.strip()
                if len(example) > 10 and len(example) < 200:
                    examples.append(example)

        return examples[:3]  # 最大3個

    def _extract_related_terms(self, term: str, content: str) -> List[str]:
        """関連用語抽出"""
        related = []

        # 技術用語パターン
        tech_pattern = r'\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*\b'
        matches = re.findall(tech_pattern, content)

        # 重複除去と用語フィルタリング
        unique_terms = set(matches)
        for related_term in unique_terms:
            if (related_term != term and
                len(related_term) > 2 and
                len(related_term) < 30 and
                related_term.lower() not in ['the', 'and', 'for', 'with']):
                related.append(related_term)

        return related[:5]  # 最大5個

    # データベース操作メソッド
    def _save_search_result(self, result: SearchResult):
        """検索結果保存"""
        try:
            insert_sql = """
            INSERT INTO web_search_results (
                query, title, url, snippet, domain, search_engine, rank
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                result.query,
                result.title,
                result.url,
                result.snippet,
                result.domain,
                result.search_engine,
                result.rank
            ))

        except Exception as e:
            print(f"❌ 検索結果保存エラー: {e}")

    def _save_page_info(self, page_info: WebPageInfo):
        """ページ情報保存"""
        try:
            insert_sql = """
            INSERT OR REPLACE INTO web_page_info (
                url, title, content, headings, links, images,
                meta_description, keywords, language, content_length,
                status_code, load_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                page_info.url,
                page_info.title,
                page_info.content,
                json.dumps(page_info.headings, ensure_ascii=False),
                json.dumps(page_info.links, ensure_ascii=False),
                json.dumps(page_info.images, ensure_ascii=False),
                page_info.meta_description,
                json.dumps(page_info.keywords, ensure_ascii=False),
                page_info.language,
                page_info.content_length,
                page_info.status_code,
                page_info.load_time
            ))

        except Exception as e:
            print(f"❌ ページ情報保存エラー: {e}")

    def _save_term_definition(self, definition: TermDefinition):
        """用語定義保存"""
        try:
            insert_sql = """
            INSERT INTO term_definitions (
                term, definition, source, url, category,
                examples, related_terms, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                definition.term,
                definition.definition,
                definition.source,
                definition.url,
                definition.category,
                json.dumps(definition.examples, ensure_ascii=False),
                json.dumps(definition.related_terms, ensure_ascii=False),
                definition.confidence
            ))

        except Exception as e:
            print(f"❌ 用語定義保存エラー: {e}")

    def _save_search_history(self, query: str, results_count: int, search_type: str, success: bool, execution_time: float):
        """検索履歴保存"""
        try:
            insert_sql = """
            INSERT INTO search_history (
                query, results_count, search_type, success, execution_time
            ) VALUES (?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                query,
                results_count,
                search_type,
                success,
                execution_time
            ))

        except Exception as e:
            print(f"❌ 検索履歴保存エラー: {e}")

    def _get_cached_definition(self, term: str) -> Optional[TermDefinition]:
        """キャッシュ済み定義取得"""
        try:
            select_sql = """
            SELECT * FROM term_definitions
            WHERE term = ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT 1
            """

            cursor = self.db_manager._execute_sql(select_sql, (term,))
            row = cursor.fetchone()

            if row:
                return TermDefinition(
                    term=row[1],
                    definition=row[2],
                    source=row[3],
                    url=row[4],
                    category=row[5],
                    examples=json.loads(row[6]) if row[6] else [],
                    related_terms=json.loads(row[7]) if row[7] else [],
                    confidence=row[8],
                    timestamp=row[9]
                )

            return None

        except Exception as e:
            return None

    def _get_cached_page_info(self, url: str) -> Optional[WebPageInfo]:
        """キャッシュ済みページ情報取得"""
        try:
            select_sql = """
            SELECT * FROM web_page_info
            WHERE url = ? AND datetime(last_crawled) > datetime('now', '-1 day')
            """

            cursor = self.db_manager._execute_sql(select_sql, (url,))
            row = cursor.fetchone()

            if row:
                return WebPageInfo(
                    url=row[1],
                    title=row[2],
                    content=row[3],
                    headings=json.loads(row[4]) if row[4] else [],
                    links=json.loads(row[5]) if row[5] else [],
                    images=json.loads(row[6]) if row[6] else [],
                    meta_description=row[7],
                    keywords=json.loads(row[8]) if row[8] else [],
                    language=row[9],
                    content_length=row[10],
                    status_code=row[11],
                    load_time=row[12],
                    timestamp=row[13]
                )

            return None

        except Exception as e:
            return None

    def get_search_statistics(self) -> dict:
        """検索統計取得"""
        try:
            stats = {}

            # 総検索数
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM search_history")
            stats["total_searches"] = cursor.fetchone()[0]

            # 成功率
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM search_history WHERE success = 1")
            successful = cursor.fetchone()[0]
            stats["success_rate"] = (successful / stats["total_searches"]) * 100 if stats["total_searches"] > 0 else 0

            # 定義数
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM term_definitions")
            stats["definitions_count"] = cursor.fetchone()[0]

            # ページ数
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM web_page_info")
            stats["pages_analyzed"] = cursor.fetchone()[0]

            # 人気検索語
            cursor = self.db_manager._execute_sql("""
                SELECT query, COUNT(*) as count
                FROM search_history
                GROUP BY query
                ORDER BY count DESC
                LIMIT 5
            """)
            stats["popular_queries"] = [{"query": row[0], "count": row[1]} for row in cursor.fetchall()]

            return stats

        except Exception as e:
            return {"error": str(e)}


def main():
    """テスト実行"""
    print("🔍 Web検索・調査システム テスト開始")
    print("=" * 60)

    # システム初期化
    investigator = WebSearchInvestigator()

    # 統計表示
    stats = investigator.get_search_statistics()
    print(f"📊 検索統計:")
    print(f"  🔍 総検索数: {stats.get('total_searches', 0)}")
    print(f"  ✅ 成功率: {stats.get('success_rate', 0):.1f}%")
    print(f"  📚 定義数: {stats.get('definitions_count', 0)}")
    print(f"  📄 解析ページ数: {stats.get('pages_analyzed', 0)}")
    print()

    # テスト検索
    test_terms = [
        ("Python", "programming"),
        ("機械学習", "general"),
        ("Flask", "python"),
        ("BeautifulSoup", "python")
    ]

    for term, search_type in test_terms:
        print(f"🔍 '{term}' を検索中 (タイプ: {search_type})...")

        result = investigator.search_term(term, search_type, max_results=5)

        if result["success"]:
            definition = result.get("definition")
            if definition:
                print(f"✅ 定義取得成功:")
                print(f"  📝 定義: {definition.definition[:100]}...")
                print(f"  🌐 ソース: {definition.source}")
                print(f"  🎯 信頼度: {definition.confidence:.2f}")
                print(f"  📂 カテゴリ: {definition.category}")
            else:
                print(f"⚠️ 定義は取得できませんでしたが、{len(result.get('search_results', []))}件の検索結果を取得")

            print(f"  ⏱️ 検索時間: {result['search_time']:.2f}秒")
        else:
            print(f"❌ 検索失敗: {result.get('error', 'Unknown error')}")

        print("-" * 40)

    # 最終統計
    final_stats = investigator.get_search_statistics()
    print(f"\n📈 最終統計:")
    print(f"  🔍 総検索数: {final_stats.get('total_searches', 0)}")
    print(f"  📚 定義数: {final_stats.get('definitions_count', 0)}")
    print(f"  📄 解析ページ数: {final_stats.get('pages_analyzed', 0)}")

    print(f"\n💾 データベース: {investigator.db_manager.db_path}")
    print("🎉 テスト完了!")


if __name__ == "__main__":
    main()
