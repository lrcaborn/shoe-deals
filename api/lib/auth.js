import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
)

/**
 * Validates a Supabase JWT from the Authorization header.
 * Returns the authenticated user object, or throws a 401 response.
 *
 * @param {Request} req - Vercel request object
 * @returns {Promise<{id: string, email: string}>}
 */
export async function requireAuth(req) {
  const authHeader = req.headers['authorization'] || req.headers['Authorization'] || ''
  const token = authHeader.replace(/^Bearer\s+/i, '').trim()

  if (!token) {
    const err = new Error('Missing authorization token')
    err.status = 401
    throw err
  }

  const { data, error } = await supabase.auth.getUser(token)

  if (error || !data?.user) {
    const err = new Error('Invalid or expired token')
    err.status = 401
    throw err
  }

  return data.user
}

/**
 * Returns a Supabase client authenticated as the given user (via JWT).
 * Useful for RLS-gated queries.
 */
export function getAuthedSupabase(token) {
  return createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_ANON_KEY,
    { global: { headers: { Authorization: `Bearer ${token}` } } }
  )
}

export { supabase }
