import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'
import { api } from '../lib/api.js'
import { useState } from 'react'

function formatPrice(p) {
  return `$${Number(p).toFixed(2)}`
}

export default function DealCard({ deal, onWatchlistAdd }) {
  const { user, session } = useAuth()
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)

  const dropPct = deal.drop_percent ?? Math.round(
    ((deal.previous_price - deal.current_price) / deal.previous_price) * 100
  )

  async function handleWatch(e) {
    e.preventDefault()
    if (!user) {
      window.location.href = '/login'
      return
    }
    setAdding(true)
    try {
      await api.watchlist.add(session.access_token, deal.id || deal.product_id)
      setAdded(true)
      onWatchlistAdd?.()
    } catch {
      // silently fail — user may already have it on watchlist
      setAdded(true)
    } finally {
      setAdding(false)
    }
  }

  const productId = deal.id || deal.product_id

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow flex flex-col">
      <Link to={`/products/${productId}`} className="block">
        {deal.image_url ? (
          <img
            src={deal.image_url}
            alt={deal.name}
            className="w-full h-44 object-contain bg-gray-50 p-4"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-44 bg-gray-100 flex items-center justify-center text-gray-300 text-sm">
            No image
          </div>
        )}
      </Link>

      <div className="p-4 flex flex-col flex-1 gap-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
              {deal.brand || deal.retailer_name}
            </p>
            <Link to={`/products/${productId}`}>
              <h3 className="text-sm font-semibold text-gray-800 leading-snug hover:text-blue-600">
                {deal.name}
              </h3>
            </Link>
          </div>
          <span className="shrink-0 bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded-full">
            -{dropPct}%
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-lg font-bold text-gray-900">
            {formatPrice(deal.current_price)}
          </span>
          {deal.previous_price && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(deal.previous_price)}
            </span>
          )}
        </div>

        {deal.retailer_name && (
          <p className="text-xs text-gray-400">{deal.retailer_name}</p>
        )}

        <div className="mt-auto flex gap-2">
          <a
            href={deal.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center text-sm bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            View deal
          </a>
          <button
            onClick={handleWatch}
            disabled={adding || added}
            className={`px-3 py-2 rounded-md text-sm border transition-colors ${
              added
                ? 'border-green-300 text-green-600 bg-green-50'
                : 'border-gray-300 text-gray-600 hover:border-blue-300 hover:text-blue-600'
            }`}
            title={added ? 'On your watchlist' : 'Watch this shoe'}
          >
            {added ? '✓' : '♡'}
          </button>
        </div>
      </div>
    </div>
  )
}
