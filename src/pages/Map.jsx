import StoreMap from '../components/StoreMap.jsx'

export default function Map() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Retailer Map</h1>
        <p className="text-gray-500 text-sm mt-1">
          Running shoe retailers in and around Toronto. Adjust the radius to find stores near you.
        </p>
      </div>
      <StoreMap />
    </div>
  )
}
