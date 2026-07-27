/**
 * API client — all data requests go through /api/*.
 * Never imports Supabase; never constructs direct database queries.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = new Error(body.error || `HTTP ${res.status}`)
    err.status = res.status
    throw err
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  deals: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null))
    ).toString()
    return apiFetch(`/api/deals${qs ? `?${qs}` : ''}`)
  },

  products: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null))
    ).toString()
    return apiFetch(`/api/products${qs ? `?${qs}` : ''}`)
  },

  product: (id) => apiFetch(`/api/products/${id}`),

  productHistory: (id) => apiFetch(`/api/products/${id}/history`),

  retailers: () => apiFetch('/api/retailers'),

  watchlist: {
    get: (token) => apiFetch('/api/watchlist', { token }),
    add: (token, product_id, target_price) =>
      apiFetch('/api/watchlist', {
        method: 'POST',
        token,
        body: JSON.stringify({ product_id, target_price }),
      }),
    remove: (token, id) =>
      apiFetch(`/api/watchlist/${id}`, { method: 'DELETE', token }),
  },
}
