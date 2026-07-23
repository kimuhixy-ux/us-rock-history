#!/usr/bin/env python3
# backfill_person_begin_year.py: data/artists.json 内の個人ミュージシャン(type: "person")の
# begin_year を、生年(MusicBrainzのlife-span.begin由来)から
# 最初のスタジオアルバムのリリース年に修正するスクリプト。
#
# fetch_data.py はもともとPersonエンティティのlife-span.beginを
# begin_yearとして保存していたが、これは生年月日であり、年代のグループ分け
# (年表の年代別セクションなど)には不適切だった。すでにalbumsに年データを
# 保存済みなので、API通信なしでその場で再計算できる。

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTISTS_PATH = os.path.join(BASE_DIR, "data", "artists.json")


def main():
    with open(ARTISTS_PATH, encoding="utf-8") as f:
        artists = json.load(f)

    fixed = 0
    unknown = 0
    for artist in artists:
        if artist.get("type") != "person":
            continue
        album_years = [a["year"] for a in artist.get("albums", []) if a.get("year")]
        new_begin_year = min(album_years) if album_years else None
        if new_begin_year != artist.get("begin_year"):
            print(f"  {artist['name']}: {artist.get('begin_year')} -> {new_begin_year}")
            artist["begin_year"] = new_begin_year
            fixed += 1
        if new_begin_year is None:
            unknown += 1

    tmp_path = ARTISTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, ARTISTS_PATH)

    print(f"=== 完了: {fixed}件を修正、{unknown}件は該当アルバムなしのため不明(None) ===")


if __name__ == "__main__":
    main()
