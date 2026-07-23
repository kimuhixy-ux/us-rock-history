// artist-card.js: アーティスト一覧・年表で使う共通カードHTML

import { escapeHtml } from "../router.js";

export function artistCardHtml(artist) {
  const period = artist.begin_year
    ? `${artist.begin_year}〜${artist.end_year || ""}`
    : "活動時期不明";
  const typeLabel = artist.type === "person" ? "個人" : "グループ";
  return `
    <a class="artist-card" href="#/artist/${encodeURIComponent(artist.slug)}">
      <div class="name">${escapeHtml(artist.name)}</div>
      <div class="meta">${typeLabel} ・ ${period}</div>
    </a>
  `;
}
