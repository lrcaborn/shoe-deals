import { useEffect, useState, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api.js'

// Fix Leaflet default marker icons broken by bundlers
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const TORONTO_CENTER = [43.6532, -79.3832]
const KM_TO_M = 1000

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function RadiusCircle({ center, radiusKm }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, map.getZoom())
  }, [center, map])
  return <Circle center={center} radius={radiusKm * KM_TO_M} pathOptions={{ color: '#2563eb', fillOpacity: 0.06 }} />
}

export default function StoreMap() {
  const [retailers, setRetailers] = useState([])
  const [radiusKm, setRadiusKm] = useState(25)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.retailers()
      .then((r) => setRetailers(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const visible = retailers.filter((r) => {
    if (!r.lat || !r.lng) return false
    return haversineKm(TORONTO_CENTER[0], TORONTO_CENTER[1], r.lat, r.lng) <= radiusKm
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-600 font-medium whitespace-nowrap">
          Radius: {radiusKm} km
        </label>
        <input
          type="range"
          min={5}
          max={75}
          step={5}
          value={radiusKm}
          onChange={(e) => setRadiusKm(Number(e.target.value))}
          className="w-48 accent-blue-600"
        />
        <span className="text-sm text-gray-400">{visible.length} store{visible.length !== 1 ? 's' : ''} within radius</span>
      </div>

      {loading ? (
        <div className="h-96 bg-gray-100 rounded-xl flex items-center justify-center text-gray-400 text-sm">
          Loading map...
        </div>
      ) : (
        <div className="rounded-xl overflow-hidden border border-gray-200" style={{ height: '480px' }}>
          <MapContainer
            center={TORONTO_CENTER}
            zoom={11}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <RadiusCircle center={TORONTO_CENTER} radiusKm={radiusKm} />
            {visible.map((r) => (
              <Marker key={r.id} position={[r.lat, r.lng]}>
                <Popup>
                  <div className="text-sm">
                    <p className="font-semibold">{r.name}</p>
                    <p className="text-gray-500">{r.city}</p>
                    <a
                      href={r.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      Visit site
                    </a>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      )}
    </div>
  )
}
