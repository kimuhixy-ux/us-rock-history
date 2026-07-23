// artists.js: アーティスト一覧(検索・フィルタ・並べ替え)

import { loadData } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";
import { escapeHtml } from "../router.js";

export async function renderArtists(view, queryString) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
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
    <h1 class="page-title">アーティスト一覧</h1>
    <p class="page-lead">全${artists.length}組のアメリカのロックアーティストを検索・絞り込みできます。</p>

    <div class="filter-bar">
      <input type="search" id="qInput" placeholder="アーティスト名で検索…" value="${escapeHtml(state.q)}">
      <select id="sortSelect">
        <option value="name">名前順</option>
        <option value="begin">活動開始年順</option>
        <option value="albums">アルバム数順</option>
      </select>
    </div>
    <div class="filter-row" id="typeRow"></div>
    <div class="filter-row" id="decadeRow"></div>
    <div class="filter-row" id="genreRow"></div>
    <div class="result-count" id="resultCount"></div>
    <div class="artist-grid" id="results"></div>
  `;

  const qInput = view.querySelector("#qInput");
  const sortSelect = view.querySelector("#sortSelect");
  sortSelect.value = state.sort;

  const typeRow = view.querySelector("#typeRow");
  const decadeRow = view.querySelector("#decadeRow");
  const genreRow = view.querySelector("#genreRow");
  const resultsEl = view.querySelector("#results");
  const countEl = view.querySelector("#resultCount");

  const TYPES = [["", "すべて"], ["group", "グループ"], ["person", "個人"]];
  const decades = [...new Set(artists.map((a) => a.begin_year && Math.floor(a.begin_year / 10) * 10).filter(Boolean))].sort();
  const DECADES = [["", "すべての年代"], ...decades.map((d) => [String(d), `${d}年代`])];
  const GENRES = [["", "すべてのジャンル"], ...genres.categories.map((c) => [c.id, c.label])];

  typeRow.innerHTML = TYPES.map(([v, l]) => chipHtml("type", v, l, state.type)).join("");
  decadeRow.innerHTML = DECADES.map(([v, l]) => chipHtml("decade", v, l, state.decade)).join("");
  genreRow.innerHTML = GENRES.map(([v, l]) => chipHtml("genre", v, l, state.genre)).join("");

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
    if (state.q) {
      const q = state.q.toLowerCase();
      list = list.filter((a) => a.name.toLowerCase().includes(q));
    }
    if (state.genre) list = list.filter((a) => a.genreIds.includes(state.genre));
    if (state.decade) list = list.filter((a) => a.begin_year && Math.floor(a.begin_year / 10) * 10 === Number(state.decade));
    if (state.type) list = list.filter((a) => a.type === state.type);

    list = [...list];
    if (state.sort === "begin") {
      list.sort((a, b) => (a.begin_year ?? 9999) - (b.begin_year ?? 9999) || a.name.localeCompare(b.name));
    } else if (state.sort === "albums") {
      list.sort((a, b) => b.albums.length - a.albums.length || a.name.localeCompare(b.name));
    } else {
      list.sort((a, b) => a.name.localeCompare(b.name));
    }

    countEl.textContent = `${list.length}件ヒット`;
    resultsEl.innerHTML = list.length
      ? list.map((a) => artistCardHtml(a)).join("")
      : `<p class="empty-hint">該当するアーティストが見つかりませんでした。</p>`;
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
