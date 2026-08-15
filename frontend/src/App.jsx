import { useCallback, useEffect, useRef, useState } from 'react'
import MatrixRain from './MatrixRain'
import Scene3D from './Scene3D'
import {
  adminLogs, adminSetRole, adminUsers, chat, clearToken, getMe, getQuota,
  getToken, listTools, login, register, runDetect, setToken,
} from './api'

const MODES = [
  { id: 'chat', label: 'CHAT', desc: 'ask anything security / hacking' },
  { id: 'analyze', label: 'ANALYZE', desc: 'paste logs / code to analyze' },
  { id: 'code', label: 'CODE', desc: 'generate safe PoC / scripts' },
  { id: 'detect', label: 'DETECT', desc: 'run lab tools on lab targets' },
]

const BOOT_LINES = [
  '[ OK ] Booting cyber_bite kernel v1.0',
  '[ OK ] Loading security modules',
  '[ OK ] Mounting knowledge base (9 topics)',
  '[ OK ] Initializing AI engine ... linked',
  '[ OK ] Opening encrypted session (AES-256)',
  '       connecting to lab@cyberbite -> OK',
]

const BANNER = [
  '╔══════════════════════════════════════════════════╗',
  '║   CYBER_BITE@LAB :: AI SECURITY COPILOT         ║',
  '║   session: encrypted · scope: lab only          ║',
  '╚══════════════════════════════════════════════════╝',
].join('\n')

function useClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

function pad(n) {
  return String(n).padStart(2, '0')
}

function Typewriter({ text, rate = 200 }) {
  const [n, setN] = useState(0)
  const [inst, setInst] = useState(false)

  useEffect(() => {
    setN(0)
    setInst(false)
    if (!text) return
    const step = Math.max(1, Math.round(rate / 60))
    const id = setInterval(() => {
      setN((p) => {
        if (p >= text.length) {
          clearInterval(id)
          return p
        }
        return p + step
      })
    }, 1000 / 60)
    return () => clearInterval(id)
  }, [text, rate])

  if (!text) return null
  const done = inst || n >= text.length
  return (
    <span className={done ? '' : 'clickable-type'} onClick={() => setInst(true)}>
      {done ? text : text.slice(0, n)}
      {!done && <span className="cursor">█</span>}
    </span>
  )
}

function Hud() {
  const start = useRef(Date.now())
  const now = useClock()
  const [cpu, setCpu] = useState(42)
  const [net, setNet] = useState(71)

  useEffect(() => {
    const id = setInterval(() => {
      setCpu(18 + Math.round(Math.random() * 66))
      setNet(38 + Math.round(Math.random() * 58))
    }, 2000)
    return () => clearInterval(id)
  }, [])

  const up = Math.floor((Date.now() - start.current) / 1000)
  const bar = (v) => '█'.repeat(Math.round(v / 12.5)).padEnd(8, '░')

  return (
    <div className="hud">
      <span className="hud-item">UPTIME {pad(Math.floor(up / 60))}:{pad(up % 60)}</span>
      <span className="hud-item">CPU <span className="bar">{bar(cpu)}</span> {cpu}%</span>
      <span className="hud-item">NET <span className="bar">{bar(net)}</span> {net}%</span>
      <span className="hud-item">NODES 3</span>
      <span className="hud-item">ENC AES-256</span>
      <span className="hud-item hud-right">{now.toLocaleTimeString('en-GB', { hour12: false })}</span>
    </div>
  )
}

function AuthScreen({ onAuthed }) {
  const [booted, setBooted] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const timers = BOOT_LINES.map((_, i) => setTimeout(() => setBooted(i + 1), 250 * (i + 1)))
    timers.push(setTimeout(() => setShowForm(true), 250 * BOOT_LINES.length + 400))
    return () => timers.forEach(clearTimeout)
  }, [])

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
          <span className="bar-title">root@cyberbite:~# secure-shell</span>
        </div>
        <div className="auth-body">
          <pre className="ascii">{BANNER}</pre>
          <div className="boot-lines">
            {BOOT_LINES.slice(0, booted).map((l, i) => (
              <p key={i} className="ok">{l}</p>
            ))}
            {!showForm && <p className="ok typing">▊</p>}
          </div>
          {showForm && (
            <>
              <div className="tabs">
                <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>LOGIN</button>
                <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>REGISTER</button>
              </div>
              <form onSubmit={submit}>
                <input placeholder="username" value={username}
                  onChange={(e) => setUsername(e.target.value)} required autoFocus />
                {mode === 'register' && (
                  <input type="email" placeholder="email" value={email}
                    onChange={(e) => setEmail(e.target.value)} required />
                )}
                <input type="password" placeholder="password" value={password}
                  onChange={(e) => setPassword(e.target.value)} required minLength={8} />
                {err && <p className="err">✗ {err}</p>}
                <button className="primary" disabled={busy}>
                  {busy ? 'AUTHENTICATING...' : mode === 'login' ? '> ENTER LAB' : '> CREATE ACCOUNT'}
                </button>
              </form>
              <p className="hint">root@cyberbite:~# access is free & unlimited for selected (pro) users</p>
            </>
          )}
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
          <div className="who">{m.role === 'user' ? 'you@lab:~$' : 'cyber_bite@lab ▸'}</div>
          <pre>
            {m.role === 'bot'
              ? <Typewriter text={m.text} />
              : m.text}
          </pre>
          {m.meta && <div className="meta">{m.meta}</div>}
        </div>
      ))}
      {busy && <div className="msg bot"><div className="who">cyber_bite@lab ▸</div><pre className="typing">▊</pre></div>}
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
          <span className="prompt">root@cyberbite:~#</span>
          <textarea rows={2} placeholder={mode.id === 'analyze' ? 'paste logs / code to analyze...' : 'ask CyberBite...'}
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
        <span className="mode-desc">run whitelisted lab tools inside the isolated sandbox</span>
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
        <pre>{output || 'no output yet. targets must be lab networks (.lab/.local/localhost/private ranges).'}</pre>
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
      <p className="hint">root@cyberbite:~# role "pro" and role "free" both have unlimited public access here.</p>
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
        <MatrixRain opacity={0.9} />
        <div className="overlay" />
        <AuthScreen onAuthed={onAuthed} />
      </>
    )
  }

  return (
    <>
      <Scene3D />
      <MatrixRain opacity={0.8} />
      <div className="overlay" />
      <div className="app">
        <div className="topbar">
          <div className="brand glitch">$ cyber_bite@lab <span className="blink">▊</span></div>
          <span className="status-dot" />
          <div className="spacer" />
          {user.role === 'free' && quota && typeof quota.messages_left_today === 'number' && quota.messages_left_today >= 0 && (
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
        <Hud />
      </div>
    </>
  )
}

export default App
