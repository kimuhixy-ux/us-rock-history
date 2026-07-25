// strings.js: 日本語/英語のUI文言辞書。LOCALEに応じてSオブジェクトの値が決まる。
import { LOCALE } from "./i18n.js";

const en = LOCALE === "en";

export const S = {
  // ===== 共通 =====
  loading: en ? "Loading…" : "読み込み中…",
  notFound: en ? "Page not found" : "ページが見つかりません",
  loadError: (msg) => (en ? `An error occurred while loading: ${msg}` : `読み込みエラーが発生しました: ${msg}`),
  person: en ? "Solo" : "個人",
  group: en ? "Group" : "グループ",
  periodUnknown: en ? "Period unknown" : "活動時期不明",
  yearUnknown: en ? "Year unknown" : "年不明",
  yearUnknownShort: en ? "unknown" : "不明",
  present: en ? "present" : "現在",
  periodSeparator: en ? "–" : "〜",
  decadeLabel: (y) => (en ? `${y}s` : `${y}年代`),
  artistsCount: (n) => (en ? `${n} artists` : `${n}組`),

  // ===== timeline.js =====
  timelineTitle: en ? "Timeline" : "年表",
  timelineLead: en
    ? "Explore American rock artists by the decade they began their career, from before the 1950s to today."
    : "1950年代以前から現在まで、活動開始年ごとにアメリカのロックアーティストを辿れます。",
  seeMoreArtists: (n) => (en ? `See more artists from this era (${n}) →` : `この年代のアーティストをもっと見る(${n}組)→`),

  // ===== artists.js =====
  artistsTitle: en ? "Artists" : "アーティスト一覧",
  artistsLead: (n) => (en ? `Search and filter all ${n} American rock artists.` : `全${n}組のアメリカのロックアーティストを検索・絞り込みできます。`),
  searchPlaceholder: en ? "Search by artist name or personnel…" : "アーティスト名・参加ミュージシャン名で検索…",
  sortName: en ? "Name" : "名前順",
  sortBegin: en ? "Debut year" : "活動開始年順",
  sortAlbums: en ? "Album count" : "アルバム数順",
  typeAll: en ? "All" : "すべて",
  decadeAll: en ? "All eras" : "すべての年代",
  genreAll: en ? "All genres" : "すべてのジャンル",
  hitsCount: (n) => (en ? `${n} results` : `${n}件ヒット`),
  personnelHeading: (n) => (en ? `As featured personnel (${n} albums)` : `参加ミュージシャンとして(${n}件のアルバム)`),
  personnelHint: en
    ? "These albums matched your search in the personnel credits, not the artist name."
    : "アーティスト名ではなく、アルバムの参加ミュージシャンのクレジットが検索語と一致しています。",
  noResults: en ? "No matching artists found." : "該当するアーティストが見つかりませんでした。",
  featuredBadge: en ? "Featured" : "参加",

  // ===== artist-detail.js =====
  artistNotFound: en ? "Artist not found." : "アーティストが見つかりませんでした。",
  backToList: en ? "Back to list" : "一覧に戻る",
  backToArtists: en ? "← Back to artist list" : "← アーティスト一覧に戻る",
  favRemove: en ? "★ Remove from favorites" : "★ お気に入り解除",
  favAdd: en ? "☆ Add to favorites" : "☆ お気に入りに追加",
  wikipediaLabel: en ? "Wikipedia" : "Wikipedia(日本語版)",
  spotifySearch: en ? "Search on Spotify" : "Spotifyで検索",
  appleMusicSearch: en ? "Search on Apple Music" : "Apple Musicで検索",
  discographyHeading: (n) => (en ? `Studio Discography (${n} albums)` : `スタジオ・ディスコグラフィ(${n}枚)`),
  noAlbums: en ? "No studio albums on record." : "登録されているスタジオアルバムがありません。",
  personnelPrefix: en ? "Personnel: " : "参加ミュージシャン: ",
  lineupPrefix: en ? "Estimated lineup (based on tenure at release): " : "推定メンバー(発売年の在籍期間より): ",
  tracklistSummary: (n) => (en ? `Tracklist (${n} tracks)` : `収録曲(${n}曲)`),

  // ===== favorites.js =====
  favoritesTitle: en ? "Favorites" : "お気に入り",
  favoritesLead: en
    ? 'Artists you add via "☆ Add to favorites" on their detail page will appear here.'
    : "アーティスト詳細ページの「☆ お気に入りに追加」で登録したアーティストがここに表示されます。",
  favoritesEmpty: en
    ? 'You haven\'t added any favorites yet. Add some from the <a href="#/artists">artist list</a>.'
    : `まだお気に入りが登録されていません。<a href="#/artists">アーティスト一覧</a>から追加してみましょう。`,

  // ===== genres.js =====
  genresTitle: en ? "Genre Family Tree" : "ジャンル系統図",
  genresLead: en
    ? "How the major genres in American rock branched from one another. Tap a node to see artists in that genre."
    : "アメリカのロックシーンにおける主なジャンルの派生関係です。ノードをタップするとそのジャンルのアーティスト一覧に移動します。",
  genresSvgAriaLabel: en ? "Genre family tree diagram" : "ジャンル系統図",

  // ===== glossary.js =====
  glossaryTitle: en ? "Glossary" : "用語集",
  glossaryLead: en
    ? "Common terms used in the American rock scene."
    : "アメリカのロックシーンでよく使われる用語をまとめました。",

  // ===== guide.js =====
  guideTitle: en ? "Essential Albums" : "名盤ガイド",
  guideLead: en
    ? "Essential albums picked for each genre — a great place to start listening."
    : "ジャンルごとに選んだ代表的な名盤です。まずここから聴き始めてみてください。",
  findOnAmazon: en ? "Find on Amazon" : "CD/レコードを探す",

  // ===== relations.js =====
  relationsTitle: en ? "Member Connections" : "メンバー相関図",
  relationsLead: en
    ? "Connections between key artists and musicians. Drag nodes to move them; tap an artist in the data to open their detail page."
    : "主要アーティスト・ミュージシャン間のつながりです。ノードをドラッグで動かせます。データに含まれるアーティストはタップで詳細ページへ移動します。",

  // ===== stats.js =====
  statsTitle: en ? "Statistics" : "統計",
  statsLead: (n) => (en ? `Trends in American rock, based on all ${n} artists in the dataset.` : `収集したデータ(全${n}組)から見る、アメリカロックの傾向です。`),
  basicInfo: en ? "Overview" : "基本情報",
  albumsByDecadeHeading: en ? "Albums Released by Decade" : "年代別アルバムリリース数",
  artistsByGenreHeading: en ? "Artists by Genre" : "ジャンル別アーティスト数",

  // ===== donate.js =====
  kofiSupport: en ? "☕ Support on Ko-fi" : "☕ Ko-fiで応援する",
};
