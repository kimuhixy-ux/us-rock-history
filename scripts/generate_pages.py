#!/usr/bin/env python3
"""Generate bilingual, fact-only pages for the curated essential-album guide."""

from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path
from string import Template
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://kimuhixy.com/us-rock-history"
OG_IMAGE = f"{BASE}/icons/icon-512.png"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def ascii_slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def load_rows() -> tuple[list[dict], dict, dict, dict[str, str]]:
    ja = json.loads((ROOT / "data/album_guide.json").read_text(encoding="utf-8"))
    en = json.loads((ROOT / "data/album_guide.en.json").read_text(encoding="utf-8"))
    genres_ja = json.loads((ROOT / "data/genres.json").read_text(encoding="utf-8"))
    genres_en = json.loads((ROOT / "data/genres.en.json").read_text(encoding="utf-8"))
    artist_types = {row["name"]: row.get("type", "group") for row in json.loads((ROOT / "data/artists.json").read_text(encoding="utf-8"))}
    if ja.keys() != en.keys() or any(len(ja[key]) != len(en[key]) for key in ja):
        raise ValueError("Japanese and English album guides do not align.")
    rows = []
    used = set()
    for genre_id, ja_items in ja.items():
        for position, (ja_row, en_row) in enumerate(zip(ja_items, en[genre_id]), 1):
            identity_ja = (ja_row["artist"], ja_row["album"], ja_row["year"])
            identity_en = (en_row["artist"], en_row["album"], en_row["year"])
            if identity_ja != identity_en:
                raise ValueError(f"Guide mismatch in {genre_id} record {position}.")
            base = ascii_slug(f"{ja_row['artist']}-{ja_row['album']}-{ja_row['year']}") or f"album-{position}"
            slug, suffix = base, 2
            while slug in used or slug == "index":
                slug, suffix = f"{base}-{suffix}", suffix + 1
            used.add(slug)
            rows.append({"genre_id": genre_id, "ja": ja_row, "en": en_row, "slug": slug})
    labels_ja = {x["id"]: x["label"] for x in genres_ja["categories"]}
    labels_en = {x["id"]: x["label"] for x in genres_en["categories"]}
    return rows, labels_ja, labels_en, artist_types


def related_indices(rows: list[dict]) -> list[list[int]]:
    result = []
    for i, row in enumerate(rows):
        album = row["ja"]
        ranked = sorted((j for j in range(len(rows)) if j != i), key=lambda j: (
            -(rows[j]["ja"]["artist"] == album["artist"]),
            -(rows[j]["genre_id"] == row["genre_id"]),
            abs(int(rows[j]["ja"]["year"]) - int(album["year"])),
            rows[j]["slug"],
        ))
        result.append(ranked[:6])
    return result


