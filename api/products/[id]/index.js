import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from '../../lib/rateLimit.js'
import { applyAffiliateTag } from '../../lib/affiliates.js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
)

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!(await applyRateLimit(req, res))) return

  const { id } = req.query

  const { data, error } = await supabase
    .from('products')
    .select(`
      id, name, brand, category, url, image_url, first_seen,
      retailer:retailers(id, name, website, lat, lng, city),
      price_history(price, sale_price, in_stock, scraped_at)
    `)
    .eq('id', id)
    .order('scraped_at', { foreignTable: 'price_history', ascending: false })
    .limit(90, { foreignTable: 'price_history' })
    .single()

  if (error || !data) {
    return res.status(404).json({ error: 'Product not found' })
  }

  const prices = data.price_history || []
  const effectivePrices = prices.map((ph) =>
    ph.sale_price != null ? ph.sale_price : ph.price
  )
  const allTimeLow = effectivePrices.length ? Math.min(...effectivePrices) : null

  return res.status(200).json({
    data: {
      ...data,
      url: applyAffiliateTag(data.url, data.retailer?.name),
      all_time_low: allTimeLow,
      current_price: effectivePrices[0] ?? null,
    },
  })
}
