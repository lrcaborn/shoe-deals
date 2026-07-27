import { useState, useEffect } from 'react'
import { api } from '../lib/api.js'
import DealCard from '../components/DealCard.jsx'
import FilterBar from '../components/FilterBar.jsx'

export default function Home() {
  const [deals, setDeals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ page: 1 })

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.deals(filters)
      .then((r) => setDeals(r.data || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [filters])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Today's Running Shoe Deals</h1>
        <p className="text-gray-500 text-sm mt-1">
          Price drops from the last 24 hours across 12 Toronto-area retailers.
        </p>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      {loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-72 animate-pulse" />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="text-center py-16 text-red-500">{error}</div>
      )}

      {!loading && !error && deals.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No deals found today.</p>
          <p className="text-sm mt-1">Check back after the next scrape run (6am ET daily).</p>
        </div>
      )}

      {!loading && !error && deals.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {deals.map((deal) => (
              <DealCard key={deal.product_id || deal.id} deal={deal} />
            ))}
          </div>

          <div className="flex justify-center gap-3 mt-8">
            {filters.page > 1 && (
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
              >
                Previous
              </button>
            )}
            {deals.length === 50 && (
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
              >
                Next
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
