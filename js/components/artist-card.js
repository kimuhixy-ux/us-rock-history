// artist-card.js: アーティスト一覧・年表で使う共通カードHTML

import { escapeHtml } from "../router.js";
import { S } from "../strings.js";

export function artistCardHtml(artist) {
  const period = artist.begin_year
    ? `${artist.begin_year}${S.periodSeparator}${artist.end_year || ""}`
    : S.periodUnknown;
  const typeLabel = artist.type === "person" ? S.person : S.group;
  return `
    <a class="artist-card" href="#/artist/${encodeURIComponent(artist.slug)}">
      <div class="name">${escapeHtml(artist.name)}</div>
      <div class="meta">${typeLabel} ・ ${period}</div>
    </a>
  `;
}
