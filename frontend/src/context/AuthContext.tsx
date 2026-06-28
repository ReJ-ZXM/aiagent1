import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface User { id: string; username: string; home_city: string }
interface AuthCtx {
  user: User | null; token: string | null; ready: boolean
  login: (u: string, p: string) => Promise<void>
  register: (u: string, p: string, c: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [ready, setReady] = useState(false)

  // 同步 token 到 localStorage
  useEffect(() => { if (token) localStorage.setItem('token', token); else localStorage.removeItem('token') }, [token])

  // 页面刷新时恢复用户信息
  useEffect(() => {
    const stored = localStorage.getItem('token')
    if (stored) {
      fetch('/api/v1/auth/me', { headers: { 'Authorization': `Bearer ${stored}` } })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(d => { setToken(stored); setUser(d.user) })
        .catch(() => { localStorage.removeItem('token') })
        .finally(() => setReady(true))
    } else {
      setReady(true)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const r = await fetch('/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) })
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || '登录失败') }
    const d = await r.json(); setToken(d.token); setUser(d.user)
  }

  const register = async (username: string, password: string, home_city: string) => {
    const r = await fetch('/api/v1/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, home_city }) })
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || '注册失败') }
    const d = await r.json(); setToken(d.token); setUser(d.user)
  }

  const logout = () => { setToken(null); setUser(null) }

  return <AuthContext.Provider value={{ user, token, ready, login, register, logout }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)!
