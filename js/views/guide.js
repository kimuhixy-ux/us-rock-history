// guide.js: 名盤ガイド

import { loadData, spotifySearchUrl, appleMusicSearchUrl } from "../data.js";
import { escapeHtml } from "../router.js";
import { buildAffiliateLink } from "../affiliate.js";
import { ROOT, localeDataFile } from "../i18n.js";
import { S } from "../strings.js";

let guideCache = null;
async function loadGuide() {
  if (!guideCache) guideCache = await fetch(`${ROOT}${localeDataFile("data/album_guide.json")}`).then((r) => r.json());
  return guideCache;
}

export async function renderGuide(view) {
  view.innerHTML = `<div class="loading">${S.loading}</div>`;
  const [{ genres }, guide] = await Promise.all([loadData(), loadGuide()]);
  const categoryById = new Map(genres.categories.map((c) => [c.id, c]));

  const html = genres.categories
    .filter((c) => guide[c.id]?.length)
    .map((c) => {
      const albums = guide[c.id];
      return `
        <section class="guide-genre">
          <h2>${escapeHtml(c.label)}</h2>
          <p class="genre-desc">${escapeHtml(c.description || "")}</p>
          ${albums.map((al) => {
            const q = `${al.artist} ${al.album}`;
            const amazonUrl = buildAffiliateLink(al.amazon_asin);
            return `
              <div class="album-pick">
                <div class="title">${escapeHtml(al.album)} <span style="color:var(--text-dim); font-weight:400;">(${al.year})</span></div>
                <div class="artist">${escapeHtml(al.artist)}</div>
                <div class="note">${escapeHtml(al.note)}</div>
                <div class="album-links" style="margin-top:8px;">
                  <a href="${spotifySearchUrl(q)}" target="_blank" rel="noopener">Spotify</a>
                  <a href="${appleMusicSearchUrl(q)}" target="_blank" rel="noopener">Apple Music</a>
                  ${amazonUrl ? `<a href="${amazonUrl}" target="_blank" rel="sponsored noopener">${S.findOnAmazon}<span class="pr-label">PR</span></a>` : ""}
                </div>
              </div>
            `;
          }).join("")}
        </section>
      `;
    }).join("");

  view.innerHTML = `
    <h1 class="page-title">${S.guideTitle}</h1>
    <p class="page-lead">${S.guideLead}</p>
    ${html}
  `;
}
