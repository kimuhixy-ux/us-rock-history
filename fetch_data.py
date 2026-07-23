#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us-rock-history: MusicBrainz APIからアメリカのロック系アーティスト情報を収集するスクリプト。

使い方:
  # 小規模テスト(シードリストの先頭10組のみ)
  python3 fetch_data.py --mode test

  # 全件取得(シードリスト + タグ検索でアメリカ出身ロック系アーティストを300組以上収集)
  python3 fetch_data.py --mode full --target 300

途中で失敗・中断しても、data/progress.json に進捗が保存されているので
同じコマンドを再実行すれば続きから再開されます(最初からやり直す場合は
data/progress.json と data/artists.json を削除してください)。
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://musicbrainz.org/ws/2"
# MusicBrainz APIの利用規約により、連絡先が分かるUser-Agentを設定する(メールはダミー)
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
ARTISTS_PATH = os.path.join(DATA_DIR, "artists.json")
PROGRESS_PATH = os.path.join(DATA_DIR, "progress.json")

REQUEST_INTERVAL = 1.0  # 秒。MusicBrainzのマナーとして1秒1リクエストに制限
_last_request_ts = [0.0]

US_AREAS = {"United States"}

# --- シードリスト: 必ず含めたい代表的アーティスト ---
SEED_ARTISTS = [
    "Elvis Presley", "Chuck Berry", "Buddy Holly", "Little Richard", "The Beach Boys",
    "Bob Dylan", "The Byrds", "Simon & Garfunkel", "The Velvet Underground", "The Doors",
    "Jimi Hendrix", "Janis Joplin", "Creedence Clearwater Revival", "Sly and the Family Stone",
    "Grateful Dead", "Jefferson Airplane", "Santana", "Crosby, Stills, Nash & Young",
    "The Allman Brothers Band", "Lynyrd Skynyrd", "ZZ Top", "Eagles", "Steely Dan",
    "Aerosmith", "Kiss", "Alice Cooper", "Boston", "Journey", "Foreigner", "Van Halen",
    "Bruce Springsteen", "Tom Petty and the Heartbreakers", "Talking Heads", "Ramones",
    "Blondie", "Patti Smith", "The Stooges", "MC5", "New York Dolls", "Television",
    "Pixies", "R.E.M.", "Sonic Youth", "Hüsker Dü", "The Replacements", "Dinosaur Jr.",
    "Guns N' Roses", "Metallica", "Nirvana", "Pearl Jam", "Soundgarden", "Alice in Chains",
    "Red Hot Chili Peppers", "Foo Fighters", "Green Day", "The White Stripes", "The Strokes",
    "Wilco", "My Chemical Romance",
]

# --- 広く収集するためのタグ検索キーワード(主要ジャンルを網羅) ---
TAG_QUERIES = [
    "rock", "rock and roll", "rockabilly", "surf rock", "garage rock", "folk rock",
    "blues rock", "psychedelic rock", "southern rock", "hard rock", "heavy metal",
    "arena rock", "glam metal", "punk", "punk rock", "hardcore punk", "post-punk",
    "new wave", "power pop", "college rock", "alternative rock", "grunge",
    "indie rock", "emo", "pop punk",
]


def log(msg):
    print(msg, flush=True)


def api_get(path, params, retries=3):
    """MusicBrainz APIにGETリクエストを送る(レート制限・リトライ付き)"""
    # レート制限: 前回のリクエストから REQUEST_INTERVAL 秒空ける
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
            if e.code == 503:
                # レート制限などで一時的に弾かれた場合は少し待って再試行
                time.sleep(3)
                continue
            else:
                _last_request_ts[0] = time.time()
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(2)
            continue
    raise RuntimeError(f"APIリクエストに失敗しました: {url} ({last_err})")


def search_artist_by_name(name):
    """名前でアーティストを検索し、最も一致度の高い候補を1件返す"""
    data = api_get("/artist", {"query": f'artist:"{name}"', "limit": 5})
    artists = data.get("artists", [])
    if not artists:
        return None
    for a in artists:
        if a.get("name", "").lower() == name.lower():
            return a
    return artists[0]


def search_artists_by_tag(tag, offset, limit=100):
    """タグ + アメリカ出身の条件でアーティストを検索する"""
    area_query = " OR ".join(f'area:"{a}"' for a in US_AREAS)
    query = f'tag:"{tag}" AND ({area_query})'
    return api_get("/artist", {"query": query, "limit": limit, "offset": offset})


def get_artist_detail(mbid):
    return api_get(f"/artist/{mbid}", {"inc": "tags+genres"})


