import { useCallback, useEffect, useRef, useState } from 'react'
import Scene3D from './Scene3D'
import {
  adminLogs, adminSetRole, adminUsers, chat, clearToken, getMe, getQuota,
  getToken, listTools, login, register, runDetect, setToken,
} from './api'

const MODES = [
  { id: 'chat', label: 'CHAT', desc: 'Ask anything security / hacking' },
  { id: 'analyze', label: 'ANALYZE', desc: 'Paste logs / code to analyze' },
  { id: 'code', label: 'CODE', desc: 'Generate safe PoC / scripts' },
  { id: 'detect', label: 'DETECT', desc: 'Run lab tools on lab targets' },
]

function formatTime() {
  return new Date().toLocaleTimeString('en-GB', { hour12: false })
}

function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      const res = mode === 'login'
        ? await login(username, password)
        : await register(username, email, password)
      setToken(res.access_token)
      onAuthed()
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-box holo">
        <div className="terminal-bar">
          <span className="dot r" /><span className="dot y" /><span className="dot g" />
          <span className="bar-title">$ cyber_bite@lab — AI Security Copilot</span>
        </div>
        <div className="auth-body">
          <div className="boot-lines">
            <p>&gt; Initializing AI Security Copilot...</p>
            <p className="ok">System online</p>
            <p className="ok">Knowledge loaded</p>
            <p className="ok">Tools ready</p>
            <p className="ok">AI engine linked</p>
          </div>
          <div className="tabs">
            <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>LOGIN</button>
            <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>REGISTER</button>
          </div>
          <form onSubmit={submit}>
            <input placeholder="username" value={username}
              onChange={(e) => setUsername(e.target.value)} required />
            {mode === 'register' && (
              <input type="email" placeholder="email" value={email}
                onChange={(e) => setEmail(e.target.value)} required />
            )}
            <input type="password" placeholder="password" value={password}
              onChange={(e) => setPassword(e.target.value)} required minLength={8} />
            {err && <p className="err">✗ {err}</p>}
            <button className="primary" disabled={busy}>
              {busy ? '...' : mode === 'login' ? 'ENTER LAB' : 'CREATE ACCOUNT'}
            </button>
          </form>
          <p className="hint">Anyone can register and start using all chatbot modes.</p>
        </div>
      </div>
    </div>
  )
}

function MessageList({ messages, busy }) {
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, busy])
  return (
    <div className="messages">
      {messages.map((m, i) => (
        <div key={i} className={`msg ${m.role}`}>
          <div className="who">{m.role === 'user' ? 'you@lab:~$' : 'cyber_bite@lab'}</div>
          <pre>{m.text}</pre>
          {m.meta && <div className="meta">{m.meta}</div>}
        </div>
      ))}
      {busy && <div className="msg bot"><div className="who">cyber_bite@lab</div><pre className="typing">▋</pre></div>}
    </div>
  )
}

function ChatMode({ mode, onAddMsg, setMessages, messages, busy, setBusy, onQuotaChange }) {
  const [input, setInput] = useState('')
  const [target, setTarget] = useState('')

  const send = async () => {
    const text = input.trim()
    if (!text || busy) return
    setInput('')
    onAddMsg({ role: 'user', text })
    setBusy(true)
    try {
      const res = await chat(text, mode.id, target.trim() || undefined)
      onAddMsg({ role: 'bot', text: res.reply,
        meta: res.decision !== 'allowed' ? `policy: ${res.decision}` : (res.used_rag ? 'rag: knowledge base used' : '') })
      if (typeof res.quota_left === 'number') onQuotaChange(res.quota_left)
    } catch (ex) {
      onAddMsg({ role: 'bot', text: `Error: ${ex.message}` })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mode-body">
      <div className="mode-head holo">
        <span className="mode-label">{mode.label} MODE</span>
        <span className="mode-desc">{mode.desc}</span>
      </div>
      <MessageList messages={messages} busy={busy} />
      <div className="composer">
        {mode.id === 'detect' && (
          <input className="target" placeholder="lab target (e.g. 127.0.0.1, dvwa.lab)"
            value={target} onChange={(e) => setTarget(e.target.value)} />
        )}
        <div className="composer-row">
          <textarea rows={2} placeholder={mode.id === 'analyze' ? 'Paste logs / code to analyze...' : 'Ask CyberBite...'}
            value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }} />
          <button className="primary" onClick={send} disabled={busy}>➤</button>
        </div>
      </div>
    </div>
  )
}

