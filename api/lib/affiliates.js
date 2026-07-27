/**
 * Applies affiliate tracking to product URLs at the API response layer.
 * Clean URLs are stored in the database; tags are applied here only.
 *
 * Configuration lives entirely in environment variables — no network names,
 * URL patterns, or tracking IDs appear in this file.
 *
 * One env var per retailer: AFFILIATE_<RETAILER_SLUG>
 *
 * Two template formats (set whichever your affiliate network requires):
 *
 *   Wrap format — full wrapper URL with {encoded_url} placeholder:
 *     AFFILIATE_SPORT_CHEK=https://your-network.com/click?url={encoded_url}
 *
 *   Append format — query string fragment starting with ? or &:
 *     AFFILIATE_MEC=?affid=your_id
 *     AFFILIATE_RUNNING_ROOM=?CID=your_pid
 */

function toSlug(retailerName) {
  return retailerName
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

/**
 * @param {string} url - Clean product URL from the database
 * @param {string} retailerName - Retailer name as stored in the retailers table
 * @returns {string} URL with affiliate tracking appended, or the original URL if unconfigured
 */
export function applyAffiliateTag(url, retailerName) {
  if (!url || !retailerName) return url

  const template = process.env[`AFFILIATE_${toSlug(retailerName)}`]
  if (!template) return url

  try {
    if (template.startsWith('http')) {
      // Wrap format: substitute placeholders into the wrapper URL
      return template
        .replace('{encoded_url}', encodeURIComponent(url))
        .replace('{url}', url)
    }

    if (template.startsWith('?') || template.startsWith('&')) {
      // Append format: add query params to the product URL
      const parsed = new URL(url)
      const extra = new URLSearchParams(template.replace(/^[?&]/, ''))
      extra.forEach((value, key) => parsed.searchParams.set(key, value))
      return parsed.toString()
    }

    return url
  } catch {
    return url
  }
}
