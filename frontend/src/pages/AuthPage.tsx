import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function AuthPage() {
  const { login, register } = useAuth()
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [username, setUser] = useState('')
  const [password, setPass] = useState('')
  const [city, setCity] = useState('上海')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError(''); setLoading(true)
    try {
      if (tab === 'login') await login(username, password)
      else await register(username, password, city)
      window.location.href = '/'
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center wave-bg px-4">
      <div className="card-travel p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <svg className="w-12 h-12 mx-auto mb-3 text-travel-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h1 className="text-xl font-bold text-gray-800">旅行 AI 助手</h1>
        </div>

        <div className="flex mb-4 bg-gray-100 rounded-lg p-0.5">
          <button className={`flex-1 py-2 rounded-md text-sm font-medium transition ${tab === 'login' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500'}`}
            onClick={() => setTab('login')}>登录</button>
          <button className={`flex-1 py-2 rounded-md text-sm font-medium transition ${tab === 'register' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500'}`}
            onClick={() => setTab('register')}>注册</button>
        </div>

        <div className="space-y-3">
          <input type="text" placeholder="用户名" value={username} onChange={e => setUser(e.target.value)} className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-travel-300" />
          <input type="password" placeholder="密码 (6位以上)" value={password} onChange={e => setPass(e.target.value)} className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-travel-300" />
          {tab === 'register' && <input type="text" placeholder="常住城市 (如上海)" value={city} onChange={e => setCity(e.target.value)} className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-travel-300" />}
          {error && <p className="text-red-500 text-xs">{error}</p>}
          <button onClick={submit} disabled={loading || !username || !password} className="w-full py-2.5 rounded-lg bg-gradient-to-r from-travel-500 to-ocean-500 text-white font-medium text-sm disabled:opacity-50 hover:shadow-lg transition">
            {loading ? '...' : tab === 'login' ? '登录' : '注册'}
          </button>
        </div>
      </div>
    </div>
  )
}
