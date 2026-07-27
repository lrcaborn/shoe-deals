import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { useAuth } from '../lib/auth.jsx'

export default function Login() {
  const { user, supabase } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) navigate('/watchlist', { replace: true })
  }, [user, navigate])

  return (
    <div className="max-w-sm mx-auto mt-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Sign in</h1>
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['google']}
          redirectTo={window.location.origin + '/watchlist'}
          view="sign_in"
        />
      </div>
    </div>
  )
}
