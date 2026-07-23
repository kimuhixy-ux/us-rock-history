#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
us-rock-history: MusicBrainzから収録曲(トラックリスト)情報を取得し、
data/artists.json の各アルバムに "tracks" フィールドとして追加するスクリプト。

各アルバムの release_group_mbid (backfill_release_group_ids.py で付与済み) を使い、
そのリリースグループに属するリリース候補(最大3件)をブラウズし、
最もトラック数が多いものを採用してトラックリスト(曲順・曲名・収録時間)を構築する。

MusicBrainzはコミュニティ編集のデータベースのため、トラック情報が
登録されていないリリースも多い。見つからない場合は tracks を null のまま
にし、存在しないデータを捏造しない。

途中で中断しても data/tracklist_progress.json に進捗が保存されているので、
同じコマンドを再実行すれば続きから再開される。

使い方:
  python3 fetch_tracklist.py --mode test --limit 3
  python3 fetch_tracklist.py --mode full
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
PROGRESS_PATH = os.path.join(BASE_DIR, "data", "tracklist_progress.json")

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0  # MusicBrainzのマナーとして1秒1リクエストに制限

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
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(3)
            continue
    raise RuntimeError(f"APIリクエストに失敗しました: {url} ({last_err})")


MAX_TRACKS = 40  # 通常のスタジオアルバム(2枚組含む)で現実的な曲数の上限
# ディスク数(media)は判定に使わない: 1940年代以前のSP盤(78rpm)は
# 1曲=1メディアとしてMusicBrainzに登録されているため、ディスク数だけで
# ボックスセットかどうかは判別できない(曲数のみで十分に判別できる)。


def get_releases_for_group(rg_mbid):
    """release-groupに属するリリースを、トラック情報込みで取得する
    (1リクエストで完結させるため limit を指定。件数を増やしても
    追加リクエストは発生しないため、多めに候補を確保する)。"""
    data = api_get("/release", {
        "release-group": rg_mbid,
        "inc": "recordings",
        "limit": 10,
    })
    if not data:
        return []
    return data.get("releases", [])


def format_length(ms):
    if not ms:
        return None
    total_seconds = round(ms / 1000)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def extract_tracklist(release):
    """1リリース分のレスポンスから収録曲を [{"position", "title", "length"}, ...] にする。
    トラックが無ければ None。"""
    tracks = []
    position = 0
    for medium in release.get("media", []) or []:
        for track in medium.get("tracks", []) or []:
            position += 1
            recording = track.get("recording") or {}
            title = track.get("title") or recording.get("title")
            if not title:
                continue
            length_ms = track.get("length") or recording.get("length")
            tracks.append({
                "position": position,
                "title": title,
                "length": format_length(length_ms),
            })
    return tracks or None


def fetch_tracklist_for_release_group(rg_mbid):
    """複数リリース候補の中から、通常のアルバムとして妥当な曲数に収まるもののうち、
    最もトラック数が多いものを採用する。

    まれにMusicBrainz上でrelease_group_mbidが本来のスタジオアルバムではなく
    多数ディスクのボックスセット(例: 16枚組226曲)を指してしまっているケースがある。
    そうした異常値を鵜呑みにして表示すると実態と異なるトラックリストになるため、
    曲数が一定を超える候補は除外する。該当候補が無ければ捏造せずNoneを返す。"""
    releases = get_releases_for_group(rg_mbid)
    best = None
    best_count = 0
    for release in releases:
        tracklist = extract_tracklist(release)
        if tracklist is None or len(tracklist) > MAX_TRACKS:
            continue
        if len(tracklist) > best_count:
            best = tracklist
            best_count = len(tracklist)
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
    parser = argparse.ArgumentParser(description="us-rock-history 収録曲取得スクリプト")
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
            tracklist = fetch_tracklist_for_release_group(rg_id)
        except Exception as e:
            log(f"[{processed}/{total}] {artist['name']} - {album['title']} - エラー: {e}")
            continue

        if tracklist:
            album["tracks"] = tracklist
            found += 1
        else:
            album["tracks"] = None
            not_found += 1

        done_keys.add(key)
        log(f"[{processed}/{total}] {artist['name']} - {album['title']} - "
            f"{'見つかった(' + str(len(tracklist)) + '曲)' if tracklist else '見つからない'}")

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

    log(f"\n=== 完了: {found}枚に収録曲情報を追加、"
        f"{not_found}枚は見つかりませんでした ===")


if __name__ == "__main__":
    main()
