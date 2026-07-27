# US Rock History 名盤ガイドPSEO運用手順

精選した米国ロック名盤の日英静的ページを再生成・検証するための手順書です。生成ページは既存アプリを置き換えず、検索結果から事実情報とアプリ本体へ案内します。

## 対象データとURL

- 日本語: `data/album_guide.json`
- 英語: `data/album_guide.en.json`
- ジャンル: `data/genres.json` / `data/genres.en.json`
- 日本語URL: `/items/<artist-album-year>/`
- 英語URL: `/en/items/<artist-album-year>/`

日英各72件を18カテゴリ内の順序で対応させ、アーティスト、アルバム名、年が一致しなければ生成を停止する。slugはASCIIケバブケースとし、重複時は連番を付ける。

`data/artists.json` 内の約7,135件の取得アルバムはコンピレーション等を含む補助データであり、精査が済むまでPSEO対象にしない。

## 出力範囲

アルバム名、アーティスト名、発表年、ジャンルだけを出力する。紹介文、ジャケット画像、曲目、再生時間、音源は本文、メタ情報、OGP、JSON-LD、索引へ複製しない。SpotifyとApple Musicは検索リンクだけを設置する。

## 構造化データと配信

- アルバム: `MusicAlbum`
- アーティスト: `Person` または `MusicGroup`
- 共通: `WebSite`、`WebPage`、`BreadcrumbList`
- 索引: `CollectionPage`

アーティスト名が `data/artists.json` と完全一致する場合だけ既存種別を採用し、それ以外は `MusicGroup` とする。データにない発売種別、レーベル、録音日は推測しない。

既存の `js/ads.js`、本番ホスト判定、AdSense IDを維持する。canonicalと日英相互hreflangを設定し、OGPには共通アイコンを使う。72件×2言語、索引2ページ、既存主要6ページの合計152 URLをsitemapへ収録する。生成ページは事前キャッシュせず、HTMLナビゲーションをネットワーク優先にする。

## 再生成と検証

```sh
python3 scripts/generate_pages.py
python3 scripts/validate_generated_pages.py
git diff --check
```

`items/` と `en/items/` は手編集せず、入力データ、テンプレート、生成スクリプトを修正して再生成する。

## 公開前チェック

- [ ] 日英各72詳細ページ、索引2ページ、sitemap 152 URL
- [ ] title、description、canonical、hreflang、OGP、JSON-LDが正しい
- [ ] 紹介文、画像、曲目、音源が含まれない
- [ ] 全内部リンクの参照先が存在する
- [ ] 生成ページが事前キャッシュ対象外
- [ ] git push前にオーナーの承認を得る
