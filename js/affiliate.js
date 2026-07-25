// affiliate.js: Amazonアフィリエイトリンクの生成
import { AMAZON_ASSOCIATE_TAG } from "./config.js";

export function buildAffiliateLink(asin) {
  if (!asin || !AMAZON_ASSOCIATE_TAG) return null;
  return `https://www.amazon.co.jp/dp/${encodeURIComponent(asin)}/?tag=${encodeURIComponent(AMAZON_ASSOCIATE_TAG)}`;
}
