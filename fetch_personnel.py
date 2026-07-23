#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us-rock-history: MusicBrainzの参加ミュージシャン(パフォーマー)情報を取得し、
data/artists.json の各アルバムに "personnel" フィールドとして追加するスクリプト。

各アルバムの release_group_mbid (backfill_release_group_ids.py で付与済み) を使い、
そのリリースグループに属するリリースをブラウズし、レコーディング単位の
アーティスト・リレーション(演奏者・ヴォーカル・ゲスト参加など)を集計する。
バンドの正規メンバーもゲストミュージシャンも同じリレーション情報として
扱われるため、区別なく「参加ミュージシャン」としてまとめて表示する。

MusicBrainzはコミュニティ編集のデータベースのため、リレーション情報が
登録されていないリリースも多い。見つからない場合は personnel を null のまま
にし、存在しないデータを捏造しない。

途中で中断しても data/personnel_progress.json に進捗が保存されているので、
同じコマンドを再実行すれば続きから再開される。

使い方:
  python3 fetch_personnel.py --mode test --limit 3
  python3 fetch_personnel.py --mode full
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTISTS_PATH = os.path.join(BASE_DIR, "data", "artists.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "data", "personnel_progress.json")

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0  # MusicBrainzのマナーとして1秒1リクエストに制限

_last_request_ts = [0.0]

RELEVANT_RELATION_TYPES = {"instrument", "vocal", "performer", "conductor"}

# MusicBrainzの属性名(英語) -> 略称。無い場合はそのまま(小文字)を使う。
INSTRUMENT_ABBR = {
    "vocals": "vo", "lead vocals": "vo", "background vocals": "cho",
    "spoken vocals": "narration",
    "trumpet": "tp", "cornet": "cornet", "flugelhorn": "flh",
    "trombone": "tb", "bass trombone": "b-tb",
    "clarinet": "cl", "bass clarinet": "b-cl",
    "saxophone": "sax", "soprano saxophone": "ss", "alto saxophone": "as",
    "tenor saxophone": "ts", "baritone saxophone": "bs",
    "flute": "fl", "piccolo": "picc", "oboe": "ob", "bassoon": "bsn",
    "piano": "p", "electric piano": "ep", "organ": "org",
    "keyboard": "kbd", "synthesizer": "syn", "mellotron": "mellotron",
    "harpsichord": "harpsichord", "celesta": "celesta",
    "guitar": "g", "electric guitar": "g", "acoustic guitar": "ag",
    "twelve-string guitar": "12-string g", "slide guitar": "slide g",
    "banjo": "banjo", "ukulele": "uke", "mandolin": "mandolin", "sitar": "sitar",
    "double bass": "b", "bass guitar": "b", "electric bass guitar": "b",
    "drums (drum set)": "ds", "drum kit": "ds", "drums": "ds",
    "percussion": "perc", "vibraphone": "vib", "marimba": "marimba",
    "tambourine": "tambourine", "timpani": "timpani",
    "conductor": "cond", "arranger": "arr", "producer": "prod",
    "violin": "vln", "viola": "vla", "cello": "cello",
    "harmonica": "harmonica", "harp": "harp", "accordion": "accordion",
    "string section": "strings", "brass section": "brass",
}


def log(msg):
    print(msg, flush=True)


def abbreviate(attr):
    return INSTRUMENT_ABBR.get(attr, attr)


def api_get(path, params, retries=3):
    elapsed = time.time() - _last_request_ts[0]
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)

    query = dict(params)
    query["fmt"] = "json"
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                _last_request_ts[0] = time.time()
                return data
        except urllib.error.HTTPError as e:
            last_err = e
            _last_request_ts[0] = time.time()
            if e.code == 503:
                time.sleep(3)
                continue
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(3)
            continue
    raise RuntimeError(f"APIリクエストに失敗しました: {url} ({last_err})")


def get_releases_for_group(rg_mbid):
    """release-groupに属するリリースを、レコーディング単位のアーティスト・
    リレーション込みで取得する(1リクエストで完結させるため limit で数件のみ)。"""
    data = api_get("/release", {
        "release-group": rg_mbid,
        "inc": "recordings+artist-credits+artist-rels+recording-level-rels",
        "limit": 3,
    })
    if not data:
        return []
    return data.get("releases", [])


