import { BrowserRouter, NavLink, Navigate, useLocation, useSearchParams, useNavigate } from 'react-router-dom'
import { useEffect, useState, useRef } from 'react'
import { api } from './api/client'
import Modules from './pages/Modules'
import ReportHistory from './pages/ReportHistory'
import Support from './pages/Support'
import About from './pages/About'
import Decoder from './pages/Decoder'
import { TerminalProvider, useTerminal } from './context/TerminalContext'
import { TargetScopeProvider } from './context/TargetScopeContext'

function App() {
  const [quote, setQuote] = useState<{ quote: string; movie: string } | null>(null)

  useEffect(() => {
    api.quote().then(setQuote).catch(() => setQuote({ quote: 'Hack the Planet!', movie: 'Hackers' }))
  }, [])

  return (
    <BrowserRouter>
      <TerminalProvider>
      <div className="app-wrapper">
        <div className="crt-overlay" />
        <header className="app-header">
          <div className="title">[ PLANETHACK ]</div>
          <div className="quote">{quote ? `"${quote.quote}" — ${quote.movie}` : '...'}</div>
        </header>

        <NavWithJobs />

        <div className="app-body">
          <main className="main-content">
            <PageContent />
          </main>
          <TerminalPanelPlaceholder />
        </div>

        <StatusBar />
      </div>
      </TerminalProvider>
      </TargetScopeProvider>
    </BrowserRouter>
  )
}

