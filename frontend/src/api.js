const TOKEN_KEY = 'cyberbite_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(path, { ...options, headers })
  } catch {
    throw new Error(
      `Cannot reach backend API at "${path}". ` +
      'Start the backend server and verify frontend proxy/API URL settings.'
    )
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    data = { detail: res.statusText }
  }
  if (!res.ok) {
    const err = new Error(data?.detail || res.statusText)
    err.status = res.status
    throw err
  }
  return data
}

export const login = (username, password) =>
  request('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
export const register = (username, email, password) =>
  request('/api/auth/register', { method: 'POST', body: JSON.stringify({ username, email, password }) })
export const getMe = () => request('/api/auth/me')
export const getQuota = () => request('/api/auth/me/quota')

export const chat = (message, mode, target) =>
  request('/api/chat', { method: 'POST', body: JSON.stringify({ message, mode, target }) })

export const listTools = () => request('/api/detect/tools')
export const runDetect = (tool, target, args) =>
  request('/api/detect/run', { method: 'POST', body: JSON.stringify({ tool, target, args }) })

export const adminUsers = () => request('/api/admin/users')
export const adminSetRole = (id, role) =>
  request(`/api/admin/users/${id}/role`, { method: 'PUT', body: JSON.stringify({ role }) })
export const adminLogs = (limit = 50) => request(`/api/admin/logs?limit=${limit}`)
