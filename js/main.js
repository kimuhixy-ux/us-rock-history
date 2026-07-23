// main.js: アプリのエントリーポイント。ルーティングとナビゲーションの初期化を行う

import { addRoute, startRouter } from "./router.js";
import { renderTimeline } from "./views/timeline.js";
import { renderArtists } from "./views/artists.js";
import { renderArtistDetail } from "./views/artist-detail.js";
import { renderGenres } from "./views/genres.js";
import { renderRelations } from "./views/relations.js";
import { renderGuide } from "./views/guide.js";
import { renderGlossary } from "./views/glossary.js";
import { renderFavorites } from "./views/favorites.js";
import { renderStats } from "./views/stats.js";

addRoute(/^#\/timeline$/, renderTimeline);
addRoute(/^#\/artists(?:\?(.*))?$/, renderArtists);
addRoute(/^#\/artist\/([^/]+)$/, renderArtistDetail);
addRoute(/^#\/genres$/, renderGenres);
addRoute(/^#\/relations$/, renderRelations);
addRoute(/^#\/guide$/, renderGuide);
addRoute(/^#\/glossary$/, renderGlossary);
addRoute(/^#\/favorites$/, renderFavorites);
addRoute(/^#\/stats$/, renderStats);
addRoute(/^#\/?$/, renderTimeline);

startRouter();

// モバイル用ナビの開閉
const navToggle = document.getElementById("navToggle");
const mainNav = document.getElementById("mainNav");
navToggle.addEventListener("click", () => {
  const open = mainNav.classList.toggle("open");
  navToggle.setAttribute("aria-expanded", String(open));
});
mainNav.addEventListener("click", (e) => {
  if (e.target.tagName === "A") {
    mainNav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
  }
});

// Service Workerの登録(オフライン対応)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((err) => {
      console.warn("Service Workerの登録に失敗しました:", err);
    });
  });
}
