#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web検索コマンドツール
コマンドラインから簡単に単語を調べられるツール
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.web.practical_web_searcher import PracticalWebSearcher


def format_result(result: dict, index: int) -> str:
    """検索結果をフォーマット"""
    confidence_stars = "⭐" * int(result['confidence'] * 5)

    formatted = f"\n{'='*60}\n"
    formatted += f"📍 結果 {index}\n"
    formatted += f"🏷️  タイトル: {result['title']}\n"
    formatted += f"📝 説明: {result['snippet']}\n"
    formatted += f"🔗 URL: {result['url']}\n"
    formatted += f"🌐 ソース: {result['source']}\n"
    formatted += f"⭐ 信頼度: {result['confidence']:.2f} {confidence_stars}\n"
    formatted += f"🕒 取得時刻: {result['timestamp']}\n"

    return formatted


def display_search_results(search_result: dict):
    """検索結果表示"""
    if not search_result.get("success"):
        print(f"\n❌ 検索失敗: {search_result.get('error', 'Unknown error')}")
        return

    term = search_result['term']
    results = search_result['results']
    execution_time = search_result['execution_time']
    source = search_result['source']

    print(f"\n🔍 '{term}' の検索結果")
    print(f"📊 {len(results)} 件の結果 | ⏱️ {execution_time:.2f}秒 | 📡 {source}")

    if not results:
        print("\n📭 結果が見つかりませんでした")
        return

    for i, result in enumerate(results, 1):
        print(format_result(result, i))

    # 要約表示
    print(f"\n{'='*60}")
    print(f"📋 要約:")
    print(f"  🎯 最高信頼度: {max(r['confidence'] for r in results):.2f}")
    print(f"  📚 情報源: {', '.join(set(r['source'] for r in results))}")

    # 最も信頼性の高い結果のスニペットを表示
    best_result = max(results, key=lambda x: x['confidence'])
    print(f"\n💡 推奨説明 ({best_result['source']}):")
    print(f"「{best_result['snippet']}」")


def interactive_search():
    """対話型検索モード"""
    searcher = PracticalWebSearcher()

    print("🔍 Web検索システム - 対話モード")
    print("=" * 60)
    print("💡 使い方:")
    print("  - 調べたい単語を入力してEnter")
    print("  - 'quit' または 'exit' で終了")
    print("  - 'stats' で統計表示")
    print("  - 'history' で検索履歴表示")
    print()

    search_history = []

    while True:
        try:
            user_input = input("\n🔍 調べたい単語を入力: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Web検索システムを終了します")
                break

            if user_input.lower() == 'stats':
                stats = searcher.get_statistics()
                print(f"\n📊 統計情報:")
                print(f"  🔍 総検索数: {stats.get('total_searches', 0)}")
                print(f"  🎯 平均信頼度: {stats.get('average_confidence', 0):.2f}")
                print(f"  📄 キャッシュページ数: {stats.get('cached_pages', 0)}")
                print(f"  📚 ソース分布: {stats.get('sources', {})}")
                continue

            if user_input.lower() == 'history':
                print(f"\n📚 検索履歴 (最新{len(search_history)}件):")
                for i, term in enumerate(reversed(search_history[-10:]), 1):
                    print(f"  {i}. {term}")
                continue

            # 検索実行
            print(f"\n🔄 '{user_input}' を検索中...")
            result = searcher.search_and_explain(user_input, max_results=3)

            # 結果表示
            display_search_results(result)

            # 履歴に追加
            search_history.append(user_input)

        except KeyboardInterrupt:
            print("\n\n👋 検索を中断しました")
            break
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")