function DetectMode({ user, onAddMsg }) {
  const [tools, setTools] = useState([])
  const [tool, setTool] = useState('nmap')
  const [target, setTarget] = useState('')
  const [args, setArgs] = useState('')
  const [busy, setBusy] = useState(false)
  const [output, setOutput] = useState('')

  useEffect(() => {
    listTools().then(setTools).catch(() => {})
  }, [])

  const run = async () => {
    if (!target.trim() || busy) return
    setBusy(true)
    setOutput('running...')
    onAddMsg({ role: 'user', text: `run ${tool} ${target} ${args}` })
    try {
      const argList = args.trim() ? args.trim().split(/\s+/) : []
      const res = await runDetect(tool, target.trim(), argList)
      setOutput(`${res.decision === 'allowed' ? '' : 'BLOCKED: '}${res.output}`)
    } catch (ex) {
      setOutput(`Error: ${ex.message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mode-body">
      <div className="mode-head holo">
        <span className="mode-label">DETECT MODE</span>
        <span className="mode-desc">Run whitelisted lab tools inside the isolated sandbox</span>
      </div>
      <div className="tool-panel holo">
        <select value={tool} onChange={(e) => setTool(e.target.value)}>
          {tools.map((t) => <option key={t.name} value={t.name}>{t.name} — {t.description}</option>)}
        </select>
        <input placeholder="lab target (127.0.0.1, dvwa.lab, ...)" value={target}
          onChange={(e) => setTarget(e.target.value)} />
        <input placeholder="extra args (e.g. -sV -T4)" value={args}
          onChange={(e) => setArgs(e.target.value)} />
        <button className="primary" onClick={run} disabled={busy}>RUN IN SANDBOX</button>
      </div>
      <div className="tool-output holo">
        <pre>{output || 'No output yet. Targets must be lab networks (.lab/.local/localhost/private ranges).'}</pre>
      </div>
    </div>
  )
}

function AdminView({ onMsg }) {
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const [tab, setTab] = useState('users')

  const load = useCallback(async () => {
    try {
      setUsers(await adminUsers())
      setLogs(await adminLogs())
    } catch (ex) {
      onMsg(ex.message)
    }
  }, [onMsg])

  useEffect(() => { load() }, [load])

  const setRole = async (id, role) => {
    try {
      await adminSetRole(id, role)
      load()
    } catch (ex) {
      onMsg(ex.message)
    }
  }

  return (
    <div className="admin">
      <div className="tabs">
        <button className={tab === 'users' ? 'active' : ''} onClick={() => setTab('users')}>USERS</button>
        <button className={tab === 'logs' ? 'active' : ''} onClick={() => setTab('logs')}>AUDIT LOGS</button>
      </div>
      {tab === 'users' && (
        <table>
          <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Action</th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td><td>{u.username}</td><td>{u.email}</td>
                <td><span className={`role ${u.role}`}>{u.role}</span></td>
                <td>
                  <button onClick={() => setRole(u.id, 'pro')}>SELECT (unlimited free)</button>
                  <button onClick={() => setRole(u.id, 'free')}>LIMIT</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === 'logs' && (
        <table>
          <thead><tr><th>Time</th><th>User</th><th>Mode</th><th>Decision</th><th>Tool</th><th>Request</th></tr></thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={i}>
                <td>{l.timestamp}</td><td>{l.username}</td><td>{l.mode}</td>
                <td><span className={`role ${l.decision}`}>{l.decision}</span></td>
                <td>{l.tool}</td><td className="truncate">{l.request}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="hint">Role "pro" and role "free" both have unlimited public access in this deployment.</p>
    </div>
  )
}

function App() {
  const [user, setUser] = useState(null)
  const [quota, setQuota] = useState(null)
  const [mode, setMode] = useState(MODES[0])
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const [notif, setNotif] = useState('')

  const refreshMe = useCallback(async () => {
    try {
      setUser(await getMe())
      setQuota(await getQuota())
    } catch {
      clearToken()
      setUser(null)
    }
  }, [])

  useEffect(() => {
    if (getToken() && !user) refreshMe()
  }, [user, refreshMe])

  const onAuthed = () => refreshMe()
  const onAddMsg = (m) => setMessages((prev) => [...prev, m])
  const onQuotaChange = (left) => setQuota((q) => (q ? { ...q, messages_left_today: left } : q))
  const flash = (t) => { setNotif(t); setTimeout(() => setNotif(''), 4000) }

  if (!user) {
    return (
      <>
        <Scene3D />
        <div className="overlay" />
        <AuthScreen onAuthed={onAuthed} />
      </>
    )
  }

  const isFree = user.role === 'free'

  return (
    <>
      <Scene3D />
      <div className="overlay" />
      <div className="app">
      <div className="topbar">
        <div className="brand">$ cyber_bite@lab <span className="blink">▊</span></div>
        <div className="spacer" />
        {isFree && quota && typeof quota.messages_left_today === 'number' && quota.messages_left_today >= 0 && (
          <span className="quota">messages left today: <b>{quota.messages_left_today}</b></span>
        )}
        <span className={`role ${user.role}`}>{user.role} · {user.username}</span>
        <button className="logout" onClick={() => { clearToken(); setUser(null) }}>EXIT</button>
      </div>
      {notif && <div className="notif">{notif}</div>}
      <div className="tabs main">
        {MODES.map((m) => (
          <button key={m.id} className={mode.id === m.id ? 'active' : ''}
            onClick={() => { setMode(m); flash('') }}>
            {m.label}
          </button>
        ))}
        {user.role === 'admin' && (
          <button className={mode.id === 'admin' ? 'active' : ''}
            onClick={() => setMode({ id: 'admin', label: 'ADMIN', desc: '' })}>ADMIN</button>
        )}
      </div>
      {mode.id === 'admin' ? (
        <AdminView onMsg={flash} />
      ) : mode.id === 'detect' ? (
        <DetectMode user={user} onAddMsg={onAddMsg} />
      ) : (
        <ChatMode mode={mode} messages={messages} busy={busy} setBusy={setBusy}
          setMessages={setMessages} onAddMsg={onAddMsg} onQuotaChange={onQuotaChange} />
      )}
      </div>
    </>
  )
}

export default App