def schema(row: dict, genre: str, artist_type: str, english: bool) -> str:
    data = row["en" if english else "ja"]
    prefix = "en/" if english else ""
    canonical = f"{BASE}/{prefix}items/{row['slug']}/"
    album_id = f"{canonical}#album"
    artist_schema_type = "Person" if artist_type == "person" else "MusicGroup"
    graph = [
        {"@type": "WebSite", "@id": f"{BASE}/#website", "url": f"{BASE}/", "name": "US Rock History", "inLanguage": ["ja", "en"]},
        {"@type": "WebPage", "@id": f"{canonical}#webpage", "url": canonical, "name": data["album"], "inLanguage": "en" if english else "ja", "isPartOf": {"@id": f"{BASE}/#website"}, "mainEntity": {"@id": album_id}},
        {"@type": "MusicAlbum", "@id": album_id, "name": data["album"], "byArtist": {"@type": artist_schema_type, "name": data["artist"]}, "datePublished": str(data["year"]), "genre": genre},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home" if english else "トップ", "item": f"{BASE}/{prefix}"},
            {"@type": "ListItem", "position": 2, "name": "Essential album index" if english else "名盤索引", "item": f"{BASE}/{prefix}items/"},
            {"@type": "ListItem", "position": 3, "name": data["album"], "item": canonical},
        ]},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def detail_context(row: dict, genre: str, related: list[int], rows: list[dict], artist_types: dict[str, str], english: bool) -> dict[str, str]:
    data = row["en" if english else "ja"]
    prefix = "en/" if english else ""
    canonical = f"{BASE}/{prefix}items/{row['slug']}/"
    root = "../../../" if english else "../../"
    home = f"{root}{'en/' if english else ''}"
    title = data["album"]
    artist = data["artist"]
    facts = "".join([
        f'<div><dt>{"Artist" if english else "アーティスト"}</dt><dd>{esc(artist)}</dd></div>',
        f'<div><dt>{"Release year" if english else "発表年"}</dt><dd>{esc(data["year"])}</dd></div>',
        f'<div><dt>{"Genre" if english else "ジャンル"}</dt><dd>{esc(genre)}</dd></div>',
    ])
    related_html = "".join(f'<li><a href="../{rows[i]["slug"]}/">{esc(rows[i]["en" if english else "ja"]["album"])}</a><span>{esc(rows[i]["en" if english else "ja"]["artist"])}</span></li>' for i in related)
    query = quote(f"{artist} {title}")
    meta = f"{title} by {artist}, released in {data['year']}. View genre facts in the US Rock History essential album guide." if english else f"{artist}『{title}』（{data['year']}年）のジャンルをUS Rock History名盤ガイドの事実情報で確認できます。"
    return {
        "lang": "en" if english else "ja", "title": esc(title), "artist": esc(artist), "genre": esc(genre),
        "page_title": esc(f"{title} — {artist} ({data['year']}) | US Rock History"), "meta_description": esc(meta[:155]),
        "canonical": canonical, "ja_url": f"{BASE}/items/{row['slug']}/", "en_url": f"{BASE}/en/items/{row['slug']}/", "og_image": OG_IMAGE,
        "json_ld": schema(row, genre, artist_types.get(artist, "group"), english), "root": root, "home_url": home, "index_url": "../",
        "index_label": "Essential album index" if english else "名盤索引", "other_url": f"{BASE}/{'items' if english else 'en/items'}/{row['slug']}/", "other_label": "日本語" if english else "English",
        "breadcrumb_label": "Breadcrumb" if english else "パンくずリスト", "home_label": "Home" if english else "トップ", "facts": facts,
        "source_note": "This page contains factual metadata from the curated guide. Editorial notes, cover art, track lists, and audio are not reproduced." if english else "このページは精選名盤ガイドの事実情報を掲載しています。紹介文、ジャケット画像、曲目、音源は転載していません。",
        "app_url": f"{home}#/guide", "app_label": "Open the essential album guide" if english else "アプリの名盤ガイドを開く",
        "spotify_url": f"https://open.spotify.com/search/{query}", "apple_url": f"https://music.apple.com/{'us' if english else 'jp'}/search?term={query}",
        "related_label": "Related essential albums" if english else "関連する名盤", "related": related_html,
        "data_note": "Data source: MusicBrainz. Playback links go to Spotify / Apple Music." if english else "データ出典: MusicBrainz。楽曲再生はSpotify / Apple Musicへリンクします。",
        "about_url": f"{home}about.html", "about_label": "About" if english else "運営者情報", "privacy_url": f"{home}privacy.html", "privacy_label": "Privacy Policy" if english else "プライバシーポリシー",
    }


