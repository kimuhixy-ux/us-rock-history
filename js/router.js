// router.js: シンプルなハッシュルーター

import { S } from "./strings.js";

const routes = [];

export function addRoute(pattern, handler) {
  routes.push({ pattern, handler });
}

export function navigate(hash) {
  if (location.hash !== hash) location.hash = hash;
  else render();
}

export async function render() {
  const hash = location.hash || "#/timeline";
  const view = document.getElementById("view");

  for (const { pattern, handler } of routes) {
    const m = hash.match(pattern);
    if (m) {
      view.scrollTop = 0;
      window.scrollTo(0, 0);
      updateActiveNav(hash);
      try {
        await handler(view, ...m.slice(1).map((s) => (s ? decodeURIComponent(s) : s)));
      } catch (err) {
        console.error(err);
        view.innerHTML = `<div class="empty-state">${S.loadError(escapeHtml(String(err.message || err)))}</div>`;
      }
      return;
    }
  }
  view.innerHTML = `<div class="empty-state">${S.notFound}</div>`;
}

function updateActiveNav(hash) {
  const base = "#/" + hash.slice(2).split("/")[0];
  document.querySelectorAll(".main-nav a").forEach((a) => {
    a.classList.toggle("active", a.getAttribute("href") === base);
  });
}

export function startRouter() {
  window.addEventListener("hashchange", render);
  render();
}

export function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
