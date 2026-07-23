// genres.js: ジャンル系統図(SVGで静的に描画)

import { loadData } from "../data.js";
import { escapeHtml } from "../router.js";

// 各ジャンルカテゴリの表示位置(SVG座標、ノード中心)。おおよそ左→右が年代の流れ、
// 上下は系統(フォーク/サーフ系・ハードロック系・パンク系)を表す。
const POSITIONS = {
  "rock-and-roll": { x: 90, y: 60 },
  "folk-rock": { x: 90, y: 320 },
  "surf-garage-rock": { x: 270, y: 60 },
  "psychedelic-rock": { x: 270, y: 190 },
  "southern-rock": { x: 270, y: 450 },
  "singer-songwriter": { x: 270, y: 320 },
  "proto-punk": { x: 450, y: 60 },
  "arena-hard-rock": { x: 450, y: 190 },
  "glam-metal": { x: 450, y: 320 },
  "punk-rock": { x: 630, y: 60 },
  "new-wave": { x: 630, y: 190 },
  "heavy-metal": { x: 630, y: 320 },
  "hardcore-punk": { x: 810, y: 60 },
  "college-rock-indie": { x: 810, y: 190 },
  "pop-punk-emo": { x: 810, y: 450 },
  "grunge": { x: 990, y: 190 },
  "alternative-rock": { x: 990, y: 320 },
  "garage-indie-revival": { x: 990, y: 450 },
  "other": { x: 90, y: 600 },
};

const NODE_W = 160;
const NODE_H = 48;

export async function renderGenres(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const { genres } = await loadData();
  const { categories, genealogy } = genres;

  const edgesSvg = genealogy.map(({ from, to }) => {
    const a = POSITIONS[from];
    const b = POSITIONS[to];
    if (!a || !b) return "";
    return `<line class="edge" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" />`;
  }).join("");

  const nodesSvg = categories.map((c) => {
    const p = POSITIONS[c.id];
    if (!p) return "";
    return `
      <g class="genre-node" data-id="${c.id}" transform="translate(${p.x - NODE_W / 2}, ${p.y - NODE_H / 2})">
        <rect width="${NODE_W}" height="${NODE_H}"></rect>
        <text x="${NODE_W / 2}" y="${NODE_H / 2 - 4}" text-anchor="middle">${wrapLabel(c.label)[0]}</text>
        <text x="${NODE_W / 2}" y="${NODE_H / 2 + 12}" text-anchor="middle">${wrapLabel(c.label)[1] || ""}</text>
      </g>
    `;
  }).join("");

  view.innerHTML = `
    <h1 class="page-title">ジャンル系統図</h1>
    <p class="page-lead">アメリカのロックシーンにおける主なジャンルの派生関係です。ノードをタップするとそのジャンルのアーティスト一覧に移動します。</p>
    <div class="genealogy-wrap">
      <svg viewBox="0 0 1080 760" width="1080" height="760" role="img" aria-label="ジャンル系統図">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0L10,5L0,10z" fill="#9a9aa8"></path>
          </marker>
        </defs>
        <g>${edgesSvg}</g>
        <g>${nodesSvg}</g>
      </svg>
    </div>
  `;

  view.querySelectorAll(".genre-node").forEach((node) => {
    node.addEventListener("click", () => {
      location.hash = `#/artists?genre=${node.dataset.id}`;
    });
  });
}

function wrapLabel(label) {
  const idx = label.indexOf(" / ");
  if (idx !== -1) return [label.slice(0, idx), label.slice(idx + 3)];
  if (label.length > 10) {
    const mid = Math.ceil(label.length / 2);
    const splitAt = label.lastIndexOf("(", mid) > 0 ? label.lastIndexOf("(", mid) : mid;
    return [label.slice(0, splitAt), label.slice(splitAt)];
  }
  return [label, ""];
}
