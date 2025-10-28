#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal BeautifulSoup CLI
Usage:
  python tools/bs_scraper.py URL|- [N] [TEXT] [--out FILE | --out-dir DIR] [--save DIR]

引数:
  URL|-     : 取得元。URL か '-'（STDIN）
  N         : 取得モード番号（省略可。省略時は「タイトル＋本文」を返す）
  TEXT      : n=6 は検索語 / n=8 はCSSセレクタ

主なモード:
  1: <title>
  2: og:title
  3: meta description/og:description
  4: 本文サマリ（~2000文字）
  5: 全リンク一覧（text, href）
  6: キーワード一致段落（TEXT）
  7: 標準まとめJSON（title/description/canonical/og/sample_text/links）
  8: CSSセレクタ抽出（TEXT）
  9: canonical URL
  10: <img src> 一覧 + 画像保存（--save未指定時は ./images）

オプション:
  --timeout SECONDS   : デフォルト15
  --pretty            : JSON整形出力
  --out FILE          : 出力をファイル保存（標準出力も行う）
  --out-dir DIR       : URLと日時から自動命名してDIR配下に保存（標準出力も行う）
  --save DIR          : 画像保存先（n=10時）。未指定なら ./images
  --modes / --modes-json : モード一覧の表示
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Iterable
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

MODES: Dict[int, str] = {
    1: "<title>（or og:title）",
    2: "og:title",
    3: "meta description（or og:description）",
    4: "本文のサマリ（~2000文字）",
    5: "ページ内リンク一覧（text, href）最大100件",
    6: "キーワード一致段落（TEXT=検索語, 大小無視）",
    7: "標準まとめJSON（title/description/canonical/og/sample_text/links）",
    8: "CSSセレクタ抽出（TEXT=CSSセレクタ, 要素テキスト配列）",
    9: "canonical URL",
    10: "<img> の src 一覧 + 保存（--save 省略時は ./images）",
}

def print_modes() -> None:
    print("番号ヘルプ:")
    for k in sorted(MODES):
        print(f"  {k:>2}: {MODES[k]}")

def print_modes_json() -> None:
    print(json.dumps(MODES, ensure_ascii=False, indent=2))

