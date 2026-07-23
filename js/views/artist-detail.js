// artist-detail.js: アーティスト詳細ページ

import { loadData, findArtistBySlug, isFavorite, toggleFavorite, spotifySearchUrl, appleMusicSearchUrl, wikipediaJaUrl } from "../data.js";
import { escapeHtml } from "../router.js";

export async function renderArtistDetail(view, slug) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const { artists, genres, categoryById } = await loadData();
  const artist = findArtistBySlug(artists, slug);

  if (!artist) {
    view.innerHTML = `<div class="empty-state">アーティストが見つかりませんでした。<br><a href="#/artists">一覧に戻る</a></div>`;
    return;
  }

  const typeLabel = artist.type === "person" ? "個人" : "グループ";
  const period = `${artist.begin_year ?? "不明"} 〜 ${artist.end_year ?? "現在"}`;
  const genreLabels = artist.genreIds.map((id) => categoryById.get(id)?.label).filter(Boolean);

  view.innerHTML = `
    <p><a href="#/artists">← アーティスト一覧に戻る</a></p>
    <div class="detail-header">
      <h1>${escapeHtml(artist.name)}</h1>
      <div class="detail-meta">
        <span class="chip">${typeLabel}</span>
        <span class="chip">${period}</span>
        ${artist.area ? `<span class="chip">${escapeHtml(artist.area)}</span>` : ""}
        ${genreLabels.map((g) => `<span class="chip">${escapeHtml(g)}</span>`).join("")}
      </div>
      <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <button class="btn fav ${isFavorite(artist.mbid) ? "is-active" : ""}" id="favBtn">
          ${isFavorite(artist.mbid) ? "★ お気に入り解除" : "☆ お気に入りに追加"}
        </button>
        <a class="btn" href="${wikipediaJaUrl(artist.name)}" target="_blank" rel="noopener">Wikipedia(日本語版)</a>
        <a class="btn" href="${spotifySearchUrl(artist.name)}" target="_blank" rel="noopener">Spotifyで検索</a>
        <a class="btn" href="${appleMusicSearchUrl(artist.name)}" target="_blank" rel="noopener">Apple Musicで検索</a>
      </div>
    </div>

    <h2 style="margin-top:28px; font-size:16px;">スタジオ・ディスコグラフィ(${artist.albums.length}枚)</h2>
    <div class="discography">
      ${artist.albums.length ? artist.albums.map((al) => albumRowHtml(artist, al)).join("") : `<p class="empty-hint">登録されているスタジオアルバムがありません。</p>`}
    </div>
  `;

  view.querySelector("#favBtn").addEventListener("click", (e) => {
    const active = toggleFavorite(artist.mbid);
    e.target.classList.toggle("is-active", active);
    e.target.textContent = active ? "★ お気に入り解除" : "☆ お気に入りに追加";
  });
}

function albumRowHtml(artist, album) {
  const query = `${artist.name} ${album.title}`;
  const artwork = album.artwork
    ? `<img class="album-artwork" src="${escapeHtml(album.artwork)}" alt="" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'), {className: 'album-artwork album-artwork-placeholder'}))">`
    : `<div class="album-artwork album-artwork-placeholder"></div>`;
  return `
    <div class="album-row">
      ${artwork}
      <div class="album-info">
        <span class="album-title">${escapeHtml(album.title)}</span>
        <span class="album-year">${album.year ?? "年不明"}</span>
        ${album.personnel
          ? `<div class="personnel" style="margin-top:4px; font-size:0.85em; color:var(--text-dim);">参加ミュージシャン: ${escapeHtml(album.personnel)}</div>`
          : album.lineup
          ? `<div class="personnel" style="margin-top:4px; font-size:0.85em; color:var(--text-dim);">推定メンバー(発売年の在籍期間より): ${escapeHtml(album.lineup)}</div>`
          : ""}
        ${tracklistHtml(album)}
      </div>
      <div class="album-links">
        <a href="${spotifySearchUrl(query)}" target="_blank" rel="noopener">Spotify</a>
        <a href="${appleMusicSearchUrl(query)}" target="_blank" rel="noopener">Apple Music</a>
      </div>
    </div>
  `;
}

function tracklistHtml(album) {
  if (!album.tracks || !album.tracks.length) return "";
  const items = album.tracks
    .map((t) => `<li>${escapeHtml(t.title)}${t.length ? ` <span class="track-length">${escapeHtml(t.length)}</span>` : ""}</li>`)
    .join("");
  return `
    <details class="tracklist">
      <summary>収録曲(${album.tracks.length}曲)</summary>
      <ol>${items}</ol>
    </details>
  `;
}