def get_studio_albums(mbid):
    """スタジオアルバム(type=album, secondary-typeなし, status=Official)を取得。

    browseエンドポイント(artist=mbid)だとブートレグ盤も混ざってしまうため、
    検索エンドポイントで status:Official を条件に加えて絞り込む。
    検索結果はページをまたいで同じ盤が重複することがあるため release-group id で重複排除する。
    """
    query = f"arid:{mbid} AND primarytype:Album AND status:Official"
    seen = {}
    offset = 0
    limit = 100
    while True:
        data = api_get("/release-group", {"query": query, "limit": limit, "offset": offset})
        groups = data.get("release-groups", [])
        for g in groups:
            # ライブ盤・コンピレーション・サウンドトラック等(secondary-typeあり)は除外
            if g.get("secondary-types"):
                continue
            date = g.get("first-release-date") or ""
            year = None
            if len(date) >= 4 and date[:4].isdigit():
                year = int(date[:4])
            seen[g["id"]] = {"title": g.get("title"), "year": year}
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

    a_type = detail.get("type")  # "Group" / "Person" など
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
        # MusicBrainzのPersonエンティティでは life-span.begin は生年月日であり、
        # 音楽活動の開始時期(年代のグループ分けに使いたい情報)とは一致しない
        # (例: David Bowieは1947年生まれだが、活動開始は1960年代後半)。
        # そのため個人ミュージシャンは、最初のスタジオアルバムのリリース年を
        # begin_year として採用する。該当アルバムがない場合はNone(不明)とする。
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


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def collect_candidate_mbids(mode, seed_limit, target):
    """処理対象となるアーティストのMBIDリストを集める(名前とセットで返す)"""
    candidates = {}  # mbid -> name (ログ用)

    seeds = SEED_ARTISTS if mode == "full" else SEED_ARTISTS[:seed_limit]
    log(f"--- シード検索: {len(seeds)}組を名前で検索します ---")
    for name in seeds:
        result = search_artist_by_name(name)
        if result is None:
            log(f"  [警告] 見つかりませんでした: {name}")
            continue
        candidates[result["id"]] = result.get("name", name)
        log(f"  OK: {name} -> {result.get('name')}")

    if mode == "full":
        log(f"--- タグ検索: {len(TAG_QUERIES)}個のジャンルタグで追加収集します(目標 {target} 組) ---")
        for tag in TAG_QUERIES:
            if len(candidates) >= target:
                break
            offset = 0
            while len(candidates) < target:
                data = search_artists_by_tag(tag, offset)
                artists = data.get("artists", [])
                if not artists:
                    break
                for a in artists:
                    a_type = a.get("type")
                    if a_type not in ("Group", "Person"):
                        continue
                    area = a.get("area", {}) or {}
                    if area.get("name") not in US_AREAS:
                        continue
                    if a["id"] not in candidates:
                        candidates[a["id"]] = a.get("name")
                total = data.get("count", 0)
                offset += 100
                log(f"  タグ '{tag}': {len(candidates)}組まで収集(offset={offset}/{total})")
                if offset >= total:
                    break

    return candidates


def main():
    parser = argparse.ArgumentParser(description="us-rock-history データ収集スクリプト")
    parser.add_argument("--mode", choices=["test", "full"], default="test",
                         help="test: シードリスト先頭のみで動作確認 / full: 全件収集")
    parser.add_argument("--seed-limit", type=int, default=10,
                         help="testモードで処理するシードの数(デフォルト10)")
    parser.add_argument("--target", type=int, default=300,
                         help="fullモードでの目標アーティスト数(デフォルト300)")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    progress = load_json(PROGRESS_PATH, {"processed_mbids": []})
    artists = load_json(ARTISTS_PATH, [])
    processed = set(progress["processed_mbids"])

    candidates = collect_candidate_mbids(args.mode, args.seed_limit, args.target)
    total_candidates = len(candidates)
    todo = [(mbid, name) for mbid, name in candidates.items() if mbid not in processed]

    log(f"\n=== 候補アーティスト数: {total_candidates}組(未処理: {len(todo)}組) ===")
    est_seconds = len(todo) * 2  # 詳細取得+アルバム取得で概ね1組あたり2リクエスト以上
    log(f"=== 推定所要時間: 約{est_seconds // 60}分{est_seconds % 60}秒 ===\n")

    for i, (mbid, name) in enumerate(todo, 1):
        try:
            record = build_artist_record(mbid)
            artists.append(record)
            processed.add(mbid)
            n_albums = len(record["albums"])
            log(f"[{i}/{len(todo)}] {record['name']} ({record['type']}, {record['begin_year']}) "
                f"- アルバム{n_albums}枚 - OK")
        except Exception as e:
            log(f"[{i}/{len(todo)}] {name} - エラー: {e}")
            continue

        # 5組ごとに進捗を保存(中断しても再開できるように)
        if i % 5 == 0 or i == len(todo):
            progress["processed_mbids"] = sorted(processed)
            save_json(PROGRESS_PATH, progress)
            save_json(ARTISTS_PATH, artists)

    progress["processed_mbids"] = sorted(processed)
    save_json(PROGRESS_PATH, progress)
    save_json(ARTISTS_PATH, artists)

    log(f"\n=== 完了: data/artists.json に {len(artists)}組を保存しました ===")


if __name__ == "__main__":
    main()
