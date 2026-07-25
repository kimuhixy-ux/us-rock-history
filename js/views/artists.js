// artists.js: アーティスト一覧(検索・フィルタ・並べ替え)

import { loadData } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";
import { escapeHtml } from "../router.js";
import { S } from "../strings.js";

export async function renderArtists(view, queryString) {
  view.innerHTML = `<div class="loading">${S.loading}</div>`;
  const { artists, genres } = await loadData();
  const params = new URLSearchParams(queryString || "");

  const state = {
    q: params.get("q") || "",
    genre: params.get("genre") || "",
    decade: params.get("decade") || "",
    type: params.get("type") || "",
    sort: params.get("sort") || "name",
  };

  view.innerHTML = `
    <h1 class="page-title">${S.artistsTitle}</h1>
    <p class="page-lead">${S.artistsLead(artists.length)}</p>

    <div class="filter-bar">
      <input type="search" id="qInput" placeholder="${S.searchPlaceholder}" value="${escapeHtml(state.q)}">
      <select id="sortSelect">
        <option value="name">${S.sortName}</option>
        <option value="begin">${S.sortBegin}</option>
        <option value="albums">${S.sortAlbums}</option>
      </select>
    </div>
    <div class="filter-row" id="typeRow"></div>
    <div class="filter-row" id="decadeRow"></div>
    <div class="filter-row" id="genreRow"></div>
    <div class="result-count" id="resultCount"></div>
    <div class="artist-grid" id="results"></div>

    <div class="personnel-section" id="personnelSection" hidden>
      <h2 class="section-title" id="personnelHeading"></h2>
      <p class="section-hint">${S.personnelHint}</p>
      <div class="album-hit-list" id="personnelResults"></div>
    </div>
  `;

  const qInput = view.querySelector("#qInput");
  const sortSelect = view.querySelector("#sortSelect");
  sortSelect.value = state.sort;

  const typeRow = view.querySelector("#typeRow");
  const decadeRow = view.querySelector("#decadeRow");
  const genreRow = view.querySelector("#genreRow");
  const resultsEl = view.querySelector("#results");
  const countEl = view.querySelector("#resultCount");
  const personnelSection = view.querySelector("#personnelSection");
  const personnelResultsEl = view.querySelector("#personnelResults");
  const personnelHeadingEl = view.querySelector("#personnelHeading");

  const TYPES = [["", S.typeAll], ["group", S.group], ["person", S.person]];
  const decades = [...new Set(artists.map((a) => a.begin_year && Math.floor(a.begin_year / 10) * 10).filter(Boolean))].sort();
  const DECADES = [["", S.decadeAll], ...decades.map((d) => [String(d), S.decadeLabel(d)])];
  const GENRES = [["", S.genreAll], ...genres.categories.map((c) => [c.id, c.label])];

  typeRow.innerHTML = TYPES.map(([v, l]) => chipHtml("type", v, l, state.type)).join("");
  decadeRow.innerHTML = DECADES.map(([v, l]) => chipHtml("decade", v, l, state.decade)).join("");
  genreRow.innerHTML = GENRES.map(([v, l]) => chipHtml("genre", v, l, state.genre)).join("");

  function personnelSnippet(personnel, q) {
    // 括弧内(楽器名)のカンマでは分割しないよう、トップレベルのカンマのみで区切る
    const seg = personnel
      .split(/,\s*(?![^()]*\))/)
      .map((s) => s.trim())
      .find((s) => s.toLowerCase().includes(q));
    return seg || personnel;
  }

  function albumHitHtml(artist, album, q) {
    const artwork = album.artwork
      ? `<img class="album-artwork" src="${escapeHtml(album.artwork)}" alt="" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement('div'), {className: 'album-artwork album-artwork-placeholder'}))">`
      : `<div class="album-artwork album-artwork-placeholder"></div>`;
    return `
      <a class="album-row personnel-hit" href="#/artist/${encodeURIComponent(artist.slug)}">
        ${artwork}
        <div class="album-info">
          <span class="hit-badge">${S.featuredBadge}</span>
          <span class="album-title">${escapeHtml(album.title)}</span>
          <span class="album-year">${album.year ?? S.yearUnknown}</span>
          <div class="album-artist">${escapeHtml(artist.name)}</div>
          <div class="personnel-snippet">${escapeHtml(personnelSnippet(album.personnel, q))}</div>
        </div>
      </a>
    `;
  }

  function chipHtml(group, value, label, current) {
    const active = value === current ? " active" : "";
    return `<button type="button" class="chip${active}" data-group="${group}" data-value="${escapeHtml(value)}">${escapeHtml(label)}</button>`;
  }

  function syncUrl() {
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.genre) p.set("genre", state.genre);
    if (state.decade) p.set("decade", state.decade);
    if (state.type) p.set("type", state.type);
    if (state.sort !== "name") p.set("sort", state.sort);
    const qs = p.toString();
    history.replaceState(null, "", `#/artists${qs ? "?" + qs : ""}`);
  }

  function applyFilters() {
    let list = artists;
    if (state.genre) list = list.filter((a) => a.genreIds.includes(state.genre));
    if (state.decade) list = list.filter((a) => a.begin_year && Math.floor(a.begin_year / 10) * 10 === Number(state.decade));
    if (state.type) list = list.filter((a) => a.type === state.type);

    let nameMatches = list;
    let albumHits = [];
    if (state.q) {
      const q = state.q.toLowerCase();
      nameMatches = list.filter((a) => a.name.toLowerCase().includes(q));
      for (const a of list) {
        if (a.name.toLowerCase().includes(q)) continue; // リーダー本人のアルバムは「参加ミュージシャン」欄に出さない
        for (const al of a.albums || []) {
          if (al.personnel && al.personnel.toLowerCase().includes(q)) {
            albumHits.push({ artist: a, album: al });
          }
        }
      }
    }

    nameMatches = [...nameMatches];
    if (state.sort === "begin") {
      nameMatches.sort((a, b) => (a.begin_year ?? 9999) - (b.begin_year ?? 9999) || a.name.localeCompare(b.name));
    } else if (state.sort === "albums") {
      nameMatches.sort((a, b) => b.albums.length - a.albums.length || a.name.localeCompare(b.name));
    } else {
      nameMatches.sort((a, b) => a.name.localeCompare(b.name));
    }
    albumHits.sort((a, b) => a.artist.name.localeCompare(b.artist.name) || (a.album.year ?? 9999) - (b.album.year ?? 9999));

    countEl.textContent = S.hitsCount(nameMatches.length);
    resultsEl.innerHTML = nameMatches.length
      ? nameMatches.map((a) => artistCardHtml(a)).join("")
      : `<p class="empty-hint">${S.noResults}</p>`;

    personnelSection.hidden = albumHits.length === 0;
    if (albumHits.length) {
      personnelHeadingEl.textContent = S.personnelHeading(albumHits.length);
      personnelResultsEl.innerHTML = albumHits
        .map(({ artist, album }) => albumHitHtml(artist, album, state.q.toLowerCase()))
        .join("");
    }

    syncUrl();
  }

  let debounceTimer;
  qInput.addEventListener("input", () => {
    state.q = qInput.value;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 200);
  });

  sortSelect.addEventListener("change", () => {
    state.sort = sortSelect.value;
    applyFilters();
  });

  view.querySelectorAll(".chip[data-group]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const group = btn.dataset.group;
      state[group] = btn.dataset.value;
      view.querySelectorAll(`.chip[data-group="${group}"]`).forEach((b) => b.classList.toggle("active", b === btn));
      applyFilters();
    });
  });

  applyFilters();
}
