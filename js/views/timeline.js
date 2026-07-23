// timeline.js: 年表ビュー(トップ画面)

import { loadData, decadeOf } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";

const DECADES = [
  {
    year: 1960,
    label: "1960年代",
    desc: `リヴァプールのマージービートに端を発し、ビートルズやローリング・ストーンズら
      「ブリティッシュ・インヴェイジョン」がアメリカ市場を席巻した時代。同時期、アメリカン・ブルースを
      吸収したブルースロック(ヤードバーズ、クリーム)や、サイケデリックロックの萌芽も生まれた。`,
  },
  {
    year: 1970,
    label: "1970年代",
    desc: `プログレッシブロック(キング・クリムゾン、イエス、ジェネシス)が長尺・複雑な楽曲構成で花開く一方、
      レッド・ツェッペリンやディープ・パープルらがハードロックを確立。グラムロック(T. Rex、デヴィッド・ボウイ)が
      ポップとロックの境界を揺さぶり、後半にはセックス・ピストルズらのパンクロックが既存の音楽シーンに衝撃を与えた。`,
  },
  {
    year: 1980,
    label: "1980年代",
    desc: `パンクの衝動を引き継いだポストパンク/ニューウェイヴ(ジョイ・ディヴィジョン、ザ・キュアー)が
      内省的かつ実験的なサウンドを展開。ゴシックロックが独自の美学を築く一方、アイアン・メイデンら
      NWOBHM勢がヘヴィメタルを国際的なジャンルへと押し上げた。ザ・スミスらギターポップも存在感を放った。`,
  },
  {
    year: 1990,
    label: "1990年代",
    desc: `マンチェスターを震源地に、ダンスとロックが融合した「マッドチェスター」(ストーン・ローゼズ、
      ハッピー・マンデーズ)が席巻。マイ・ブラッディ・ヴァレンタインらのシューゲイザーが音の壁を追求する中、
      オアシスやブラーらの「ブリットポップ」戦争が英国ロックを再び国民的な話題へと押し上げた。`,
  },
  {
    year: 2000,
    label: "2000年代",
    desc: `ブリットポップ以降のギターロック・リバイバルとして、アークティック・モンキーズらが
      SNS以前の口コミ文化から台頭。ミューズやコールドプレイはスタジアム規模のアリーナロックへと
      スケールアップし、英国ロックの表現の幅がさらに広がった。`,
  },
  {
    year: 2010,
    label: "2010年代",
    desc: `インディーロックがフォークやエレクトロニカと交わりながら多様化。ストリーミング時代の到来により
      シーンの境界はより流動的になり、UKロックの系譜を引き継ぐ新世代バンドが各地で生まれ続けた。`,
  },
  {
    year: 2020,
    label: "2020年代〜",
    desc: `パンデミックを経て、DIY精神やジャンル越境がより意識される時代へ。過去の名盤やアーティストの
      再評価も進み、ストリーミングを通じて世代を超えたリスナーがUKロックの歴史そのものを楽しんでいる。`,
  },
];

export async function renderTimeline(view) {
  view.innerHTML = `<div class="loading">読み込み中…</div>`;
  const { artists } = await loadData();

  const byDecade = new Map(DECADES.map((d) => [d.year, []]));
  for (const artist of artists) {
    const dec = decadeOf(artist.begin_year);
    if (dec != null && byDecade.has(dec)) {
      byDecade.get(dec).push(artist);
    } else if (dec != null && dec > 2020) {
      byDecade.get(2020).push(artist);
    }
  }

  const html = `
    <h1 class="page-title">年表</h1>
    <p class="page-lead">1960年代から現在まで、活動開始年ごとにアメリカのロックアーティストを辿れます。</p>
    ${DECADES.map((d) => {
      const list = byDecade.get(d.year).sort((a, b) => (a.begin_year - b.begin_year) || a.name.localeCompare(b.name));
      return `
        <section class="decade-block">
          <div class="decade-header">
            <span class="decade-year">${d.label}</span>
            <span class="chip">${list.length}組</span>
          </div>
          <p class="decade-desc">${d.desc.trim().replace(/\s+/g, " ")}</p>
          <div class="artist-grid">
            ${list.slice(0, 24).map((a) => artistCardHtml(a)).join("")}
          </div>
          ${list.length > 24 ? `<p style="margin-top:10px"><a href="#/artists?decade=${d.year}">この年代のアーティストをもっと見る(${list.length}組)→</a></p>` : ""}
        </section>
      `;
    }).join("")}
  `;
  view.innerHTML = html;
}
