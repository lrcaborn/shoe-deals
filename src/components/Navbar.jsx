import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'

export default function Navbar() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const linkClass = ({ isActive }) =>
    `text-sm font-medium transition-colors ${
      isActive ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900'
    }`

  async function handleSignOut() {
    await signOut()
    navigate('/')
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 max-w-7xl flex items-center justify-between h-14">
        <Link to="/" className="font-bold text-lg text-blue-600 tracking-tight">
          GTA Running Deals
        </Link>

        <nav className="flex items-center gap-5">
          <NavLink to="/" end className={linkClass}>Deals</NavLink>
          <NavLink to="/products" className={linkClass}>Browse</NavLink>
          <NavLink to="/map" className={linkClass}>Map</NavLink>
          {user ? (
            <>
              <NavLink to="/watchlist" className={linkClass}>Watchlist</NavLink>
              <button
                onClick={handleSignOut}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={linkClass}>Sign in</NavLink>
              <NavLink
                to="/signup"
                className="text-sm font-medium bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors"
              >
                Sign up
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
