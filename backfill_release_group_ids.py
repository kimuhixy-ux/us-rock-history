#!/usr/bin/env python3
# backfill_release_group_ids.py: data/artists.json の各アルバムに
# MusicBrainzのrelease-group ID(release_group_mbid)を追記するスクリプト。
#
# fetch_data.py 実行時にはタイトルと年だけを保存していたが、
# Cover Art Archive でジャケット画像を探すには release-group ID が必要。
#
# アーティスト単位で全アルバムを再検索して突き合わせる方式だと、
# MusicBrainzの検索インデックス(関連度ランキング)の揺れにより
# 一部のアルバムが結果に出てこないことがあったため、
# 「アルバムタイトルを直接検索してIDを1件特定する」方式にしている。

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTISTS_PATH = os.path.join(BASE_DIR, "data", "artists.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "data", "backfill_progress.json")

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0  # MusicBrainzのマナーとして1秒1リクエストに制限

_last_request_time = 0.0


def api_get(path, params):
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)

    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                _last_request_time = time.time()
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 503:
                print("  レート制限、3秒待機します…")
                time.sleep(3)
                continue
            print(f"  APIエラー(HTTP {e.code}): {url}")
            _last_request_time = time.time()
            return None
        except Exception:
            print("  通信エラー、3秒待機してリトライします…")
            time.sleep(3)
    _last_request_time = time.time()
    return None


def normalize(s):
    return "".join(c for c in s.lower() if c.isalnum())


def find_release_group_id(artist_mbid, album_title, album_year=None):
    """アーティストIDとアルバムタイトルから、release-group IDを1件特定する。

    Peter Gabriel の初期4作(すべて "Peter Gabriel" というタイトル)のように
    同じアーティストが同名タイトルのアルバムを複数出している場合、
    タイトル一致だけでは区別できない。album_year が与えられていれば
    first-release-date の年で絞り込み、正しい方を選ぶ。
    """
    safe_title = album_title.replace('"', "")
    query = f'"{safe_title}" AND arid:{artist_mbid} AND primarytype:Album'
    data = api_get("/release-group", {"query": query, "limit": 10, "offset": 0})
    if not data:
        return None

    groups = data.get("release-groups", [])
    if not groups:
        return None

    target = normalize(album_title)
    candidates = []
    for g in groups:
        title_norm = normalize(g.get("title", ""))
        if title_norm == target:
            score = 2
        elif target in title_norm or title_norm in target:
            score = 1
        else:
            score = 0
        if score > 0:
            candidates.append((score, g))

    if not candidates:
        return None

    best_score = max(c[0] for c in candidates)
    top = [g for score, g in candidates if score == best_score]

    if len(top) > 1 and album_year:
        year_matches = [
            g for g in top
            if str(g.get("first-release-date", "")).startswith(str(album_year))
        ]
        if year_matches:
            top = year_matches

    return top[0].get("id")


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(done):
    tmp_path = PROGRESS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False)
    os.replace(tmp_path, PROGRESS_PATH)


def save_artists(artists):
    tmp_path = ARTISTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, ARTISTS_PATH)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test", "full"], default="test")
    parser.add_argument("--limit", type=int, default=3, help="testモードで処理するアーティスト数")
    args = parser.parse_args()

    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    target_artists = artists[: args.limit] if args.mode == "test" else artists
    total_albums = sum(len(a.get("albums", [])) for a in target_artists)

    done = load_progress()
    processed = 0
    matched = 0
    unmatched = 0
    start_time = time.time()

    for artist in target_artists:
        for i, album in enumerate(artist.get("albums", [])):
            # タイトルだけをキーにすると、同じタイトルのアルバムが
            # 複数ある場合(例: Peter Gabriel の自主タイトル4作)に
            # 2作目以降が「処理済み」と誤認されてスキップされてしまうため、
            # リスト内のインデックスもキーに含める。
            key = f"{artist['mbid']}::{i}::{album['title']}"
            processed += 1

            if key in done:
                continue

            rg_id = find_release_group_id(artist["mbid"], album["title"], album.get("year"))
            if rg_id:
                album["release_group_mbid"] = rg_id
                matched += 1
            else:
                album["release_group_mbid"] = None
                unmatched += 1

            done.add(key)

            if processed % 10 == 0 or processed == total_albums:
                save_artists(artists)
                save_progress(done)
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = total_albums - processed
                eta_min = (remaining / rate / 60) if rate > 0 else 0
                print(f"[{processed}/{total_albums}] マッチ:{matched} 未マッチ:{unmatched} 残り目安:{eta_min:.1f}分")

    save_artists(artists)
    save_progress(done)
    print(f"=== 完了: {matched}件マッチ、{unmatched}件未マッチ ===")


if __name__ == "__main__":
    main()
