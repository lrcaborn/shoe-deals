import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/auth.jsx'
import PriceChart from '../components/PriceChart.jsx'

function formatPrice(p) {
  if (p == null) return 'N/A'
  return `$${Number(p).toFixed(2)}`
}

export default function Product() {
  const { id } = useParams()
  const { user, session } = useAuth()
  const [product, setProduct] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [targetPrice, setTargetPrice] = useState('')
  const [alertModal, setAlertModal] = useState(false)
  const [alertSaving, setAlertSaving] = useState(false)
  const [alertSaved, setAlertSaved] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([api.product(id), api.productHistory(id)])
      .then(([p, h]) => {
        setProduct(p.data)
        setHistory(h.data || [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  async function handleAddAlert(e) {
    e.preventDefault()
    if (!user) {
      window.location.href = '/login'
      return
    }
    setAlertSaving(true)
    try {
      await api.watchlist.add(
        session.access_token,
        id,
        targetPrice ? parseFloat(targetPrice) : null
      )
      setAlertSaved(true)
      setAlertModal(false)
    } catch {
      setAlertSaved(true)
      setAlertModal(false)
    } finally {
      setAlertSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="h-8 bg-gray-100 rounded animate-pulse w-2/3" />
        <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
        <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    )
  }

  if (error || !product) {
    return <div className="text-center py-16 text-red-500">{error || 'Product not found'}</div>
  }

  const currentPrice = product.current_price
  const allTimeLow = product.all_time_low

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex gap-6">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-48 h-48 object-contain bg-gray-50 rounded-lg shrink-0"
            />
          ) : (
            <div className="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center text-gray-300 shrink-0">
              No image
            </div>
          )}

          <div className="flex-1 space-y-3">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{product.brand}</p>
              <h1 className="text-xl font-bold text-gray-900 leading-tight">{product.name}</h1>
              <p className="text-sm text-gray-500 mt-1">
                Sold by{' '}
                <a href={product.retailer?.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  {product.retailer?.name}
                </a>
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <p className="text-xs text-gray-400">Current price</p>
                <p className="text-2xl font-bold text-gray-900">{formatPrice(currentPrice)}</p>
              </div>
              {allTimeLow != null && (
                <div>
                  <p className="text-xs text-gray-400">All-time low</p>
                  <p className="text-lg font-semibold text-green-600">{formatPrice(allTimeLow)}</p>
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-blue-600 text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Buy now
              </a>
              {alertSaved ? (
                <span className="text-green-600 text-sm font-medium py-2">Added to watchlist</span>
              ) : (
                <button
                  onClick={() => {
                    if (!user) { window.location.href = '/login'; return }
                    setAlertModal(true)
                  }}
                  className="border border-gray-300 text-gray-700 px-5 py-2 rounded-md text-sm font-medium hover:border-blue-400 hover:text-blue-600 transition-colors"
                >
                  Set price alert
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-800 mb-4">Price history</h2>
        <PriceChart history={history} />
      </div>

      {alertModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="text-base font-semibold text-gray-900 mb-1">Set price alert</h3>
            <p className="text-sm text-gray-500 mb-4">
              We'll email you when this shoe drops to your target price. Leave blank to alert on any drop.
            </p>
            <form onSubmit={handleAddAlert} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">Target price (CAD)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  placeholder={currentPrice ? `e.g. ${formatPrice(currentPrice * 0.8)}` : 'Optional'}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={alertSaving}
                  className="flex-1 bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {alertSaving ? 'Saving...' : 'Save alert'}
                </button>
                <button
                  type="button"
                  onClick={() => setAlertModal(false)}
                  className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-md text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