def index_context(rows: list[dict], labels: dict, english: bool) -> dict[str, str]:
    prefix = "en/" if english else ""
    root = "../../" if english else "../"
    home = f"{root}{'en/' if english else ''}"
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["genre_id"]].append(row)
    groups = []
    for genre_id, name in labels.items():
        if genre_id not in grouped:
            continue
        links = "".join(f'<li><a href="{row["slug"]}/">{esc(row["en" if english else "ja"]["album"])}</a><span>{esc(row["en" if english else "ja"]["artist"])} · {esc(row["en" if english else "ja"]["year"])}</span></li>' for row in grouped[genre_id])
        groups.append(f'<section class="pseo-index-group"><h2>{esc(name)}</h2><ul>{links}</ul></section>')
    title = "Essential US Rock Album Index" if english else "米国ロック名盤索引"
    canonical = f"{BASE}/{prefix}items/"
    graph = [{"@type": "WebSite", "@id": f"{BASE}/#website", "url": f"{BASE}/", "name": "US Rock History", "inLanguage": ["ja", "en"]}, {"@type": "CollectionPage", "url": canonical, "name": title, "inLanguage": "en" if english else "ja", "isPartOf": {"@id": f"{BASE}/#website"}}]
    return {
        "lang": "en" if english else "ja", "title": title, "page_title": f"{title} | US Rock History",
        "meta_description": f"Browse {len(rows)} essential US rock albums by genre, with artist and release-year facts." if english else f"米国ロックの精選名盤{len(rows)}枚をジャンル別に探せる索引です。アーティストと発表年を確認できます。",
        "canonical": canonical, "ja_url": f"{BASE}/items/", "en_url": f"{BASE}/en/items/", "og_image": OG_IMAGE,
        "json_ld": json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")), "root": root,
        "home_url": home, "home_label": "Home" if english else "トップ", "other_url": f"{BASE}/{'items' if english else 'en/items'}/", "other_label": "日本語" if english else "English",
        "lead": f"A genre-by-genre index of {len(rows)} curated albums. Editorial notes remain in the app." if english else f"精選した名盤{len(rows)}枚のジャンル別索引です。紹介文はアプリ本体でご覧ください。",
        "groups": "".join(groups), "data_note": "Data source: MusicBrainz." if english else "データ出典: MusicBrainz。",
        "about_url": f"{home}about.html", "about_label": "About" if english else "運営者情報", "privacy_url": f"{home}privacy.html", "privacy_label": "Privacy Policy" if english else "プライバシーポリシー",
    }


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    rows, labels_ja, labels_en, artist_types = load_rows()
    related = related_indices(rows)
    detail_template = Template((ROOT / "templates/detail.html").read_text(encoding="utf-8"))
    index_template = Template((ROOT / "templates/index.html").read_text(encoding="utf-8"))
    for directory in (ROOT / "items", ROOT / "en/items"):
        if directory.exists():
            shutil.rmtree(directory)
    for i, row in enumerate(rows):
        for english, labels, path in ((False, labels_ja, ROOT / "items" / row["slug"] / "index.html"), (True, labels_en, ROOT / "en/items" / row["slug"] / "index.html")):
            write(path, detail_template.substitute(detail_context(row, labels[row["genre_id"]], related[i], rows, artist_types, english)))
    write(ROOT / "items/index.html", index_template.substitute(index_context(rows, labels_ja, False)))
    write(ROOT / "en/items/index.html", index_template.substitute(index_context(rows, labels_en, True)))
    urls = [f"{BASE}/", f"{BASE}/en/", f"{BASE}/about.html", f"{BASE}/en/about.html", f"{BASE}/privacy.html", f"{BASE}/en/privacy.html", f"{BASE}/items/", f"{BASE}/en/items/"]
    urls += [f"{BASE}/items/{row['slug']}/" for row in rows] + [f"{BASE}/en/items/{row['slug']}/" for row in rows]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{esc(url)}</loc></url>\n" for url in urls) + "</urlset>\n"
    write(ROOT / "sitemap.xml", sitemap)
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    print(f"Generated {len(rows) * 2} detail pages, 2 indexes, and {len(urls)} sitemap URLs.")


if __name__ == "__main__":
    main()