/** Nav with persistent jobs list - always visible when jobs exist */
function NavWithJobs() {
  const location = useLocation()
  const { jobs, outputs } = useTerminal()
  const runningCount = jobs.filter((id) => !outputs[id] || !outputs[id].done).length

  return (
    <nav className="nav-tabs" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <NavLink to="/report-history" className={({ isActive }) => (isActive ? 'active' : '')}>DASHBOARD</NavLink>
      <NavLink to="/modules" className={({ isActive }) => (isActive ? 'active' : '')}>MODULES</NavLink>
      <NavLink to="/terminal" className={({ isActive }) => (isActive ? 'active' : '')}>
        TERMINAL {jobs.length > 0 && `(${jobs.length})`}
      </NavLink>
      <NavLink to="/decoder" className={({ isActive }) => (isActive ? 'active' : '')}>DECODER</NavLink>
      <NavLink to="/support" className={({ isActive }) => (isActive ? 'active' : '')}>SUPPORT</NavLink>
      <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>ABOUT</NavLink>
      {jobs.length > 0 && (
        <div
          style={{
            marginLeft: 8,
            padding: '4px 10px',
            background: 'rgba(0,255,65,0.15)',
            border: '1px solid var(--fg-dim)',
            fontSize: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>JOBS:</span>
          {jobs.map((id) => {
            const out = outputs[id]
            const isDone = out?.done ?? false
            return (
              <NavLink
                key={id}
                to={`/terminal?job=${id}`}
                style={{
                  color: isDone ? 'var(--fg-dim)' : 'var(--warning)',
                  textDecoration: 'none',
                  fontFamily: 'monospace',
                }}
              >
                {id.slice(0, 8)}{isDone ? ' ✓' : ' ●'}
              </NavLink>
            )
          })}
          {runningCount > 0 && (
            <span style={{ color: 'var(--warning)', fontSize: 9 }}>{runningCount} running</span>
          )}
        </div>
      )}
    </nav>
  )
}

/** Renders main page content based on route */
function PageContent() {
  const location = useLocation()
  const path = location.pathname

  if (path === '/' || path === '/home') {
    return <Navigate to="/report-history" replace />
  }

  if (path === '/terminal') {
    return <TerminalTab />
  }

  return (
    <>
      <div style={{ display: path === '/report-history' ? 'block' : 'none', height: '100%' }}>
        <ReportHistory />
      </div>
      <div style={{ display: path === '/modules' ? 'block' : 'none', height: '100%' }}>
        <Modules />
      </div>
      <div style={{ display: path === '/decoder' ? 'block' : 'none', height: '100%' }}>
        <Decoder />
      </div>
      <div style={{ display: path === '/support' ? 'block' : 'none', height: '100%' }}>
        <Support />
      </div>
      <div style={{ display: path === '/about' ? 'block' : 'none', height: '100%' }}>
        <About />
      </div>
    </>
  )
}

/** Terminal tab page - full embedded terminal when user clicks TERMINAL in nav */
function TerminalTab() {
  return (
    <div className="terminal-tab-page">
      <TerminalPanel embedded syncFromUrl />
    </div>
  )
}

/** Banner when job completes: ask user to confirm before adding to Report History */
function JobCompleteBanner({
  jobId,
  visible,
  onConfirm,
  onDismiss,
}: {
  jobId: string
  visible: boolean
  onConfirm: () => void | Promise<void>
  onDismiss: () => void
}) {
  if (!visible) return null
  return (
    <div
      style={{
        marginBottom: 8,
        padding: '10px 14px',
        background: 'rgba(0,255,65,0.12)',
        border: '1px solid var(--accent)',
        fontSize: 11,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}
    >
      <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>
        Job {jobId.slice(0, 8)} complete. Add results to Report History?
      </span>
      <button type="button" className="neon-btn green" style={{ padding: '4px 12px', fontSize: 11 }} onClick={onConfirm}>
        Yes, Add & View
      </button>
      <button type="button" className="neon-btn" style={{ padding: '4px 12px', fontSize: 11 }} onClick={onDismiss}>
        No, Keep in Terminal Only
      </button>
    </div>
  )
}

/** Bottom terminal panel - hidden when viewing Terminal tab (terminal is in main content) */
function TerminalPanelPlaceholder() {
  const location = useLocation()
  if (location.pathname === '/terminal') return null
  return <TerminalPanel embedded={false} />
}

/** Persistent terminal panel - bottom bar or full embedded in Terminal tab */
function TerminalPanel({ embedded = false, syncFromUrl = false }: { embedded?: boolean; syncFromUrl?: boolean }) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { jobs, outputs, removeJob } = useTerminal()
  const [activeId, setActiveId] = useState<string | null>(null)
  const preRef = useRef<HTMLPreElement>(null)
  const prevJobsLen = useRef(0)
  const [confirmedOrDismissed, setConfirmedOrDismissed] = useState<Set<string>>(new Set())

  const urlJob = syncFromUrl ? searchParams.get('job') : null

  useEffect(() => {
    if (jobs.length === 0) {
      setActiveId(null)
    } else if (urlJob && jobs.includes(urlJob)) {
      setActiveId(urlJob)
    } else if (jobs.length > prevJobsLen.current) {
      setActiveId(jobs[jobs.length - 1])
    } else if (!activeId || !jobs.includes(activeId)) {
      setActiveId(jobs[jobs.length - 1])
    }
    prevJobsLen.current = jobs.length
  }, [jobs, activeId, urlJob])

  const active = activeId || jobs[0]
  const activeOutput = active ? outputs[active]?.output ?? [] : []

  useEffect(() => {
    preRef.current?.scrollTo(0, preRef.current.scrollHeight)
  }, [active, activeOutput.length])

  const handleClose = (id: string) => {
    const ok = window.confirm(
      'Close this terminal? Output will be removed and cannot be recovered. Are you sure?'
    )
    if (ok) {
      removeJob(id)
      if (activeId === id) setActiveId(jobs.find((j) => j !== id) ?? null)
    }
  }

  if (jobs.length === 0) {
    if (embedded) {
      return (
        <div className="terminal-empty-state">
          <p style={{ color: 'var(--fg-dim)', marginBottom: 12 }}>
            No terminal sessions. Run a module (e.g. RECON) from the Modules page to see output here.
          </p>
          <NavLink to="/modules" className="neon-btn green" style={{ padding: '8px 16px' }}>
            GO TO MODULES
          </NavLink>
        </div>
      )
    }
    return null
  }

  const runningCount = jobs.filter((id) => !outputs[id] || !outputs[id].done).length

  return (
    <div className={`terminal-panel ${embedded ? 'terminal-panel-embedded' : ''}`}>
      <div className="terminal-panel-header">
        <span style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold' }}>TERMINAL</span>
        <span style={{ color: 'var(--fg-dim)', fontSize: 10, marginLeft: 4 }}>
          — {jobs.length} job{jobs.length !== 1 ? 's' : ''}
          {runningCount > 0 && ` (${runningCount} running)`}
        </span>
        <button
          type="button"
          className="neon-btn"
          style={{ padding: '2px 8px', fontSize: 10, marginLeft: 8 }}
          onClick={() => {
            const sel = window.getSelection?.()?.toString?.()?.trim() || ''
            if (sel) navigate(`/decoder?input=${encodeURIComponent(sel)}`)
          }}
        >
          Decode selected
        </button>
        <div
          style={{
            display: 'flex',
            gap: 2,
            flexWrap: 'wrap',
            alignItems: 'center',
            marginLeft: 8,
          }}
        >
          <span style={{ color: 'var(--fg-dim)', fontSize: 10, marginRight: 4 }}>Current jobs:</span>
          {jobs.map((id) => {
            const out = outputs[id]
            const isDone = out?.done ?? false
            const lineCount = out?.output?.length ?? 0
            return (
              <div
                key={id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '4px 10px',
                  background: active === id ? 'rgba(0,255,65,0.2)' : 'rgba(0,0,0,0.3)',
                  border: `1px solid ${active === id ? 'var(--fg)' : 'var(--fg-dim)'}`,
                  cursor: 'pointer',
                  fontSize: 11,
                }}
                onClick={() => setActiveId(id)}
              >
                {id.slice(0, 8)}
                {isDone ? (
                  <span style={{ color: 'var(--fg-dim)', fontSize: 9 }}>✓ Done</span>
                ) : (
                  <span className="terminal-tab-running" style={{ color: 'var(--warning)', fontSize: 9 }}>● Running</span>
                )}
                {lineCount > 0 && <span style={{ color: 'var(--fg-dim)', fontSize: 9 }}>({lineCount})</span>}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleClose(id)
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--fg-dim)',
                    cursor: 'pointer',
                    padding: '0 2px',
                    fontSize: 12,
                  }}
                  aria-label="Close tab"
                >
                  ×
                </button>
              </div>
            )
          })}
        </div>
      </div>
      <div className="terminal-panel-body">
        {jobs.map((id) => {
          const jobOutput = outputs[id] || { output: [], done: false, progress: null }
          return (
            <div
              key={id}
              style={{
                display: active === id ? 'flex' : 'none',
                flexDirection: 'column',
                height: '100%',
              }}
            >
              <JobCompleteBanner
                jobId={id}
                visible={jobOutput.done && !confirmedOrDismissed.has(id)}
                onConfirm={async () => {
                  try {
                    await api.jobConfirmReport(id)
                    setConfirmedOrDismissed((s) => new Set(s).add(id))
                    navigate('/report-history')
                    window.dispatchEvent(new Event('report-history-refresh'))
                  } catch {
                    setConfirmedOrDismissed((s) => new Set(s).add(id))
                  }
                }}
                onDismiss={() => setConfirmedOrDismissed((s) => new Set(s).add(id))}
              />
              {jobOutput.progress && (
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 'bold',
                    color: 'var(--accent)',
                    padding: '6px 10px',
                    background: 'rgba(0,255,255,0.12)',
                    marginBottom: 4,
                    borderLeft: '3px solid var(--accent)',
                  }}
                >
                  ● {jobOutput.progress}
                </div>
              )}
              {!jobOutput.done && (
                <div style={{ fontSize: 10, color: 'var(--fg-dim)', padding: '2px 8px', marginBottom: 4 }}>
                  Output is throttled. Heavy tools (nuclei, gobuster) may take minutes. If VM freezes, use HTB preset.
                </div>
              )}
              {jobOutput.output.length === 0 && !jobOutput.done && (
                <div
                  style={{
                    padding: 12,
                    color: 'var(--fg-dim)',
                    fontSize: 11,
                    background: 'rgba(0,255,255,0.05)',
                    border: '1px dashed var(--fg-dim)',
                    margin: 8,
                  }}
                >
                  ↳ Job running in background. Output will appear here as it streams.
                  <br />
                  <span style={{ fontSize: 10 }}>Check status bar below for progress. Do not close this tab.</span>
                </div>
              )}
              <pre
                ref={active === id ? preRef : undefined}
                style={{
                  margin: 0,
                  padding: 12,
                  background: '#0d1117',
                  overflow: 'auto',
                  flex: 1,
                  fontFamily: 'monospace',
                  fontSize: 12,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {jobOutput.output.length === 0 && jobOutput.done
                  ? '[ Job completed. Click REFRESH on Report Dashboard to see findings. ]'
                  : jobOutput.output.length === 0 && !jobOutput.done
                    ? ''
                    : jobOutput.output.join('')}
              </pre>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Status bar - reflects terminal job state (READY vs RUNNING) */
function StatusBar() {
  const { jobs, outputs } = useTerminal()

  // Job is running if we have no output yet (just added) OR output says not done
  const runningIds = jobs.filter((id) => {
    const out = outputs[id]
    return !out || !out.done
  })
  const runningCount = runningIds.length
  const running = runningIds[0]
  const runningOutput = running ? outputs[running] : null
  const progress = runningOutput?.progress
  const statusText = runningCount > 0
    ? progress
      ? `${runningCount} job${runningCount > 1 ? 's' : ''} running: ${progress}`
      : `${runningCount} job${runningCount > 1 ? 's' : ''} running — ${running.slice(0, 8)}...`
    : 'READY'

  const isRunning = runningCount > 0

  return (
    <div className={`status-bar ${isRunning ? 'running' : ''}`}>
      <span className="label">STATUS &gt;</span>
      <span
        className="value"
        style={{
          color: isRunning ? 'var(--warning)' : 'var(--fg)',
          fontWeight: isRunning ? 'bold' : 'normal',
        }}
      >
        {statusText}
      </span>
      <NavLink to="/about" style={{ marginLeft: 'auto', color: 'var(--fg-dim)', fontSize: '10px', textDecoration: 'none' }}>
        by HCKNKnuckle
      </NavLink>
    </div>
  )
}

export default App
