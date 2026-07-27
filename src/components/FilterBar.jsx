import { useState, useEffect } from 'react'
import { api } from '../lib/api.js'

const BRANDS = ['ASICS', 'Brooks', 'HOKA', 'Mizuno', 'New Balance', 'Nike', 'On', 'Saucony', 'Salomon', 'Altra']
const CATEGORIES = [
  { value: 'road', label: 'Road' },
  { value: 'trail', label: 'Trail' },
  { value: 'track', label: 'Track' },
]

export default function FilterBar({ filters, onChange }) {
  const [retailers, setRetailers] = useState([])

  useEffect(() => {
    api.retailers().then((r) => setRetailers(r.data || [])).catch(() => {})
  }, [])

  const set = (key, value) => onChange({ ...filters, [key]: value || undefined, page: 1 })

  return (
    <div className="flex flex-wrap gap-3 mb-6">
      <select
        value={filters.brand || ''}
        onChange={(e) => set('brand', e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All brands</option>
        {BRANDS.map((b) => (
          <option key={b} value={b}>{b}</option>
        ))}
      </select>

      <select
        value={filters.retailer_id || ''}
        onChange={(e) => set('retailer_id', e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All retailers</option>
        {retailers.map((r) => (
          <option key={r.id} value={r.id}>{r.name}</option>
        ))}
      </select>

      <select
        value={filters.category || ''}
        onChange={(e) => set('category', e.target.value)}
        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All categories</option>
        {CATEGORIES.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>

      <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
        <input
          type="checkbox"
          checked={!!filters.in_stock}
          onChange={(e) => set('in_stock', e.target.checked ? 'true' : '')}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        In stock only
      </label>

      {Object.values(filters).some(Boolean) && (
        <button
          onClick={() => onChange({ page: 1 })}
          className="text-sm text-blue-600 hover:underline"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
