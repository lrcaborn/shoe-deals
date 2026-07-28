import { createClient } from '@supabase/supabase-js'
import { applyRateLimit } from './lib/rateLimit.js'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
)

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  if (!(await applyRateLimit(req, res))) return

  const { data, error } = await supabase
    .from('retailers')
    .select('id, name, website, lat, lng, city')
    .order('name')

  if (error) {
    console.error('retailers query error:', error)
    return res.status(500).json({ error: 'Failed to fetch retailers' })
  }

  return res.status(200).json({ data: data || [] })
}
