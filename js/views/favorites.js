// favorites.js: お気に入り一覧(localStorage)

import { loadData, getFavorites } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";
import { S } from "../strings.js";

export async function renderFavorites(view) {
  view.innerHTML = `<div class="loading">${S.loading}</div>`;
  const { artists } = await loadData();
  const favIds = new Set(getFavorites());
  const favArtists = artists.filter((a) => favIds.has(a.mbid)).sort((a, b) => a.name.localeCompare(b.name));

  view.innerHTML = `
    <h1 class="page-title">${S.favoritesTitle}</h1>
    <p class="page-lead">${S.favoritesLead}</p>
    ${favArtists.length
      ? `<div class="artist-grid">${favArtists.map((a) => artistCardHtml(a)).join("")}</div>`
      : `<p class="empty-hint">${S.favoritesEmpty}</p>`}
  `;
}
