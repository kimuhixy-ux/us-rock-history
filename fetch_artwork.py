#!/usr/bin/env python3
# fetch_artwork.py: MusicBrainzのCover Art Archive (coverartarchive.org) から
# アルバムジャケット画像のURLを取得し、data/artists.json の各アルバムに
# "artwork" フィールドとして追加するスクリプト。
#
# Cover Art Archiveは認証不要・無料で使えるMusicBrainz公式の画像アーカイブ。
# release-group単位のIDで画像の有無を問い合わせられる(backfill_release_group_ids.py
# で事前に追記した release_group_mbid を使う)。
#
# 画像そのものはダウンロードせず、coverartarchive.org上のURLだけを保存する。
# HEADリクエストで画像の有無だけを確認する(存在すれば302リダイレクト、
# 無ければ404が返る)。

import argparse
import json
import os
import time
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTISTS_PATH = os.path.join(BASE_DIR, "data", "artists.json")
PROGRESS_PATH = os.path.join(BASE_DIR, "data", "artwork_progress.json")

USER_AGENT = "us-rock-history/1.0 ( us-rock-history-app@example.com )"
REQUEST_INTERVAL = 1.0  # Cover Art ArchiveもMusicBrainz系サービスのため1秒1リクエストに制限

_last_request_time = 0.0


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """リダイレクトを自動追跡しない。

    coverartarchive.org は画像があると archive.org 上の実ファイルへ
    307リダイレクトする。urllibのデフォルト挙動でこれを自動追跡すると
    archive.org側がHEADリクエストを受け付けず500エラーになるため、
    リダイレクト先URL(Locationヘッダー)だけを取り出して使う。
    """

    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def check_artwork_url(release_group_mbid):
    """release-group IDに紐づくジャケット画像の有無を確認する。
    あればURLを返し、無ければNoneを返す。"""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)

    url = f"https://coverartarchive.org/release-group/{release_group_mbid}/front-250"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="HEAD")

    for attempt in range(3):
        try:
            with _opener.open(req, timeout=15) as resp:
                _last_request_time = time.time()
                return resp.geturl()
        except urllib.error.HTTPError as e:
            _last_request_time = time.time()
            if e.code in (307, 302, 301):
                return e.headers.get("Location")
            if e.code == 404:
                return None
            if e.code == 503:
                print("  レート制限、3秒待機します…")
                time.sleep(3)
                continue
            print(f"  APIエラー(HTTP {e.code}): {release_group_mbid}")
            return None
        except Exception:
            print("  通信エラー、3秒待機してリトライします…")
            time.sleep(3)
    _last_request_time = time.time()
    return None


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test", "full"], default="test")
    parser.add_argument("--limit", type=int, default=5, help="testモードで処理するアーティスト数")
    args = parser.parse_args()

    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    done_keys = load_progress()
    target_artists = artists[: args.limit] if args.mode == "test" else artists

    # release_group_mbidを持つアルバムだけが対象
    total_albums = sum(
        1
        for a in target_artists
        for al in a.get("albums", [])
        if al.get("release_group_mbid")
    )

    processed = 0
    found = 0
    not_found = 0
    skipped_no_mbid = 0
    start_time = time.time()

    for artist in target_artists:
        for i, album in enumerate(artist.get("albums", [])):
            rg_id = album.get("release_group_mbid")
            if not rg_id:
                skipped_no_mbid += 1
                continue

            # 同名タイトルのアルバムが複数ある場合に2作目以降が
            # 処理済みと誤認されないよう、インデックスもキーに含める
            key = f"{artist['mbid']}::{i}::{album['title']}"
            processed += 1

            if key in done_keys:
                continue

            artwork_url = check_artwork_url(rg_id)
            if artwork_url:
                album["artwork"] = artwork_url
                found += 1
            else:
                album["artwork"] = None
                not_found += 1

            done_keys.add(key)

            if processed % 20 == 0 or processed == total_albums:
                save_artists(artists)
                save_progress(done_keys)
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = total_albums - processed
                eta_min = (remaining / rate / 60) if rate > 0 else 0
                print(
                    f"[{processed}/{total_albums}] 見つかった:{found} "
                    f"見つからない:{not_found} 残り目安:{eta_min:.1f}分"
                )

    save_artists(artists)
    save_progress(done_keys)

    print(
        f"=== 完了: {found}枚のジャケットを取得、{not_found}枚は見つかりませんでした "
        f"(mbid未取得のためスキップ:{skipped_no_mbid}枚) ==="
    )


if __name__ == "__main__":
    main()
