import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'

function formatPrice(p) {
  if (p == null) return 'N/A'
  return `$${Number(p).toFixed(2)}`
}

function pctFromTarget(current, target) {
  if (!current || !target) return null
  const pct = ((current - target) / target) * 100
  return pct.toFixed(0)
}

export default function Watchlist() {
  const { session } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  function loadWatchlist() {
    setLoading(true)
    api.watchlist.get(session.access_token)
      .then((r) => setItems(r.data || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadWatchlist()
  }, [])

  async function handleRemove(id) {
    await api.watchlist.remove(session.access_token, id)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="text-center py-16 text-red-500">{error}</div>
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Your Watchlist</h1>
        <p className="text-gray-500 text-sm mt-1">
          You'll receive an email when a shoe hits your target price or drops 20%+.
        </p>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">Your watchlist is empty.</p>
          <Link to="/products" className="text-blue-600 hover:underline text-sm mt-2 inline-block">
            Browse shoes to watch
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const product = item.product
            const currentPrice = product?.current_price
            const pct = pctFromTarget(currentPrice, item.target_price)
            const hitTarget = item.target_price && currentPrice <= item.target_price

            return (
              <div
                key={item.id}
                className={`bg-white rounded-xl border p-4 flex items-center gap-4 ${
                  hitTarget ? 'border-green-300 bg-green-50' : 'border-gray-200'
                }`}
              >
                {product?.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product?.name}
                    className="w-16 h-16 object-contain bg-gray-50 rounded-lg shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 bg-gray-100 rounded-lg shrink-0" />
                )}

                <div className="flex-1 min-w-0">
                  <Link to={`/products/${product?.id}`} className="hover:text-blue-600">
                    <p className="text-xs text-gray-400">{product?.brand}</p>
                    <p className="text-sm font-semibold text-gray-800 truncate">{product?.name}</p>
                  </Link>
                  <p className="text-xs text-gray-400 mt-0.5">{product?.retailer?.name}</p>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-base font-bold text-gray-900">{formatPrice(currentPrice)}</p>
                  {item.target_price && (
                    <p className={`text-xs ${hitTarget ? 'text-green-600 font-medium' : 'text-gray-400'}`}>
                      {hitTarget
                        ? `At target ${formatPrice(item.target_price)}`
                        : `Target: ${formatPrice(item.target_price)} (${pct > 0 ? '+' : ''}${pct}%)`}
                    </p>
                  )}
                </div>

                <div className="flex gap-2 shrink-0">
                  <a
                    href={product?.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700"
                  >
                    Buy
                  </a>
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="text-xs border border-gray-300 text-gray-500 px-3 py-1.5 rounded-md hover:border-red-300 hover:text-red-500"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