def fetch(url: str, timeout: float = 15.0) -> str:
    headers = {"User-Agent": DEFAULT_UA, "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(follow_redirects=True, headers=headers, timeout=timeout) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text

def bs(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

def collapse(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", (s or "").strip())

def meta(head: BeautifulSoup, *, name: str = "", prop: str = "", itemprop: str = "") -> Optional[str]:
    q = {}
    if name: q["name"] = name
    if prop: q["property"] = prop
    if itemprop: q["itemprop"] = itemprop
    tag = head.find("meta", q)
    return tag.get("content") if tag and tag.has_attr("content") else None

def standard(soup: BeautifulSoup) -> Dict[str, Any]:
    head = soup.find("head") or soup
    body = soup.find("body") or soup

    title = collapse(head.title.string) if head.title and head.title.string else None
    og_title = meta(head, prop="og:title")
    description = meta(head, name="description") or meta(head, prop="og:description") or meta(head, itemprop="description")
    og_url = meta(head, prop="og:url")
    og_image = meta(head, prop="og:image")

    canonical = None
    link_tag = head.find("link", rel=lambda v: v and "canonical" in v)
    if link_tag and link_tag.has_attr("href"):
        canonical = link_tag["href"]

    content_root = soup.find(["article", "main"]) or soup.find("section") or body
    for tag in content_root(["script", "style", "noscript"]):
        tag.extract()
    sample_text = collapse(content_root.get_text(separator=" ").strip())[:2000]

    links: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        txt = collapse(a.get_text())
        href = a["href"].strip()
        if not txt and not href:
            continue
        links.append({"text": txt, "href": href})
        if len(links) >= 100:
            break

    return {
        "title": og_title or title,
        "description": description,
        "canonical": canonical,
        "og": {"url": og_url, "image": og_image, "title": og_title or title},
        "sample_text": sample_text,
        "links": links,
    }

def search_paragraphs(soup: BeautifulSoup, keyword: str, max_hits: int = 30) -> List[str]:
    if not keyword:
        return []
    patt = re.compile(re.escape(keyword), re.IGNORECASE)
    blocks = soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"])
    results: List[str] = []

    def add(text: str):
        t = collapse(text)
        if t and patt.search(t):
            results.append(t)

    for b in blocks:
        add(b.get_text(separator=" "))
        if len(results) >= max_hits:
            return results

    if len(results) < max_hits:
        for b in soup.find_all(["article", "main", "section", "div"]):
            add(b.get_text(separator=" "))
            if len(results) >= max_hits:
                break
    return results[:max_hits]

def select_texts(soup: BeautifulSoup, selector: str, max_hits: int = 200) -> List[str]:
    out: List[str] = []
    if not selector:
        return out
    for el in soup.select(selector):
        out.append(collapse(el.get_text()))
        if len(out) >= max_hits:
            break
    return out

def absolutize_urls(base_url: str, urls: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for u in urls:
        u = u.strip()
        if not u:
            continue
        if u.startswith("data:"):
            continue
        absu = urljoin(base_url, u)
        if absu not in seen:
            seen.add(absu)
            out.append(absu)
    return out

def get_images(soup: BeautifulSoup, base_url: str, max_hits: int = 100) -> List[str]:
    rels = []
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src:
            rels.append(src)
            if len(rels) >= max_hits:
                break
    return absolutize_urls(base_url, rels)

def content_type_to_ext(ct: Optional[str]) -> str:
    m = (ct or "").split(";")[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
        "image/tiff": ".tif",
        "image/x-icon": ".ico",
    }.get(m, "")

def guess_ext(url: str, ct: Optional[str]) -> str:
    from os.path import splitext
    ext = content_type_to_ext(ct)
    if ext:
        return ext
    path = urlparse(url).path
    ext = splitext(path)[1]
    if ext and len(ext) <= 5:
        return ext
    return ".jpg"

def save_images(img_urls: List[str], destdir: Path, timeout: float = 15.0) -> None:
    destdir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": DEFAULT_UA}) as client:
        for i, url in enumerate(img_urls, start=1):
            try:
                r = client.get(url)
                r.raise_for_status()
                ext = guess_ext(url, r.headers.get("Content-Type"))
                path = destdir / f"{i:04d}{ext}"
                path.write_bytes(r.content)
                print(f"[save] {path}")
            except Exception as e:
                print(f"[skip] {url} ({e})", file=sys.stderr)

def slugify_from_url(url: str, maxlen: int = 120) -> str:
    """URLのホスト＋パスからファイル名スラグを作る"""
    parsed = urlparse(url if url != "-" else "about:blank")
    base = (parsed.netloc + parsed.path).strip().strip("/")
    if not base:
        base = "page"
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    if len(base) > maxlen:
        base = base[:maxlen]
    return base or "page"

def write_output_strings(out_obj: Any, pretty: bool) -> str:
    if isinstance(out_obj, (dict, list)):
        return json.dumps(out_obj, ensure_ascii=False, indent=2 if pretty else None)
    return "" if out_obj is None else str(out_obj)

def auto_save_output(url: str, out_dir: Optional[str], output_str: str, is_json_like: bool) -> Optional[Path]:
    if not out_dir:
        return None
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    slug = slugify_from_url(url)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".json" if is_json_like else ".txt"
    path = d / f"{slug}_{ts}{ext}"
    path.write_text(output_str, encoding="utf-8")
    return path

def main() -> int:
    ap = argparse.ArgumentParser(description="Minimal BeautifulSoup CLI", add_help=True)
    ap.add_argument("source", help="URL か '-'（STDIN）")
    ap.add_argument("n", nargs="?", type=int, help="取得モード番号（1..10）。省略時はタイトル＋本文を返す")
    ap.add_argument("text", nargs="?", default="", help="n=6=検索語, n=8=CSSセレクタ")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--out", help="出力ファイル（テキスト/JSONを保存）")
    ap.add_argument("--out-dir", help="URLと日時で自動命名してDIR配下に保存")
    ap.add_argument("--save", help="画像保存先（n=10）。未指定時は ./images")
    ap.add_argument("--modes", action="store_true", help="番号ヘルプを表示して終了")
    ap.add_argument("--modes-json", action="store_true", help="番号ヘルプをJSONで表示して終了")
    args = ap.parse_args()

    if args.modes or args.modes_json:
        if args.modes_json:
            print_modes_json()
        else:
            print_modes()
        return 0

    src = args.source
    key = args.text

    try:
        if src == "-":
            html = sys.stdin.read()
            base_url = "about:blank"
        else:
            if not URL_RE.match(src):
                print("[error] SOURCE must be URL or '-'", file=sys.stderr)
                return 2
            html = fetch(src, timeout=args.timeout)
            base_url = src

        soup = bs(html)
        head = soup.find("head") or soup

        # 番号省略時: タイトル＋本文（JSONで返す）
        if args.n is None:
            std = standard(soup)
            out = {"title": std.get("title"), "content": std.get("sample_text")}
        else:
            n = args.n
            if n == 1:
                out = standard(soup)["title"]
            elif n == 2:
                out = meta(head, prop="og:title")
            elif n == 3:
                out = meta(head, name="description") or meta(head, prop="og:description")
            elif n == 4:
                out = standard(soup)["sample_text"]
            elif n == 5:
                out = standard(soup)["links"]
            elif n == 6:
                out = search_paragraphs(soup, key)
            elif n == 7:
                out = standard(soup)
            elif n == 8:
                out = select_texts(soup, key)
            elif n == 9:
                out = standard(soup)["canonical"]
            elif n == 10:
                out = get_images(soup, base_url=base_url)
                dest = Path(args.save) if args.save else Path("./images")
                save_images(out, dest, timeout=args.timeout)
            else:
                print("[error] n must be 1..10", file=sys.stderr)
                return 2

        # 出力文字列作成
        is_json_like = isinstance(out, (dict, list))
        output_str = write_output_strings(out, pretty=args.pretty)

        # 標準出力
        print(output_str)

        # 明示ファイル保存
        if args.out:
            try:
                Path(args.out).write_text(output_str, encoding="utf-8")
                print(f"[out] saved to {args.out}")
            except Exception as e:
                print(f"[warn] failed to write {args.out}: {e}", file=sys.stderr)

        # 自動命名保存（URL＋日時）
        auto_path = auto_save_output(src, args.out_dir, output_str, is_json_like)
        if auto_path:
            print(f"[out] saved to {auto_path}")

        return 0

    except httpx.HTTPError as e:
        print(f"[error] http: {type(e).__name__}: {e}", file=sys.stderr); return 3
    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}", file=sys.stderr); return 1

if __name__ == "__main__":
    raise SystemExit(main())
