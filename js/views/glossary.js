// glossary.js: 用語集

import { escapeHtml } from "../router.js";

let glossaryCache = null;
async function loadGlossary() {
  if (!glossaryCache) glossaryCache = await fetch("data/glossary.json").then((r) => r.json());
  return glossaryCache;
}

export async function renderGlossary(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const terms = await loadGlossary();

  view.innerHTML = `
    <h1 class="page-title">用語集</h1>
    <p class="page-lead">アメリカのロックシーンでよく使われる用語をまとめました。</p>
    <dl>
      ${terms.map((t) => `
        <div class="glossary-item">
          <dt>${escapeHtml(t.term)}</dt>
          <dd>${escapeHtml(t.desc)}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}
