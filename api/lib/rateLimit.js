import { Redis } from '@upstash/redis'

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
})

const WINDOW_SECONDS = 60
const MAX_REQUESTS = 60

/**
 * IP-based rate limiter using Upstash Redis sliding window.
 * Returns true if the request is within limits, false if it should be blocked.
 *
 * @param {Request} req - Vercel request object
 * @returns {Promise<{allowed: boolean, remaining: number, resetIn: number}>}
 */
export async function checkRateLimit(req) {
  const ip =
    req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
    req.headers['x-real-ip'] ||
    req.socket?.remoteAddress ||
    'unknown'

  const key = `rl:${ip}`
  const now = Math.floor(Date.now() / 1000)
  const windowStart = now - WINDOW_SECONDS

  const pipeline = redis.pipeline()
  pipeline.zremrangebyscore(key, 0, windowStart)
  pipeline.zadd(key, { score: now, member: `${now}-${Math.random()}` })
  pipeline.zcard(key)
  pipeline.expire(key, WINDOW_SECONDS * 2)

  const results = await pipeline.exec()
  const count = results[2]

  const allowed = count <= MAX_REQUESTS
  const remaining = Math.max(0, MAX_REQUESTS - count)
  const resetIn = WINDOW_SECONDS

  return { allowed, remaining, resetIn }
}

/**
 * Applies rate limit check and sends 429 if exceeded.
 * Returns true if the handler should continue, false if it already responded.
 */
export async function applyRateLimit(req, res) {
  try {
    const { allowed, remaining, resetIn } = await checkRateLimit(req)

    res.setHeader('X-RateLimit-Limit', MAX_REQUESTS)
    res.setHeader('X-RateLimit-Remaining', remaining)
    res.setHeader('X-RateLimit-Reset', resetIn)

    if (!allowed) {
      res.setHeader('Retry-After', resetIn)
      res.status(429).json({ error: 'Too many requests', retryAfter: resetIn })
      return false
    }
  } catch (err) {
    // Redis unavailable — fail open so the API keeps working
    console.error('Rate limit check failed:', err)
  }

  return true
}
