#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Iterable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)

def fetch_html(url: str, timeout: float = 15.0, ua: Optional[str] = None) -> str:
    headers = {"User-Agent": ua or DEFAULT_UA, "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(follow_redirects=True, headers=headers, timeout=timeout) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text

def soupify(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _meta(head: BeautifulSoup, *, name: str = "", prop: str = "", itemprop: str = "") -> Optional[str]:
    q = {}
    if name: q["name"] = name
    if prop: q["property"] = prop
    if itemprop: q["itemprop"] = itemprop
    tag = head.find("meta", q)
    return tag.get("content") if tag and tag.has_attr("content") else None

def extract_standard(soup: BeautifulSoup) -> Dict[str, Any]:
    head = soup.find("head") or soup
    body = soup.find("body") or soup

    title = _collapse(head.title.string) if head.title and head.title.string else None
    og_title = _meta(head, prop="og:title")
    description = (
        _meta(head, name="description")
        or _meta(head, prop="og:description")
        or _meta(head, itemprop="description")
    )
    og_url = _meta(head, prop="og:url")
    og_image = _meta(head, prop="og:image")

    canonical = None
    link_tag = head.find("link", rel=lambda v: v and "canonical" in v)
    if link_tag and link_tag.has_attr("href"):
        canonical = link_tag["href"]

    content_root = soup.find(["article", "main"]) or soup.find("section") or body
    for tag in content_root(["script", "style", "noscript"]):
        tag.extract()
    sample_text = _collapse(content_root.get_text(separator=" ").strip())[:2000]

    links: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        txt = _collapse(a.get_text())
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
        t = _collapse(text)
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
        out.append(_collapse(el.get_text()))
        if len(out) >= max_hits:
            break
    return out

def absolutize_urls(base_url: str, urls: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for u in urls:
        u = (u or "").strip()
        if not u:
            continue
        if u.startswith("data:"):
            continue
        absu = urljoin(base_url, u)
        if absu not in seen:
            seen.add(absu)
            out.append(absu)
    return out

def extract_images(soup: BeautifulSoup, base_url: str, max_hits: int = 100) -> List[str]:
    rels = []
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src:
            rels.append(src)
            if len(rels) >= max_hits:
                break
    return absolutize_urls(base_url, rels)
