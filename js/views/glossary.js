// glossary.js: 用語集

import { escapeHtml } from "../router.js";
import { ROOT, localeDataFile } from "../i18n.js";
import { S } from "../strings.js";

let glossaryCache = null;
async function loadGlossary() {
  if (!glossaryCache) glossaryCache = await fetch(`${ROOT}${localeDataFile("data/glossary.json")}`).then((r) => r.json());
  return glossaryCache;
}

export async function renderGlossary(view) {
  view.innerHTML = `<div class="loading">${S.loading}</div>`;
  const terms = await loadGlossary();

  view.innerHTML = `
    <h1 class="page-title">${S.glossaryTitle}</h1>
    <p class="page-lead">${S.glossaryLead}</p>
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
