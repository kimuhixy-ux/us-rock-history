// stats.js: 統計ページ(年代別アルバムリリース数・ジャンル別アーティスト数)

import { loadData, decadeOf } from "../data.js";
import { escapeHtml } from "../router.js";

export async function renderStats(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const { artists, genres, categoryById } = await loadData();

  // 年代別アルバムリリース数
  const albumsByDecade = new Map();
  for (const artist of artists) {
    for (const album of artist.albums) {
      const dec = decadeOf(album.year);
      if (dec == null) continue;
      albumsByDecade.set(dec, (albumsByDecade.get(dec) || 0) + 1);
    }
  }
  const decadeEntries = [...albumsByDecade.entries()].sort((a, b) => a[0] - b[0]);
  const maxAlbums = Math.max(...decadeEntries.map(([, v]) => v), 1);

  // ジャンル別アーティスト数
  const artistsByGenre = new Map();
  for (const artist of artists) {
    for (const gid of artist.genreIds) {
      artistsByGenre.set(gid, (artistsByGenre.get(gid) || 0) + 1);
    }
  }
  const genreEntries = [...artistsByGenre.entries()].sort((a, b) => b[1] - a[1]);
  const maxGenre = Math.max(...genreEntries.map(([, v]) => v), 1);

  // 種別(個人/グループ)
  const groupCount = artists.filter((a) => a.type === "group").length;
  const personCount = artists.length - groupCount;

  view.innerHTML = `
    <h1 class="page-title">統計</h1>
    <p class="page-lead">収集したデータ(全${artists.length}組)から見る、アメリカロックの傾向です。</p>

    <div class="stats-grid">
      <div class="card stat-card">
        <h3>基本情報</h3>
        <div class="bar-row"><span class="bar-label">グループ</span><div class="bar-track"><div class="bar-fill" style="width:${(groupCount / artists.length) * 100}%"></div></div><span class="bar-value">${groupCount}</span></div>
        <div class="bar-row"><span class="bar-label">個人</span><div class="bar-track"><div class="bar-fill" style="width:${(personCount / artists.length) * 100}%"></div></div><span class="bar-value">${personCount}</span></div>
      </div>
    </div>

    <div class="card stat-card" style="margin-bottom:20px;">
      <h3>年代別アルバムリリース数</h3>
      ${decadeEntries.map(([dec, count]) => `
        <div class="bar-row">
          <span class="bar-label">${dec}年代</span>
          <div class="bar-track"><div class="bar-fill" style="width:${(count / maxAlbums) * 100}%"></div></div>
          <span class="bar-value">${count}</span>
        </div>
      `).join("")}
    </div>

    <div class="card stat-card">
      <h3>ジャンル別アーティスト数</h3>
      ${genreEntries.map(([gid, count]) => `
        <div class="bar-row">
          <span class="bar-label">${escapeHtml(categoryById.get(gid)?.label || gid)}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${(count / maxGenre) * 100}%"></div></div>
          <span class="bar-value">${count}</span>
        </div>
      `).join("")}
    </div>
  `;
}
