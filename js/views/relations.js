// relations.js: メンバー相関図(D3.js v7 force-directed graph)

import { loadData } from "../data.js";
import { escapeHtml } from "../router.js";

let d3ScriptPromise = null;
function ensureD3() {
  if (window.d3) return Promise.resolve();
  if (!d3ScriptPromise) {
    d3ScriptPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "js/vendor/d3.v7.min.js";
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }
  return d3ScriptPromise;
}

export async function renderRelations(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const [{ relations, artists }] = await Promise.all([loadData(), ensureD3()]);

  const artistByName = new Map(artists.map((a) => [a.name, a]));

  view.innerHTML = `
    <h1 class="page-title">メンバー相関図</h1>
    <p class="page-lead">主要アーティスト・ミュージシャン間のつながりです。ノードをドラッグで動かせます。データに含まれるアーティストはタップで詳細ページへ移動します。</p>
    <div class="relations-wrap">
      <svg id="relSvg"></svg>
      <div class="rel-legend">
        <span><span class="dot group"></span>グループ</span>
        <span><span class="dot person"></span>個人</span>
      </div>
    </div>
  `;

  const svgEl = view.querySelector("#relSvg");
  const width = svgEl.clientWidth || 900;
  const height = 560;

  const nodes = relations.nodes.map((n) => ({ ...n }));
  const links = relations.links.map((l) => ({ ...l }));

  const d3 = window.d3;
  const svg = d3.select(svgEl).attr("viewBox", [0, 0, width, height]);

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.id).distance(70).strength(0.5))
    .force("charge", d3.forceManyBody().strength(-140))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(28));

  const link = svg.append("g").selectAll("line")
    .data(links)
    .join("line")
    .attr("class", "rel-link");

  link.append("title").text((d) => d.label || "");

  const node = svg.append("g").selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", (d) => `rel-node ${d.type}`)
    .call(drag(simulation));

  node.append("circle").attr("r", 8);
  node.append("title").text((d) => d.name);
  node.append("text")
    .attr("x", 11)
    .attr("y", 4)
    .text((d) => d.name);

  node.style("cursor", (d) => (artistByName.has(d.name) ? "pointer" : "default"));
  node.on("click", (event, d) => {
    const artist = artistByName.get(d.name);
    if (artist) location.hash = `#/artist/${encodeURIComponent(artist.slug)}`;
  });

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    node.attr("transform", (d) => `translate(${d.x},${d.y})`);
  });

  function drag(sim) {
    function dragstarted(event, d) {
      if (!event.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x; d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) sim.alphaTarget(0);
      d.fx = null; d.fy = null;
    }
    return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
  }
}
