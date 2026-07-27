#!/usr/bin/env python3
"""Validate generated US rock essential-album pages and excluded content."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JA = json.loads((ROOT / "data/album_guide.json").read_text(encoding="utf-8"))
EN = json.loads((ROOT / "data/album_guide.en.json").read_text(encoding="utf-8"))
COUNT = sum(len(items) for items in JA.values())


def main() -> None:
    pages = sorted((ROOT / "items").glob("*/index.html")) + sorted((ROOT / "en/items").glob("*/index.html"))
    assert len(pages) == COUNT * 2, f"Expected {COUNT * 2} details, found {len(pages)}"
    notes = [row["note"] for guide in (JA, EN) for items in guide.values() for row in items]
    titles = {"ja": set(), "en": set()}
    descriptions = {"ja": set(), "en": set()}
    for path in pages:
        text = path.read_text(encoding="utf-8")
        lang = "en" if "/en/" in str(path) else "ja"
        for token in ('rel="canonical"', 'hreflang="ja"', 'hreflang="en"', 'hreflang="x-default"', 'property="og:title"', 'name="twitter:card"', '"@type":"MusicAlbum"', '"@type":"BreadcrumbList"'):
            assert token in text, f"Missing {token} in {path}"
        title = re.search(r"<title>(.*?)</title>", text).group(1)
        description = re.search(r'<meta name="description" content="(.*?)">', text).group(1)
        assert title not in titles[lang] and description not in descriptions[lang], f"Duplicate metadata: {path}"
        titles[lang].add(title)
        descriptions[lang].add(description)
        schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', text).group(1)
        json.loads(schema)
        assert not any(note in text for note in notes), f"Editorial note leaked into {path}"
        assert "<img" not in text and "tracklist" not in text.lower(), f"Image or track list leaked into {path}"
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#")):
                continue
            target = (path.parent / href.split("?", 1)[0].split("#", 1)[0]).resolve()
            if target.is_dir():
                target /= "index.html"
            assert target.exists(), f"Broken local link in {path}: {href}"
    tree = ET.parse(ROOT / "sitemap.xml")
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls = [node.text for node in tree.findall(f"{ns}url/{ns}loc")]
    assert len(urls) == COUNT * 2 + 8 == len(set(urls)), f"Unexpected sitemap count: {len(urls)}"
    for path in (ROOT / "items/index.html", ROOT / "en/items/index.html"):
        text = path.read_text(encoding="utf-8")
        assert text.count('/index.html') == 0
        assert len(re.findall(r'<li><a href="[^"]+/">', text)) == COUNT, f"Incomplete index: {path}"
    print(f"Validated {COUNT * 2} detail pages, 2 indexes, and {len(urls)} sitemap URLs.")


if __name__ == "__main__":
    main()
