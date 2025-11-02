#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実用的Web検索・情報取得システム
シンプルで確実に動作する単語検索・情報取得システム
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
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

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager


@dataclass
class SimpleSearchResult:
    """シンプル検索結果"""
    term: str
    title: str
    url: str
    snippet: str
    source: str
    confidence: float
    timestamp: str


@dataclass
class WebPageContent:
    """Webページコンテンツ"""
    url: str
    title: str
    main_content: str
    status_code: int
    load_time: float
    timestamp: str


class PracticalWebSearcher:
    """実用的Web検索クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.session = requests.Session()

        # 実用的なヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # 信頼できる情報源
        self.trusted_sources = {
            'programming': {
                'python': [
                    'https://docs.python.org/ja/3/',
                    'https://docs.python.org/3/',
                ],
                'general': [
                    'https://developer.mozilla.org/',
                    'https://stackoverflow.com/',
                ]
            },
            'definitions': [
                'https://ja.wikipedia.org/wiki/',
                'https://en.wikipedia.org/wiki/',
            ],
            'tutorials': [
                'https://qiita.com/',
                'https://zenn.dev/',
                'https://note.com/',
            ]
        }

        self._create_tables()

    def _create_tables(self):
        """テーブル作成"""
        # シンプル検索結果テーブル
        simple_results_sql = """
        CREATE TABLE IF NOT EXISTS simple_search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            title TEXT,
            url TEXT,
            snippet TEXT,
            source TEXT,
            confidence REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Webページコンテンツテーブル
        web_content_sql = """
        CREATE TABLE IF NOT EXISTS web_page_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            main_content TEXT,
            status_code INTEGER,
            load_time REAL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [simple_results_sql, web_content_sql]:
            self.db_manager._execute_sql(sql)

    def smart_search(self, query: str, max_results: int = 5) -> dict:
        """
        スマート検索（エラー解決策などに特化）

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            検索結果辞書
        """
        start_time = time.time()

        try:
            print(f"🔍 スマート検索: '{query}'")

            # 1. キャッシュチェック
            cached_results = self._get_cached_results(query)
            if cached_results:
                print(f"💾 キャッシュヒット: {len(cached_results)}件")
                return {
                    "success": True,
                    "query": query,
                    "search_results": [asdict(r) for r in cached_results],
                    "source": "cache",
                    "execution_time": time.time() - start_time
                }

            # 2. 実際の検索
            results = []

            # プログラミング関連の検索
            if any(keyword in query.lower() for keyword in ['python', 'error', 'fix', 'solution', 'traceback']):
                # Stack Overflow的な検索
                programming_results = self._search_programming_solutions(query)
                results.extend(programming_results)

            # 一般的なWeb検索
            if len(results) < max_results:
                web_results = self._search_web_simple(query, max_results - len(results))
                results.extend(web_results)

            # 3. 結果を保存
            for result in results:
                self._save_search_result(result)

            execution_time = time.time() - start_time
            print(f"✅ 検索完了: {len(results)}件 ({execution_time:.2f}秒)")

            return {
                "success": True,
                "query": query,
                "search_results": [asdict(r) for r in results],
                "source": "live_search",
                "execution_time": execution_time
            }

        except Exception as e:
            print(f"❌ スマート検索エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "search_results": [],
                "execution_time": time.time() - start_time
            }

    def _search_programming_solutions(self, query: str) -> List[SimpleSearchResult]:
        """プログラミング問題解決策の検索"""
        results = []

        try:
            # Googleで検索（よりシンプルで確実）
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"

            response = self.session.get(search_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            if response.status_code == 200 and HAS_BS4:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Googleの検索結果を抽出（新しいHTML構造に対応）
                for result_div in soup.find_all('div', class_='g')[:3]:
                    try:
                        # タイトルとリンクを取得
                        h3_tag = result_div.find('h3')
                        a_tag = result_div.find('a')

                        # スニペットを取得
                        snippet_div = result_div.find('div', {'data-sncf': '1'})
                        if not snippet_div:
                            snippet_div = result_div.find('span')

                        if h3_tag and a_tag:
                            results.append(SimpleSearchResult(
                                term=query,
                                title=h3_tag.get_text(strip=True),
                                url=a_tag.get('href', ''),
                                snippet=snippet_div.get_text(strip=True) if snippet_div else '',
                                source='google_search',
                                confidence=0.8,
                                timestamp=datetime.now().isoformat()
                            ))
                    except Exception as e:
                        continue

        except Exception as e:
            print(f"プログラミング検索エラー: {e}")

        return results

    def search_and_explain(self, term: str, max_results: int = 5) -> dict:
        """用語検索と説明取得（メイン機能）"""
        start_time = time.time()

        try:
            print(f"🔍 '{term}' について調査中...")

            # 1. キャッシュチェック
            cached_results = self._get_cached_results(term)
            if cached_results:
                print(f"💾 キャッシュから {len(cached_results)} 件の結果を取得")
                return {
                    "success": True,
                    "term": term,
                    "results": cached_results,
                    "source": "cache",
                    "execution_time": time.time() - start_time
                }

            # 2. 実際の検索実行
            search_results = self._perform_practical_search(term, max_results)

            if not search_results:
                # フォールバック: 直接的な情報検索
                fallback_results = self._fallback_search(term)
                if fallback_results:
                    search_results = fallback_results
                else:
                    return {
                        "success": False,
                        "error": f"'{term}' に関する情報が見つかりませんでした",
                        "term": term
                    }

            # 3. 結果をデータベースに保存
            for result in search_results:
                self._save_search_result(result)

            execution_time = time.time() - start_time
            print(f"✅ 検索完了: {len(search_results)} 件の結果 ({execution_time:.2f}秒)")

            return {
                "success": True,
                "term": term,
                "results": [asdict(r) for r in search_results],
                "source": "live_search",
                "execution_time": execution_time
            }

        except Exception as e:
            print(f"❌ 検索エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "term": term,
                "execution_time": time.time() - start_time
            }

    def _perform_practical_search(self, term: str, max_results: int) -> List[SimpleSearchResult]:
        """実用的検索実行"""
        results = []

        try:
            # 1. Wikipedia検索（最も信頼性が高い）
            wiki_results = self._search_wikipedia(term)
            results.extend(wiki_results)

            # 2. プログラミング関連の場合
            if self._is_programming_term(term):
                programming_results = self._search_programming_docs(term)
                results.extend(programming_results)

            # 3. 一般的なWeb検索（DuckDuckGo）
            if len(results) < max_results:
                web_results = self._search_web_simple(term, max_results - len(results))
                results.extend(web_results)

            return results[:max_results]

        except Exception as e:
            print(f"❌ 実用検索エラー: {e}")
            return []

    def _search_wikipedia(self, term: str) -> List[SimpleSearchResult]:
        """Wikipedia検索"""
        results = []

        try:
            # 日本語Wikipedia API
            api_url = "https://ja.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(term)

            response = self.session.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                result = SimpleSearchResult(
                    term=term,
                    title=data.get('title', term),
                    url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    snippet=data.get('extract', ''),
                    source="wikipedia_ja",
                    confidence=0.9,
                    timestamp=datetime.now().isoformat()
                )

                results.append(result)
                print(f"✅ Wikipedia (日本語): {result.title}")

            # 英語Wikipediaも試行
            if not results:
                en_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(term)
                en_response = self.session.get(en_api_url, timeout=10)

                if en_response.status_code == 200:
                    en_data = en_response.json()

                    result = SimpleSearchResult(
                        term=term,
                        title=en_data.get('title', term),
                        url=en_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        snippet=en_data.get('extract', ''),
                        source="wikipedia_en",
                        confidence=0.8,
                        timestamp=datetime.now().isoformat()
                    )

                    results.append(result)
                    print(f"✅ Wikipedia (英語): {result.title}")

            return results

        except Exception as e:
            print(f"⚠️ Wikipedia検索エラー: {e}")
            return []

    def _search_programming_docs(self, term: str) -> List[SimpleSearchResult]:
        """プログラミングドキュメント検索"""
        results = []

        try:
            # Python公式ドキュメント検索
            if any(keyword in term.lower() for keyword in ['python', 'pip', 'django', 'flask']):
                python_result = self._search_python_docs(term)
                if python_result:
                    results.append(python_result)

            return results

        except Exception as e:
            print(f"⚠️ プログラミングドキュメント検索エラー: {e}")
            return []

    def _search_python_docs(self, term: str) -> Optional[SimpleSearchResult]:
        """Python公式ドキュメント検索"""
        try:
            # Pythonドキュメント検索
            search_url = f"https://docs.python.org/ja/3/search.html?q={quote_plus(term)}"

            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200 and HAS_BS4:
                soup = BeautifulSoup(response.content, 'html.parser')

                # 検索結果の解析
                search_results = soup.find_all('li', class_='search-result')

                if search_results:
                    first_result = search_results[0]
                    link = first_result.find('a')

                    if link:
                        title = link.get_text().strip()
                        url = urljoin('https://docs.python.org/', link.get('href'))

                        # スニペット取得
                        snippet_elem = first_result.find('p')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                        result = SimpleSearchResult(
                            term=term,
                            title=title,
                            url=url,
                            snippet=snippet,
                            source="python_docs",
                            confidence=0.9,
                            timestamp=datetime.now().isoformat()
                        )

                        print(f"✅ Python Docs: {title}")
                        return result

            return None

        except Exception as e:
            print(f"⚠️ Python Docs検索エラー: {e}")
            return None

    def _search_web_simple(self, term: str, max_results: int) -> List[SimpleSearchResult]:
        """シンプルWeb検索"""
        results = []

        try:
            # DuckDuckGo検索（シンプル）
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(term)}"

            response = self.session.get(search_url, timeout=15)

            if response.status_code == 200 and HAS_BS4:
                soup = BeautifulSoup(response.content, 'html.parser')

                # DuckDuckGo結果の解析
                search_items = soup.find_all('div', class_='result')

                for i, item in enumerate(search_items[:max_results]):
                    try:
                        # タイトルとURL
                        title_link = item.find('a', class_='result__a')
                        if not title_link:
                            continue

                        title = title_link.get_text().strip()
                        url = title_link.get('href')

                        # スニペット
                        snippet_elem = item.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                        # ドメイン判定
                        domain = urlparse(url).netloc if url else ""

                        # 信頼度計算
                        confidence = self._calculate_confidence(domain, title, snippet, term)

                        result = SimpleSearchResult(
                            term=term,
                            title=title,
                            url=url,
                            snippet=snippet,
                            source="duckduckgo",
                            confidence=confidence,
                            timestamp=datetime.now().isoformat()
                        )

                        results.append(result)
                        print(f"✅ Web検索: {title[:50]}...")

                    except Exception as e:
                        continue

            return results

        except Exception as e:
            print(f"⚠️ Web検索エラー: {e}")
            return []

    def _fallback_search(self, term: str) -> List[SimpleSearchResult]:
        """フォールバック検索（知識ベース）"""
        results = []

        try:
            # 既知の用語定義
            knowledge_base = {
                'python': {
                    'title': 'Python プログラミング言語',
                    'snippet': 'Pythonは、汎用性の高いプログラミング言語です。コードの読みやすさを重視した設計哲学で、簡潔で理解しやすい構文が特徴です。',
                    'url': 'https://www.python.org/',
                    'confidence': 0.8
                },
                'beautifulsoup': {
                    'title': 'Beautiful Soup - Pythonライブラリ',
                    'snippet': 'Beautiful SoupはPythonのライブラリで、HTMLとXMLファイルを解析するために使用されます。ウェブスクレイピングやデータ抽出に便利です。',
                    'url': 'https://pypi.org/project/beautifulsoup4/',
                    'confidence': 0.8
                },
                'flask': {
                    'title': 'Flask - Python Webフレームワーク',
                    'snippet': 'FlaskはPythonのマイクロWebフレームワークです。シンプルで軽量、拡張可能な設計により、Web アプリケーションを迅速に開発できます。',
                    'url': 'https://flask.palletsprojects.com/',
                    'confidence': 0.8
                },
                '機械学習': {
                    'title': '機械学習 (Machine Learning)',
                    'snippet': '機械学習は、コンピューターがデータから学習し、明示的にプログラムされることなく予測や判断を行う人工知能の手法です。',
                    'url': 'https://ja.wikipedia.org/wiki/機械学習',
                    'confidence': 0.7
                }
            }

            term_lower = term.lower()
            if term_lower in knowledge_base:
                kb_data = knowledge_base[term_lower]

                result = SimpleSearchResult(
                    term=term,
                    title=kb_data['title'],
                    url=kb_data['url'],
                    snippet=kb_data['snippet'],
                    source="knowledge_base",
                    confidence=kb_data['confidence'],
                    timestamp=datetime.now().isoformat()
                )

                results.append(result)
                print(f"✅ 知識ベース: {kb_data['title']}")

            return results

        except Exception as e:
            return []

    def _is_programming_term(self, term: str) -> bool:
        """プログラミング用語判定"""
        programming_keywords = {
            'python', 'javascript', 'java', 'html', 'css', 'react', 'vue',
            'flask', 'django', 'fastapi', 'beautifulsoup', 'requests',
            'numpy', 'pandas', 'matplotlib', 'scikit-learn', 'tensorflow',
            'api', 'json', 'xml', 'sql', 'git', 'github', 'docker',
            'function', 'class', 'method', 'variable', 'loop', 'array'
        }

        return any(keyword in term.lower() for keyword in programming_keywords)

    def _calculate_confidence(self, domain: str, title: str, snippet: str, term: str) -> float:
        """信頼度計算"""
        confidence = 0.5  # ベース

        # ドメイン信頼度
        trusted_domains = {
            'wikipedia.org': 0.3,
            'docs.python.org': 0.3,
            'developer.mozilla.org': 0.2,
            'stackoverflow.com': 0.2,
            'github.com': 0.1,
            'qiita.com': 0.1,
            'zenn.dev': 0.1
        }

        for trusted_domain, bonus in trusted_domains.items():
            if trusted_domain in domain:
                confidence += bonus
                break

        # 内容関連性
        if term.lower() in title.lower():
            confidence += 0.2

        if term.lower() in snippet.lower():
            confidence += 0.1

        # 内容の質
        if len(snippet) > 50 and len(snippet) < 300:
            confidence += 0.1

        return min(1.0, confidence)

    def get_page_content(self, url: str) -> Optional[WebPageContent]:
        """Webページコンテンツ取得"""
        start_time = time.time()

        try:
            # キャッシュチェック
            cached_content = self._get_cached_content(url)
            if cached_content:
                return cached_content

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            load_time = time.time() - start_time

            title = ""
            main_content = ""

            if HAS_BS4:
                soup = BeautifulSoup(response.content, 'html.parser')

                # タイトル抽出
                title_elem = soup.find('title')
                title = title_elem.get_text().strip() if title_elem else ""

                # メインコンテンツ抽出
                content_selectors = [
                    'main', 'article', '#content', '.content',
                    '.post-content', '.entry-content', '#main-content'
                ]

                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        main_content = content_elem.get_text().strip()
                        break

                # フォールバック
                if not main_content:
                    body = soup.find('body')
                    if body:
                        main_content = body.get_text().strip()
            else:
                # BeautifulSoupなしの場合
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
                title = title_match.group(1) if title_match else ""

                # HTMLタグ除去
                main_content = re.sub(r'<[^>]+>', ' ', response.text)
                main_content = re.sub(r'\s+', ' ', main_content).strip()

            page_content = WebPageContent(
                url=url,
                title=title,
                main_content=main_content[:5000],  # 最初の5000文字
                status_code=response.status_code,
                load_time=load_time,
                timestamp=datetime.now().isoformat()
            )

            # キャッシュに保存
            self._save_page_content(page_content)

            return page_content

        except Exception as e:
            print(f"❌ ページ取得エラー ({url}): {e}")
            return None

    # データベース操作
    def _save_search_result(self, result: SimpleSearchResult):
        """検索結果保存"""
        try:
            insert_sql = """
            INSERT INTO simple_search_results (
                term, title, url, snippet, source, confidence
            ) VALUES (?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                result.term,
                result.title,
                result.url,
                result.snippet,
                result.source,
                result.confidence
            ))

        except Exception as e:
            pass  # エラーは無視

    def _save_page_content(self, content: WebPageContent):
        """ページコンテンツ保存"""
        try:
            insert_sql = """
            INSERT OR REPLACE INTO web_page_content (
                url, title, main_content, status_code, load_time
            ) VALUES (?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                content.url,
                content.title,
                content.main_content,
                content.status_code,
                content.load_time
            ))

        except Exception as e:
            pass

    def _get_cached_results(self, term: str) -> List[dict]:
        """キャッシュ結果取得"""
        try:
            select_sql = """
            SELECT term, title, url, snippet, source, confidence, created_at
            FROM simple_search_results
            WHERE term = ? AND datetime(created_at) > datetime('now', '-1 day')
            ORDER BY confidence DESC
            LIMIT 5
            """

            cursor = self.db_manager._execute_sql(select_sql, (term,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "term": row[0],
                    "title": row[1],
                    "url": row[2],
                    "snippet": row[3],
                    "source": row[4],
                    "confidence": row[5],
                    "timestamp": row[6]
                })

            return results

        except Exception as e:
            return []

    def _get_cached_content(self, url: str) -> Optional[WebPageContent]:
        """キャッシュコンテンツ取得"""
        try:
            select_sql = """
            SELECT url, title, main_content, status_code, load_time, last_updated
            FROM web_page_content
            WHERE url = ? AND datetime(last_updated) > datetime('now', '-1 day')
            """

            cursor = self.db_manager._execute_sql(select_sql, (url,))
            row = cursor.fetchone()

            if row:
                return WebPageContent(
                    url=row[0],
                    title=row[1],
                    main_content=row[2],
                    status_code=row[3],
                    load_time=row[4],
                    timestamp=row[5]
                )

            return None

        except Exception as e:
            return None

    def get_statistics(self) -> dict:
        """統計取得"""
        try:
            stats = {}

            # 検索統計
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM simple_search_results")
            stats["total_searches"] = cursor.fetchone()[0]

            # ソース別統計
            cursor = self.db_manager._execute_sql("""
                SELECT source, COUNT(*)
                FROM simple_search_results
                GROUP BY source
            """)
            stats["sources"] = {row[0]: row[1] for row in cursor.fetchall()}

            # 平均信頼度
            cursor = self.db_manager._execute_sql("SELECT AVG(confidence) FROM simple_search_results")
            result = cursor.fetchone()[0]
            stats["average_confidence"] = result if result else 0

            # ページ統計
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM web_page_content")
            stats["cached_pages"] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            return {"error": str(e)}


def main():
    """テスト実行"""
    print("🔍 実用的Web検索システム テスト開始")
    print("=" * 60)

    # BeautifulSoup状態確認
    print(f"📦 BeautifulSoup: {'✅ 利用可能' if HAS_BS4 else '❌ 未インストール'}")
    print()

    # システム初期化
    searcher = PracticalWebSearcher()

    # 統計表示
    stats = searcher.get_statistics()
    print(f"📊 現在の統計:")
    print(f"  🔍 総検索数: {stats.get('total_searches', 0)}")
    print(f"  🎯 平均信頼度: {stats.get('average_confidence', 0):.2f}")
    print(f"  📄 キャッシュページ数: {stats.get('cached_pages', 0)}")
    print(f"  📚 ソース分布: {stats.get('sources', {})}")
    print()

    # テスト検索
    test_terms = [
        "Python",
        "BeautifulSoup",
        "機械学習",
        "Flask",
        "JSON"
    ]

    for term in test_terms:
        print(f"🔍 '{term}' を調査...")

        result = searcher.search_and_explain(term, max_results=3)

        if result["success"]:
            results = result["results"]
            print(f"✅ 成功: {len(results)} 件の結果 ({result['execution_time']:.2f}秒)")

            for i, res in enumerate(results, 1):
                print(f"  {i}. {res['title']}")
                print(f"     📝 {res['snippet'][:100]}...")
                print(f"     🌐 ソース: {res['source']} (信頼度: {res['confidence']:.2f})")
                print(f"     🔗 {res['url']}")
        else:
            print(f"❌ 失敗: {result.get('error', 'Unknown error')}")

        print("-" * 40)

    # 最終統計
    final_stats = searcher.get_statistics()
    print(f"\n📈 最終統計:")
    print(f"  🔍 総検索数: {final_stats.get('total_searches', 0)}")
    print(f"  🎯 平均信頼度: {final_stats.get('average_confidence', 0):.2f}")
    print(f"  📚 ソース分布: {final_stats.get('sources', {})}")

    print(f"\n💾 データベース: {searcher.db_manager.db_path}")
    print("🎉 テスト完了!")


if __name__ == "__main__":
    main()
