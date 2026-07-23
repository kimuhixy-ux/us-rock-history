#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us-rock-history: 個別にアーティストを1組追加するスクリプト。

fetch_data.py のシードリスト/タグ検索では拾いきれなかったアーティストを
MBIDを指定して直接追加する。fetch_data.py の build_artist_record と
同じロジック(スタジオアルバムのみ、type=Album・secondary-typeなし・
status=Official)でMusicBrainzから取得し、data/artists.json に追記する。

追加後は fetch_artwork.py / fetch_personnel.py / fetch_band_lineup.py を
通常どおり実行すれば、新規追加分だけ(既存アーティストはスキップされる)
ジャケット・参加ミュージシャン・推定メンバー情報が補完される。

使い方:
  python3 add_artist.py <mbid>
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTISTS_PATH = os.path.join(BASE_DIR, "data", "artists.json")

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0

_last_request_ts = [0.0]


def log(msg):
    print(msg, flush=True)


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
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(3)
            continue
    raise RuntimeError(f"APIリクエストに失敗しました: {url} ({last_err})")


def get_artist_detail(mbid):
    return api_get(f"/artist/{mbid}", {"inc": "tags+genres"})


def get_studio_albums(mbid):
    """fetch_data.py の get_studio_albums と同じ条件・同じ形式(release_group_mbidを含む)"""
    query = f"arid:{mbid} AND primarytype:Album AND status:Official"
    seen = {}
    offset = 0
    limit = 100
    while True:
        data = api_get("/release-group", {"query": query, "limit": limit, "offset": offset})
        groups = data.get("release-groups", [])
        for g in groups:
            if g.get("secondary-types"):
                continue
            date = g.get("first-release-date") or ""
            year = None
            if len(date) >= 4 and date[:4].isdigit():
                year = int(date[:4])
            seen[g["id"]] = {"title": g.get("title"), "year": year, "release_group_mbid": g["id"]}
        total = data.get("count", 0)
        offset += limit
        if offset >= total or not groups:
            break
    albums = list(seen.values())
    albums.sort(key=lambda a: (a["year"] is None, a["year"] or 0))
    return albums


def build_artist_record(mbid):
    detail = get_artist_detail(mbid)
    life_span = detail.get("life-span") or {}
    begin = life_span.get("begin")
    end = life_span.get("end")
    begin_year = int(begin[:4]) if begin and len(begin) >= 4 else None
    end_year = int(end[:4]) if end and len(end) >= 4 else None

    area = detail.get("area")
    area_name = area.get("name") if area else None

    a_type = detail.get("type")
    artist_type = "person" if a_type == "Person" else "group"

    tag_names = set()
    for t in (detail.get("tags") or []):
        if t.get("name"):
            tag_names.add(t["name"])
    for g in (detail.get("genres") or []):
        if g.get("name"):
            tag_names.add(g["name"])

    albums = get_studio_albums(mbid)

    if artist_type == "person":
        album_years = [a["year"] for a in albums if a.get("year")]
        begin_year = min(album_years) if album_years else None

    return {
        "mbid": mbid,
        "name": detail.get("name"),
        "type": artist_type,
        "begin_year": begin_year,
        "end_year": end_year,
        "area": area_name,
        "tags": sorted(tag_names),
        "albums": albums,
    }


def save_json(path, obj):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def main():
    if len(sys.argv) != 2:
        log("使い方: python3 add_artist.py <mbid>")
        sys.exit(1)
    mbid = sys.argv[1]

    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    if any(a["mbid"] == mbid for a in artists):
        log(f"既に登録済みです: {mbid}")
        sys.exit(0)

    record = build_artist_record(mbid)
    artists.append(record)
    save_json(ARTISTS_PATH, artists)
    log(f"追加しました: {record['name']} ({record['type']}, {record['begin_year']}〜{record['end_year']}) "
        f"- アルバム{len(record['albums'])}枚")


if __name__ == "__main__":
    main()
