// data.js: JSONデータの読み込みとキャッシュ、ジャンル判定・お気に入りなどの共通ロジック

import { LOCALE, ROOT, localeDataFile } from "./i18n.js";

let cache = null;

export async function loadData() {
  if (cache) return cache;
  const [artists, genres, relations] = await Promise.all([
    fetch(`${ROOT}data/artists.json`).then((r) => r.json()),
    fetch(`${ROOT}${localeDataFile("data/genres.json")}`).then((r) => r.json()),
    fetch(`${ROOT}data/relations.json`).then((r) => r.json()),
  ]);

  const tagMap = genres.tag_map || {};
  const categoryById = new Map(genres.categories.map((c) => [c.id, c]));

  // 各アーティストのタグから正規化ジャンルIDの配列を計算しておく
  for (const artist of artists) {
    const ids = new Set();
    for (const tag of artist.tags || []) {
      const mapped = tagMap[tag.toLowerCase()];
      if (mapped) mapped.forEach((id) => ids.add(id));
    }
    if (ids.size === 0) ids.add("other");
    artist.genreIds = [...ids];
    artist.slug = slugify(artist.name);
  }

  cache = { artists, genres, relations, categoryById };
  return cache;
}

export function slugify(name) {
  return encodeURIComponent(name.trim().toLowerCase().replace(/\s+/g, "-"));
}

export function findArtistBySlug(artists, slug) {
  return artists.find((a) => a.slug === slug);
}

export function decadeOf(year) {
  if (year == null) return null;
  return Math.floor(year / 10) * 10;
}

// ===== お気に入り(localStorage) =====
const FAV_KEY = "us-rock-history:favorites";

export function getFavorites() {
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
  } catch {
    return [];
  }
}

export function isFavorite(mbid) {
  return getFavorites().includes(mbid);
}

export function toggleFavorite(mbid) {
  const favs = new Set(getFavorites());
  if (favs.has(mbid)) favs.delete(mbid);
  else favs.add(mbid);
  localStorage.setItem(FAV_KEY, JSON.stringify([...favs]));
  return favs.has(mbid);
}

// ===== 外部リンク生成 =====
export function spotifySearchUrl(query) {
  return `https://open.spotify.com/search/${encodeURIComponent(query)}`;
}

export function appleMusicSearchUrl(query) {
  const storefront = LOCALE === "en" ? "us" : "jp";
  return `https://music.apple.com/${storefront}/search?term=${encodeURIComponent(query)}`;
}

export function wikipediaUrl(name) {
  const domain = LOCALE === "en" ? "en.wikipedia.org" : "ja.wikipedia.org";
  return `https://${domain}/wiki/${encodeURIComponent(name)}`;
}
