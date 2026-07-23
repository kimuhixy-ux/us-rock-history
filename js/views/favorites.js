// favorites.js: お気に入り一覧(localStorage)

import { loadData, getFavorites } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";

export async function renderFavorites(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const { artists } = await loadData();
  const favIds = new Set(getFavorites());
  const favArtists = artists.filter((a) => favIds.has(a.mbid)).sort((a, b) => a.name.localeCompare(b.name));

  view.innerHTML = `
    <h1 class="page-title">お気に入り</h1>
    <p class="page-lead">アーティスト詳細ページの「☆ お気に入りに追加」で登録したアーティストがここに表示されます。</p>
    ${favArtists.length
      ? `<div class="artist-grid">${favArtists.map((a) => artistCardHtml(a)).join("")}</div>`
      : `<p class="empty-hint">まだお気に入りが登録されていません。<a href="#/artists">アーティスト一覧</a>から追加してみましょう。</p>`}
  `;
}
