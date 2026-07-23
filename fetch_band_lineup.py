#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us-rock-history: fetch_personnel.py で参加ミュージシャン情報が見つからなかった
アルバムに対する補完策。

MusicBrainzのアーティスト・エンティティには "member of band" というリレーションが
あり、各メンバーがバンドに在籍していた期間(開始年・終了年)が記録されている
(release単位の演奏クレジットとは別の情報源)。このリレーションを使い、
アルバムの発売年時点でバンドに在籍していたメンバーを算出し、
album["lineup"] として追加する。

これはそのアルバムのレコーディングに実際に参加したことを保証するものではなく、
「発売年時点の在籍メンバー」という別種の実データに基づく推定情報のため、
fetch_personnel.pyが求める album["personnel"](実際の演奏クレジット)とは
区別して別フィールドに格納する。アプリ側ではpersonnelが無い場合のみ
lineupを「推定メンバー」として表示する想定。

対象は type == "group" のアーティストのみ(soloアーティストには
「メンバー」という概念がないため)。

使い方:
  python3 fetch_band_lineup.py --mode test --limit 5
  python3 fetch_band_lineup.py --mode full
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
PROGRESS_PATH = os.path.join(BASE_DIR, "data", "lineup_progress.json")

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0

_last_request_ts = [0.0]

# メンバーの担当楽器以外の記述的な属性(表示からは除外する)
SKIP_ATTRS = {"original", "additional", "eponymous", "founder"}
# ツアーメンバーはスタジオ録音に参加したとは限らないため、このリレーション自体を採用しない
EXCLUDE_MEMBER_ATTRS = {"touring"}

INSTRUMENT_ABBR = {
    "vocals": "vo", "lead vocals": "vo", "background vocals": "cho",
    "guitar": "g", "electric guitar": "g", "acoustic guitar": "ag",
    "slide guitar": "slide g", "lap steel guitar": "lap steel g",
    "pedal steel guitar": "pedal steel g", "twelve-string guitar": "12-string g",
    "bass": "b", "bass guitar": "b", "electric bass guitar": "b",
    "drums (drum set)": "ds", "electronic drum set": "e-ds", "membranophone": "ds",
    "keyboard": "kbd", "piano": "p", "organ": "org", "synthesizer": "syn",
    "mellotron": "mellotron", "harpsichord": "harpsichord",
    "saxophone": "sax", "trumpet": "tp", "trombone": "tb", "clarinet": "cl",
    "violin": "vln", "viola": "vla", "cello": "cello",
    "harmonica": "harmonica", "percussion": "perc", "flute": "fl",
    "sitar": "sitar", "mandolin": "mandolin", "banjo": "banjo",
    "accordion": "accordion", "autoharp": "autoharp",
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


def fetch_band_members(artist_mbid):
    """アーティストの"member of band"リレーションを取得し、
    [(name, begin_year_or_None, end_year_or_None, ended, [instrument_attrs])...] を返す。"""
    data = api_get(f"/artist/{artist_mbid}", {"inc": "artist-rels"})
    if not data:
        return []

    members = []
    for rel in data.get("relations", []) or []:
        if rel.get("type") != "member of band":
            continue
        # target-typeがartistのはず(band -> person)
        artist = rel.get("artist") or {}
        name = artist.get("name")
        if not name:
            continue
        attrs = rel.get("attributes") or []
        if any(a in EXCLUDE_MEMBER_ATTRS for a in attrs):
            continue

        begin = rel.get("begin")
        end = rel.get("end")
        ended = bool(rel.get("ended"))
        begin_year = int(begin[:4]) if begin else None
        end_year = int(end[:4]) if end else None
        instrument_attrs = [a for a in attrs if a not in SKIP_ATTRS]
        members.append((name, begin_year, end_year, ended, instrument_attrs))
    return members


def active_members_for_year(members, year, band_begin_year, band_end_year):
    """指定した年にバンドに在籍していたメンバーを集計し、
    "Name (abbr, abbr), Name2" 形式の文字列にする。同名メンバーの複数リレーション
    (楽器を変えた等)は1人にまとめる。"""
    people = {}
    order = []

    for name, begin_year, end_year, ended, attrs in members:
        by = begin_year if begin_year is not None else (band_begin_year or 0)
        if end_year is not None:
            ey = end_year
        elif not ended:
            ey = 9999  # 現在も在籍中
        else:
            # 脱退済みだが終了年が不明("いつ抜けたか"の記録が無い)場合、
            # バンド在籍期間全体を在籍していたと仮定すると精度が落ちるため、
            # このリレーションは年判定には使わない(不確実な情報で埋めない)。
            continue

        if not (by <= year <= ey):
            continue

        if name not in people:
            people[name] = []
            order.append(name)
        for a in attrs:
            if a not in people[name]:
                people[name].append(a)

    if len(order) < 2:
        return None

    parts = []
    for name in order:
        abbrs = [abbreviate(a) for a in people[name]]
        parts.append(f"{name} ({', '.join(abbrs)})" if abbrs else name)
    return ", ".join(parts)


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
    parser = argparse.ArgumentParser(description="us-rock-history 在籍メンバー(推定lineup)取得スクリプト")
    parser.add_argument("--mode", choices=["test", "full"], default="test")
    parser.add_argument("--limit", type=int, default=5, help="testモードで処理するアーティスト数")
    args = parser.parse_args()

    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    done_keys = load_progress()

    targets = [a for a in artists if a.get("type") == "group" and a.get("mbid")]
    if args.mode == "test":
        targets = targets[: args.limit]

    total = len(targets)
    processed = 0
    artists_with_members = 0
    albums_filled = 0

    for artist in targets:
        processed += 1
        key = artist["mbid"]

        if key in done_keys:
            continue

        try:
            members = fetch_band_members(artist["mbid"])
        except Exception as e:
            log(f"[{processed}/{total}] {artist['name']} - エラー: {e}")
            continue

        done_keys.add(key)

        if not members:
            log(f"[{processed}/{total}] {artist['name']} - メンバー在籍情報なし")
        else:
            artists_with_members += 1
            filled_here = 0
            for album in artist.get("albums", []):
                if album.get("personnel") or album.get("lineup"):
                    continue
                year = album.get("year")
                if not year:
                    continue
                lineup = active_members_for_year(
                    members, year, artist.get("begin_year"), artist.get("end_year")
                )
                if lineup:
                    album["lineup"] = lineup
                    albums_filled += 1
                    filled_here += 1
            log(f"[{processed}/{total}] {artist['name']} - メンバー{len(members)}名、"
                f"{filled_here}枚に推定メンバーを反映")

        if processed % 20 == 0 or processed == total:
            save_artists(artists)
            save_progress(done_keys)
            log(f"  --- 進捗保存: {processed}/{total} ---")

    save_artists(artists)
    save_progress(done_keys)

    log(f"\n=== 完了: {artists_with_members}/{total}アーティストでメンバー在籍情報を取得、"
        f"{albums_filled}枚のアルバムに推定メンバーを反映しました ===")


if __name__ == "__main__":
    main()
