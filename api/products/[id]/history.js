import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from '../../lib/rateLimit.js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!(await applyRateLimit(req, res))) return

  const { id } = req.query

  const { data, error } = await supabase
    .from('price_history')
    .select('price, sale_price, in_stock, scraped_at')
    .eq('product_id', id)
    .order('scraped_at', { ascending: true })
    .limit(90)

  if (error) {
    console.error('history query error:', error)
    return res.status(500).json({ error: 'Failed to fetch price history' })
  }

  return res.status(200).json({ data: data || [] })
}
