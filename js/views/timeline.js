// timeline.js: 年表ビュー(トップ画面)

import { loadData, decadeOf } from "../data.js";
import { artistCardHtml } from "../components/artist-card.js";

const DECADES = [
  {
    year: 0,
    label: "〜1950年代",
    desc: `ブルース、カントリー、ゴスペル、R&Bが混じり合う中から「ロックンロール」が生まれた黎明期。
      エルヴィス・プレスリーやチャック・ベリー、リトル・リチャードらがラジオとレコードを通じて
      若者文化に火をつけ、後のロックの語彙(ギターリフ、バックビート)の土台を築いた。`,
  },
  {
    year: 1960,
    label: "1960年代",
    desc: `ビーチ・ボーイズらのサーフロックやガレージロックが西海岸から広がる一方、ボブ・ディランの
      エレクトリック化やザ・バーズが「フォークロック」を切り開いた。サンフランシスコを震源地に
      グレイトフル・デッドやジェファーソン・エアプレインらのサイケデリックロックがカウンターカルチャーと結びつき、
      1969年のウッドストックはその世代の理想を象徴するイベントとなった。`,
  },
  {
    year: 1970,
    label: "1970年代",
    desc: `ジョニ・ミッチェルらシンガーソングライターが個人的な歌詞世界を確立する一方、
      オールマン・ブラザーズ・バンドやレーナード・スキナードら「サザンロック」が南部の風土を音楽に映した。
      エアロスミスやキッスはアリーナ規模のハードロックを確立し、後半にはザ・ストゥージズやMC5、
      ニューヨーク・ドールズらの「プロトパンク」がCBGBを拠点とするパンクロック(ラモーンズら)へとつながった。`,
  },
  {
    year: 1980,
    label: "1980年代",
    desc: `ブラック・フラッグやデッド・ケネディーズらハードコアパンクがDIY精神でシーンを牽引する一方、
      R.E.M.らが「カレッジロック」として後のインディーロックの原型を作った。モトリー・クルーやボン・ジョヴィら
      グラムメタル(ヘアメタル)がMTV時代を彩り、メタリカらスラッシュメタルがヘヴィメタルを過激化させた。`,
  },
  {
    year: 1990,
    label: "1990年代",
    desc: `シアトルを震源地に、ニルヴァーナやパール・ジャムらの「グランジ」が既存のロックシーンを
      一変させ、オルタナティブロックが一気に主流となった。その流れの中でグリーン・デイやオフスプリングらが
      「ポップパンク」を大衆化させ、若い世代の新たな入口となった。`,
  },
  {
    year: 2000,
    label: "2000年代",
    desc: `ザ・ストロークスやザ・ホワイト・ストライプスらが「ガレージ/インディーリバイバル」として
      粗削りなロックンロールを再興。同時期、ブリンク182やマイ・ケミカル・ロマンスらの
      「ポップパンク/エモ」が青春の感情を鮮烈に描き、ティーン世代の圧倒的な支持を集めた。`,
  },
  {
    year: 2010,
    label: "2010年代〜",
    desc: `ストリーミング時代の到来により、インディーロックはフォークやエレクトロニカ、R&B/ソウルとも
      交わりながら多様化。ジャンルの境界がより流動的になる中、ポップスとロックが融合する
      新しい潮流も生まれ、アメリカのロックシーンは世代を超えて聴かれ続けている。`,
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
    } else if (dec != null && dec > 2010) {
      byDecade.get(2010).push(artist);
    } else if (dec != null && dec < 1960) {
      byDecade.get(0).push(artist);
    }
  }

  const html = `
    <h1 class="page-title">年表</h1>
    <p class="page-lead">1950年代以前から現在まで、活動開始年ごとにアメリカのロックアーティストを辿れます。</p>
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
          ${list.length > 24 ? `<p style="margin-top:10px"><a href="#/artists${d.year === 0 || d.year === 2010 ? "" : `?decade=${d.year}`}">この年代のアーティストをもっと見る(${list.length}組)→</a></p>` : ""}
        </section>
      `;
    }).join("")}
  `;
  view.innerHTML = html;
}
