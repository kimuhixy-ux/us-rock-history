// i18n.js: URLパス(/en/を含むか)からロケールを判定する
export const LOCALE = location.pathname.includes("/en/") ? "en" : "ja";

// 相対パスの基点。/en/配下のページから見て、data/やcss/などアプリ直下のファイルは1階層上になる
export const ROOT = LOCALE === "en" ? "../" : "./";

// ja/en共通のJSONファイル名からロケール別のファイル名を作る(例: "genres.json" → "genres.en.json")
export function localeDataFile(name) {
  if (LOCALE !== "en") return name;
  return name.replace(/\.json$/, ".en.json");
}