def batch_search(terms: List[str], output_file: Optional[str] = None):
    """バッチ検索モード"""
    searcher = PracticalWebSearcher()

    print(f"🔍 バッチ検索モード - {len(terms)} 件の用語を処理")
    print("=" * 60)

    all_results = {}

    for i, term in enumerate(terms, 1):
        print(f"\n[{i}/{len(terms)}] '{term}' を検索中...")

        result = searcher.search_and_explain(term, max_results=2)
        all_results[term] = result

        if result.get("success"):
            print(f"✅ 成功: {len(result['results'])} 件の結果")
        else:
            print(f"❌ 失敗: {result.get('error', 'Unknown error')}")

    # 結果の表示・保存
    print(f"\n{'='*60}")
    print("📋 バッチ検索完了 - 結果サマリー")
    print(f"{'='*60}")

    successful = sum(1 for r in all_results.values() if r.get('success'))
    print(f"✅ 成功: {successful}/{len(terms)} 件")
    print(f"❌ 失敗: {len(terms) - successful}/{len(terms)} 件")

    # 詳細結果表示
    for term, result in all_results.items():
        print(f"\n📍 {term}:")
        if result.get("success"):
            best_result = max(result['results'], key=lambda x: x['confidence']) if result['results'] else None
            if best_result:
                print(f"  📝 {best_result['snippet'][:100]}...")
                print(f"  🌐 ソース: {best_result['source']} (信頼度: {best_result['confidence']:.2f})")
        else:
            print(f"  ❌ {result.get('error', 'Unknown error')}")

    # JSON出力
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 結果を保存しました: {output_file}")
        except Exception as e:
            print(f"\n❌ ファイル保存エラー: {e}")


def quick_search(term: str):
    """クイック検索モード"""
    searcher = PracticalWebSearcher()

    print(f"🔍 クイック検索: '{term}'")
    print("=" * 60)

    result = searcher.search_and_explain(term, max_results=1)

    if result.get("success") and result['results']:
        best_result = result['results'][0]
        print(f"✅ 検索成功 ({result['execution_time']:.2f}秒)")
        print(f"\n📝 {best_result['title']}")
        print(f"{best_result['snippet']}")
        print(f"\n🔗 詳細: {best_result['url']}")
        print(f"🌐 ソース: {best_result['source']} (信頼度: {best_result['confidence']:.2f})")
    else:
        print(f"❌ 検索失敗: {result.get('error', 'No results found')}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Web検索コマンドツール - 単語を調べてサイト情報を取得",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 対話モード
  python web_search_tool.py

  # 単語を直接検索
  python web_search_tool.py -q "Python"

  # 複数単語をバッチ検索
  python web_search_tool.py -b "Python" "Flask" "BeautifulSoup"

  # 結果をJSONファイルに保存
  python web_search_tool.py -b "機械学習" "深層学習" -o results.json

  # 詳細モードで検索
  python web_search_tool.py -s "JSON" -n 5
        """
    )

    parser.add_argument(
        '-q', '--quick',
        metavar='TERM',
        help='クイック検索（1件の結果を即座に表示）'
    )

    parser.add_argument(
        '-s', '--search',
        metavar='TERM',
        help='詳細検索（複数の結果を表示）'
    )

    parser.add_argument(
        '-b', '--batch',
        nargs='+',
        metavar='TERM',
        help='バッチ検索（複数の用語を一括処理）'
    )

    parser.add_argument(
        '-n', '--num-results',
        type=int,
        default=3,
        metavar='N',
        help='取得する結果数（デフォルト: 3）'
    )

    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='結果をJSONファイルに保存'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='統計情報を表示'
    )

    args = parser.parse_args()

    # 統計表示
    if args.stats:
        searcher = PracticalWebSearcher()
        stats = searcher.get_statistics()
        print("📊 Web検索システム統計")
        print("=" * 40)
        print(f"🔍 総検索数: {stats.get('total_searches', 0)}")
        print(f"🎯 平均信頼度: {stats.get('average_confidence', 0):.2f}")
        print(f"📄 キャッシュページ数: {stats.get('cached_pages', 0)}")
        print(f"📚 ソース分布: {stats.get('sources', {})}")
        return

    # クイック検索
    if args.quick:
        quick_search(args.quick)
        return

    # 詳細検索
    if args.search:
        searcher = PracticalWebSearcher()
        result = searcher.search_and_explain(args.search, max_results=args.num_results)
        display_search_results(result)

        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 結果を保存しました: {args.output}")
            except Exception as e:
                print(f"\n❌ ファイル保存エラー: {e}")
        return

    # バッチ検索
    if args.batch:
        batch_search(args.batch, args.output)
        return

    # デフォルト: 対話モード
    interactive_search()


if __name__ == "__main__":
    main()
