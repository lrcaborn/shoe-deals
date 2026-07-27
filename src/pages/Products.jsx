import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api.js'
import DealCard from '../components/DealCard.jsx'
import FilterBar from '../components/FilterBar.jsx'

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ page: 1 })
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const fetchProducts = useCallback(() => {
    setLoading(true)
    setError(null)
    api.products({ ...filters, q: search || undefined })
      .then((r) => setProducts(r.data || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [filters, search])

  useEffect(() => {
    fetchProducts()
  }, [fetchProducts])

  function handleSearch(e) {
    e.preventDefault()
    setSearch(searchInput)
    setFilters((f) => ({ ...f, page: 1 }))
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Browse Running Shoes</h1>
        <p className="text-gray-500 text-sm mt-1">All shoes across 12 Toronto-area retailers.</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="search"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name, e.g. Pegasus, Clifton..."
          className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
        >
          Search
        </button>
      </form>

      <FilterBar filters={filters} onChange={setFilters} />

      {loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-72 animate-pulse" />
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="text-center py-16 text-red-500">{error}</div>
      )}

      {!loading && !error && products.length === 0 && (
        <div className="text-center py-16 text-gray-400">No products found.</div>
      )}

      {!loading && !error && products.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((p) => (
              <DealCard
                key={p.id}
                deal={{
                  id: p.id,
                  name: p.name,
                  brand: p.brand,
                  image_url: p.image_url,
                  url: p.url,
                  current_price: p.latest_price?.sale_price ?? p.latest_price?.price,
                  previous_price: null,
                  retailer_name: p.retailer?.name,
                }}
              />
            ))}
          </div>

          <div className="flex justify-center gap-3 mt-8">
            {filters.page > 1 && (
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
              >
                Previous
              </button>
            )}
            {products.length === 50 && (
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
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
