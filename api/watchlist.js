import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from './lib/rateLimit.js'
import { requireAuth, getAuthedSupabase } from './lib/auth.js'
import { applyAffiliateTag } from './lib/affiliates.js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

export default async function handler(req, res) {
  if (!(await applyRateLimit(req, res))) return

  let user
  try {
    user = await requireAuth(req)
  } catch (err) {
    return res.status(err.status || 401).json({ error: err.message })
  }

  const token = req.headers['authorization'].replace(/^Bearer\s+/i, '').trim()
  const authedSupabase = getAuthedSupabase(token)

  if (req.method === 'GET') {
    return handleGet(req, res, user, authedSupabase)
  } else if (req.method === 'POST') {
    return handlePost(req, res, user, authedSupabase)
  } else if (req.method === 'DELETE') {
    return handleDelete(req, res, user, authedSupabase)
  }

  return res.status(405).json({ error: 'Method not allowed' })
}

async function handleGet(req, res, user, authedSupabase) {
  const { data, error } = await authedSupabase
    .from('watchlist')
    .select(`
      id, target_price, created_at,
      product:products(
        id, name, brand, category, url, image_url,
        retailer:retailers(id, name, website),
        price_history(price, sale_price, in_stock, scraped_at)
      )
    `)
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(50)

  if (error) {
    console.error('watchlist get error:', error)
    return res.status(500).json({ error: 'Failed to fetch watchlist' })
  }

  const mapped = (data || []).map((item) => {
    const prices = item.product?.price_history || []
    const sorted = [...prices].sort(
      (a, b) => new Date(b.scraped_at) - new Date(a.scraped_at)
    )
    const latest = sorted[0]
    const currentPrice = latest
      ? (latest.sale_price ?? latest.price)
      : null

    return {
      ...item,
      product: item.product
        ? {
            ...item.product,
            url: applyAffiliateTag(item.product.url, item.product.retailer?.name),
            price_history: undefined,
            current_price: currentPrice,
          }
        : null,
    }
  })

  return res.status(200).json({ data: mapped })
}

async function handlePost(req, res, user, authedSupabase) {
  const { product_id, target_price } = req.body || {}

  if (!product_id) {
    return res.status(400).json({ error: 'product_id is required' })
  }

  // Validate product exists
  const { data: product } = await supabase
    .from('products')
    .select('id')
    .eq('id', product_id)
    .single()

  if (!product) {
    return res.status(404).json({ error: 'Product not found' })
  }

  const { data, error } = await authedSupabase
    .from('watchlist')
    .upsert(
      {
        user_id: user.id,
        product_id,
        target_price: target_price || null,
      },
      { onConflict: 'user_id,product_id' }
    )
    .select()
    .single()

  if (error) {
    console.error('watchlist post error:', error)
    return res.status(500).json({ error: 'Failed to add to watchlist' })
  }

  return res.status(201).json({ data })
}

async function handleDelete(req, res, user, authedSupabase) {
  // Extract watchlist item ID from URL: /api/watchlist/:id
  const urlParts = req.url.split('/')
  const watchlistId = urlParts[urlParts.length - 1]

  if (!watchlistId || watchlistId === 'watchlist') {
    return res.status(400).json({ error: 'Watchlist item ID required' })
  }

  // RLS ensures user can only delete their own rows
  const { error } = await authedSupabase
    .from('watchlist')
    .delete()
    .eq('id', watchlistId)
    .eq('user_id', user.id)

  if (error) {
    console.error('watchlist delete error:', error)
    return res.status(500).json({ error: 'Failed to remove from watchlist' })
  }

  return res.status(204).end()
}
