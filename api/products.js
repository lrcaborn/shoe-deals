import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from './lib/rateLimit.js'
import { applyAffiliateTag } from './lib/affiliates.js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
)

const MAX_ROWS = 50

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!(await applyRateLimit(req, res))) return

  const { page = '1', q, brand, retailer_id, category, in_stock } = req.query
  const pageNum = Math.max(1, parseInt(page, 10) || 1)
  const offset = (pageNum - 1) * MAX_ROWS

  let query = supabase
    .from('products')
    .select(`
      id, name, brand, category, url, image_url, first_seen,
      retailer:retailers(id, name, website),
      latest_price:price_history(price, sale_price, in_stock, scraped_at)
    `)
    .order('scraped_at', { foreignTable: 'price_history', ascending: false })
    .limit(1, { foreignTable: 'price_history' })
    .range(offset, offset + MAX_ROWS - 1)

  if (q) {
    query = query.ilike('name', `%${q}%`)
  }
  if (brand) {
    query = query.ilike('brand', `%${brand}%`)
  }
  if (retailer_id) {
    query = query.eq('retailer_id', retailer_id)
  }
  if (category) {
    query = query.eq('category', category)
  }

  const { data, error } = await query

  if (error) {
    console.error('products query error:', error)
    return res.status(500).json({ error: 'Failed to fetch products' })
  }

  let rows = data || []

  if (in_stock === 'true') {
    rows = rows.filter((p) => p.latest_price?.[0]?.in_stock !== false)
  }

  const mapped = rows.map((p) => ({
    ...p,
    url: applyAffiliateTag(p.url, p.retailer?.name),
    latest_price: p.latest_price?.[0] || null,
  }))

  return res.status(200).json({ data: mapped, page: pageNum })
}
