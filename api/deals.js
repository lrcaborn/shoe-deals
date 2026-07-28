import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from './lib/rateLimit.js'
import { applyAffiliateTag } from './lib/affiliates.js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

const MAX_ROWS = 50
const DROP_WINDOW_HOURS = 24

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!(await applyRateLimit(req, res))) return

  const { page = '1', brand, retailer_id, category } = req.query
  const pageNum = Math.max(1, parseInt(page, 10) || 1)
  const offset = (pageNum - 1) * MAX_ROWS

  const since = new Date(Date.now() - DROP_WINDOW_HOURS * 60 * 60 * 1000).toISOString()

  // Fetch products with at least 2 price_history rows in the last 24h window,
  // where the most recent price is lower than the previous.
  // We use a raw RPC call for this join-heavy query.
  const { data, error } = await supabase.rpc('get_deals', {
    p_since: since,
    p_brand: brand || null,
    p_retailer_id: retailer_id || null,
    p_category: category || null,
    p_limit: MAX_ROWS,
    p_offset: offset,
  })

  if (error) {
    console.error('deals rpc error:', error)
    return res.status(500).json({ error: 'Failed to fetch deals' })
  }

  const rows = (data || []).map((row) => ({
    ...row,
    url: applyAffiliateTag(row.url, row.retailer_name),
  }))

  return res.status(200).json({ data: rows, page: pageNum })
}