def extract_personnel(release):
    """1リリース分のレスポンスから参加ミュージシャンを集計し、
    "Name (abbr, abbr), Name2 (abbr)" 形式の文字列にする。見つからなければ None。"""
    people = {}
    order = []

    def add(name, attrs):
        if name not in people:
            people[name] = []
            order.append(name)
        for a in attrs:
            if a not in people[name]:
                people[name].append(a)

    for rel in release.get("relations", []) or []:
        if rel.get("target-type") != "artist" or rel.get("type") not in RELEVANT_RELATION_TYPES:
            continue
        artist = rel.get("artist") or {}
        name = artist.get("name")
        if name:
            add(name, rel.get("attributes") or [])

    for medium in release.get("media", []) or []:
        for track in medium.get("tracks", []) or []:
            recording = track.get("recording") or {}
            for rel in recording.get("relations", []) or []:
                if rel.get("target-type") != "artist" or rel.get("type") not in RELEVANT_RELATION_TYPES:
                    continue
                artist = rel.get("artist") or {}
                name = artist.get("name")
                if name:
                    add(name, rel.get("attributes") or [])

    if not people:
        return None

    parts = []
    for name in order:
        abbrs = []
        for a in people[name]:
            ab = abbreviate(a)
            if ab not in abbrs:
                abbrs.append(ab)
        parts.append(f"{name} ({', '.join(abbrs)})" if abbrs else name)
    return ", ".join(parts)


def fetch_personnel_for_release_group(rg_mbid):
    """複数リリース候補の中から、最も多くの参加者情報が取れたものを採用する。"""
    releases = get_releases_for_group(rg_mbid)
    best = None
    best_count = 0
    for release in releases:
        personnel = extract_personnel(release)
        if personnel is None:
            continue
        count = personnel.count(",") + 1
        if count > best_count:
            best = personnel
            best_count = count
    return best


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(done_keys):
    tmp_path = PROGRESS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(sorted(done_keys), f, ensure_ascii=False)
    os.replace(tmp_path, PROGRESS_PATH)


def save_artists(artists):
    tmp_path = ARTISTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, ARTISTS_PATH)


def main():
    parser = argparse.ArgumentParser(description="us-rock-history 参加ミュージシャン取得スクリプト")
    parser.add_argument("--mode", choices=["test", "full"], default="test")
    parser.add_argument("--limit", type=int, default=3, help="testモードで処理するアルバム数")
    args = parser.parse_args()

    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    done_keys = load_progress()

    targets = []
    for artist in artists:
        for i, album in enumerate(artist.get("albums", [])):
            rg_id = album.get("release_group_mbid")
            if rg_id:
                targets.append((artist, i, album, rg_id))

    if args.mode == "test":
        targets = targets[: args.limit]

    total = len(targets)
    processed = 0
    found = 0
    not_found = 0
    start_time = time.time()

    for artist, i, album, rg_id in targets:
        key = f"{artist['mbid']}::{i}::{album['title']}"
        processed += 1

        if key in done_keys:
            continue

        try:
            personnel = fetch_personnel_for_release_group(rg_id)
        except Exception as e:
            log(f"[{processed}/{total}] {artist['name']} - {album['title']} - エラー: {e}")
            continue

        if personnel:
            album["personnel"] = personnel
            found += 1
        else:
            album["personnel"] = None
            not_found += 1

        done_keys.add(key)
        log(f"[{processed}/{total}] {artist['name']} - {album['title']} - "
            f"{'見つかった' if personnel else '見つからない'}")

        if processed % 20 == 0 or processed == total:
            save_artists(artists)
            save_progress(done_keys)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = total - processed
            eta_min = (remaining / rate / 60) if rate > 0 else 0
            log(f"  --- 進捗保存: {processed}/{total} 見つかった:{found} "
                f"見つからない:{not_found} 残り目安:{eta_min:.1f}分 ---")

    save_artists(artists)
    save_progress(done_keys)

    log(f"\n=== 完了: {found}枚に参加ミュージシャン情報を追加、"
        f"{not_found}枚は見つかりませんでした ===")


if __name__ == "__main__":
    main()
