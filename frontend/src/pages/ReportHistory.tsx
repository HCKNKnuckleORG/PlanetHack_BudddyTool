import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useState, useRef } from 'react'
import { api } from '../api/client'
import { useTerminal } from '../context/TerminalContext'
import { useTargetScope } from '../context/TargetScopeContext'
import DecodeLink from '../components/DecodeLink'

interface FindingByTool {
  ports?: Array<{ port: number; proto: string; service: string }>
  os?: string[]
  scan_target?: string
  redirect_hostname?: string
  summary?: string
  technologies?: string[]
  findings?: Array<{ detail?: string; severity?: string; path?: string; status?: string; template?: string }>
  directories?: Array<{ path?: string; status?: string }>
  count?: number
  critical_high?: number
  raw?: string | unknown
}

interface SessionData {
  summary: { tools_run?: string[]; ports?: unknown[] }
  findings_by_tool?: Record<string, FindingByTool>
  next_steps?: Array<{ reason: string; command: string; tool: string; goal?: string }>
  history?: Array<{ tool: string; source: string; exit_code: number; time: string }>
  target?: string
  log_file?: string
}

const TOOL_LABELS: Record<string, string> = {
  nmap: 'Nmap',
  whatweb: 'WhatWeb',
  nikto: 'Nikto',
  gobuster: 'Gobuster',
  feroxbuster: 'Feroxbuster',
  dirb: 'Dirb',
  nuclei: 'Nuclei',
  brute_force: 'Brute Force',
  recon: 'Recon',
}

export default function ReportHistory() {
  const [data, setData] = useState<SessionData | null>(null)
  const [showRaw, setShowRaw] = useState(false)
  const [runningIdx, setRunningIdx] = useState<number | null>(null)
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [editingCmd, setEditingCmd] = useState('')
  const [stepError, setStepError] = useState<{ idx: number; msg: string } | null>(null)
  const [showCompletedBanner, setShowCompletedBanner] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})
  const hadRunningRef = useRef(false)
  const navigate = useNavigate()
  const { target: scopeTarget, scope } = useTargetScope()
  const { addJob, jobs, outputs } = useTerminal()

  const toggleExpanded = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const runningCount = jobs.filter((id) => !outputs[id] || !outputs[id].done).length
  const allDone = jobs.length > 0 && runningCount === 0

  useEffect(() => {
    const hadRunning = hadRunningRef.current
    hadRunningRef.current = runningCount > 0
    if (runningCount > 0) {
      setShowCompletedBanner(false)
    } else if (hadRunning && jobs.length > 0) {
      setShowCompletedBanner(true)
      api.session.findings().then((r) => setData(r as SessionData)).catch(() => setData(null))
    }
  }, [runningCount, jobs.length])

  const refresh = () => {
    api.session
      .findings()
      .then((r) => setData(r as SessionData))
      .catch(() => setData(null))
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Auto-refresh every 20s while scans are running so findings appear as tools complete
  useEffect(() => {
    if (runningCount === 0) return
    const interval = setInterval(refresh, 20_000)
    return () => clearInterval(interval)
  }, [runningCount])

  // Refresh when user confirms a job and navigates here
  useEffect(() => {
    const handler = () => refresh()
    window.addEventListener('report-history-refresh', handler)
    return () => window.removeEventListener('report-history-refresh', handler)
  }, [])

  if (!data) {
    return (
      <div>
        <Link to="/modules" className="neon-btn">
          MODULES
        </Link>
        <p>Loading session data...</p>
      </div>
    )
  }

  const hasData = Boolean((data.summary as { tools_run?: unknown[] })?.tools_run?.length)
  const findingsByTool = data.findings_by_tool ?? {}
  const toolsRun = (data.summary?.tools_run ?? []) as string[]

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      {showCompletedBanner && allDone && (
        <div
          style={{
            marginBottom: 12,
            padding: '10px 14px',
            background: 'rgba(0,255,65,0.12)',
            border: '1px solid var(--fg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <span style={{ color: 'var(--fg)', fontSize: 12 }}>
            ✓ Scans completed — data refreshed below. Review findings and next steps.
          </span>
          <button
            type="button"
            className="neon-btn green"
            style={{ padding: '4px 10px', fontSize: 11 }}
            onClick={() => {
              refresh()
              setShowCompletedBanner(false)
            }}
          >
            REFRESH AGAIN
          </button>
        </div>
      )}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <Link to="/modules" className="neon-btn green">
          RUN MODULES
        </Link>
        <button type="button" className="neon-btn" onClick={refresh} style={{ padding: '6px 14px', fontSize: 11 }}>
          REFRESH
        </button>
        <span style={{ color: 'var(--fg-dim)', fontSize: 11, marginLeft: 8 }}>
          {runningCount > 0
            ? `${runningCount} job${runningCount > 1 ? 's' : ''} running — refresh after completion`
            : 'Jobs run in background — refresh after tools complete to see new findings'}
        </span>
      </div>
      <div className="section-title">[ REPORT DASHBOARD ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
      <p style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 16, maxWidth: 720 }}>
        Recon supports: <strong style={{ color: 'var(--fg)' }}>Identifying assets</strong> (ports, tech) → <strong style={{ color: 'var(--fg)' }}>Hidden info</strong> (dirs, backups) → <strong style={{ color: 'var(--fg)' }}>Attack surface</strong> (nikto, nuclei) → <strong style={{ color: 'var(--fg)' }}>Intelligence</strong> for next modules.
      </p>

      {!hasData ? (
        <div style={{ color: 'var(--fg-dim)' }}>
          <p>
            {runningCount > 0
              ? 'Scans in progress — findings will appear as each tool (nmap, whatweb, etc.) completes. Click REFRESH or wait; data refreshes automatically every 20s while running.'
              : 'No data yet. Run a module (e.g. RECON) from the Modules page.'}
          </p>
          {runningCount > 0 && (
            <button type="button" className="neon-btn" style={{ marginTop: 8 }} onClick={refresh}>
              REFRESH NOW
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Target & Scope (from session + context) & export row */}
          <div
            style={{
              display: 'flex',
              gap: 12,
              flexWrap: 'wrap',
              alignItems: 'center',
              marginBottom: 20,
            }}
          >
            <div className="panel" style={{ flex: '1 1 280px' }}>
              <div
                className="panel-header"
                style={{ color: 'var(--accent)', fontSize: 11 }}
              >
                TARGET / SCOPE
              </div>
              <div
                style={{
                  padding: '8px 12px',
                  fontFamily: 'monospace',
                  color: 'var(--fg)',
                  fontSize: 14,
                }}
              >
                {data.target || scopeTarget || '—'}
                {scope && (
                  <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--fg-dim)' }}>
                    scope: {scope}
                  </span>
                )}
              </div>
              {data.log_file && (
                <div style={{ padding: '0 12px 8px', fontSize: 10, color: 'var(--fg-dim)' }}>
                  Log: {data.log_file}
                </div>
              )}
            </div>
            <div className="panel" style={{ flex: '0 0 auto' }}>
              <div className="panel-header" style={{ fontSize: 11 }}>EXPORT</div>
              <div style={{ display: 'flex', gap: 8, padding: 8 }}>
                <button
                  type="button"
                  className="neon-btn green"
                  style={{ padding: '6px 12px', fontSize: 11 }}
                  onClick={() => {
                    fetch('/api/v1/session/report?format=md')
                      .then((r) => r.blob())
                      .then((blob) => {
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = 'planethack-report.md'
                        a.click()
                        URL.revokeObjectURL(url)
                      })
                  }}
                >
                  SAVE .MD
                </button>
                <button
                  type="button"
                  className="neon-btn"
                  style={{ padding: '6px 12px', fontSize: 11 }}
                  onClick={() => {
                    fetch('/api/v1/session/report?format=html')
                      .then((r) => r.blob())
                      .then((blob) => {
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = 'planethack-report.html'
                        a.click()
                        URL.revokeObjectURL(url)
                      })
                  }}
                >
                  SAVE .HTML
                </button>
              </div>
            </div>
          </div>

          {/* Tool findings grid */}
          <div
            className="section-title"
            style={{ marginTop: 24, marginBottom: 12, fontSize: 13 }}
          >
            [ WHAT EACH TOOL FOUND ]
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: 12,
              marginBottom: 24,
            }}
          >
            {toolsRun.map((tool) => {
              const fd = findingsByTool[tool]
              const label = TOOL_LABELS[tool] ?? tool
              if (!fd) return null
              return (
                <div key={tool} className="panel" style={{ borderColor: 'var(--fg-dim)' }}>
                  <div
                    className="panel-header"
                    style={{
                      color: 'var(--cyan)',
                      fontSize: 12,
                      borderBottom: '1px solid rgba(0,255,65,0.2)',
                      paddingBottom: 6,
                    }}
                  >
                    {label}
                  </div>
                  <div style={{ padding: '10px 12px', fontSize: 12 }}>
                    {tool === 'nmap' && fd.ports && (
                      <>
                        <div style={{ color: 'var(--fg-dim)', marginBottom: 4 }}>Open ports</div>
                        <div style={{ marginBottom: 6 }}>
                          {(expandedSections[`${tool}_ports`] ? fd.ports : fd.ports.slice(0, 12)).map((p) => (
                            <span
                              key={`${p.port}-${p.proto}`}
                              style={{
                                display: 'inline-block',
                                margin: '2px 4px 2px 0',
                                padding: '2px 6px',
                                background: 'rgba(0,255,65,0.1)',
                                borderRadius: 2,
                                fontSize: 11,
                              }}
                            >
                              {p.port}/{p.proto}
                            </span>
                          ))}
                          {fd.ports.length > 12 && (
                            <button
                              type="button"
                              onClick={() => toggleExpanded(`${tool}_ports`)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--accent)',
                                cursor: 'pointer',
                                fontSize: 11,
                                padding: '0 4px',
                                textDecoration: 'underline',
                              }}
                            >
                              {expandedSections[`${tool}_ports`]
                                ? '▲ Show less'
                                : `+${fd.ports.length - 12} more (click to expand)`}
                            </button>
                          )}
                        </div>
                        {fd.scan_target && (
                          <div style={{ fontSize: 10, color: 'var(--fg-dim)' }}>
                            Scan target: {fd.scan_target}
                          </div>
                        )}
                        {fd.redirect_hostname && (
                          <div style={{ fontSize: 10, color: 'var(--yellow)' }}>
                            Redirect: {fd.redirect_hostname}
                          </div>
                        )}
                      </>
                    )}
                    {tool === 'whatweb' && fd.technologies && (
                      <div>
                        {(expandedSections[`${tool}_technologies`] ? fd.technologies : fd.technologies.slice(0, 10)).join(', ')}
                        {fd.technologies.length > 10 && (
                          <>
                            {' '}
                            <button
                              type="button"
                              onClick={() => toggleExpanded(`${tool}_technologies`)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--accent)',
                                cursor: 'pointer',
                                fontSize: 11,
                                padding: 0,
                                textDecoration: 'underline',
                              }}
                            >
                              {expandedSections[`${tool}_technologies`]
                                ? '▲ Show less'
                                : `+${fd.technologies.length - 10} more (click)`}
                            </button>
                          </>
                        )}
                      </div>
                    )}
                    {(tool === 'nikto' || tool === 'nuclei') && fd.findings && (
                      <>
                        <div style={{ color: 'var(--fg-dim)', marginBottom: 4 }}>
                          {fd.count} finding(s)
                          {fd.critical_high != null && ` · ${fd.critical_high} critical/high`}
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, maxHeight: expandedSections[`${tool}_findings`] ? 400 : 120, overflow: 'auto' }}>
                          {(expandedSections[`${tool}_findings`] ? fd.findings : fd.findings.slice(0, 6)).map((f, i) => (
                            <li key={i} style={{ marginBottom: 2, fontSize: 11 }}>
                              <DecodeLink text={f.detail ?? ''} maxLen={70} />
                              {f.severity && (
                                <span
                                  style={{
                                    marginLeft: 4,
                                    color:
                                      f.severity === 'critical' || f.severity === 'high'
                                        ? 'var(--error)'
                                        : 'var(--fg-dim)',
                                  }}
                                >
                                  [{f.severity}]
                                </span>
                              )}
                            </li>
                          ))}
                          {fd.findings.length > 6 && (
                            <li>
                              <button
                                type="button"
                                onClick={() => toggleExpanded(`${tool}_findings`)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: 'var(--accent)',
                                  cursor: 'pointer',
                                  fontSize: 11,
                                  padding: 0,
                                  textDecoration: 'underline',
                                }}
                              >
                                {expandedSections[`${tool}_findings`]
                                  ? '▲ Show less'
                                  : `+${fd.findings.length - 6} more (click to expand)`}
                              </button>
                            </li>
                          )}
                        </ul>
                      </>
                    )}
                    {(tool === 'gobuster' || tool === 'feroxbuster' || tool === 'dirb') &&
                      (fd.directories ?? fd.findings) && (
                        <>
                          <div style={{ color: 'var(--fg-dim)', marginBottom: 4 }}>
                            {fd.count} path(s) discovered
                          </div>
                          <ul style={{ margin: 0, paddingLeft: 16, maxHeight: expandedSections[`${tool}_dirs`] ? 400 : 100, overflow: 'auto' }}>
                            {((expandedSections[`${tool}_dirs`] ? (fd.directories ?? fd.findings) : (fd.directories ?? fd.findings ?? []).slice(0, 8)) as Array<{ path?: string; status?: string }>).map((d, i) => (
                              <li key={i} style={{ fontSize: 11, fontFamily: 'monospace' }}>
                                {d.path ?? d}{' '}
                                {d.status && (
                                  <span style={{ color: 'var(--fg-dim)' }}>[{d.status}]</span>
                                )}
                              </li>
                            ))}
                            {((fd.directories ?? fd.findings) as unknown[]).length > 8 && (
                              <li>
                                <button
                                  type="button"
                                  onClick={() => toggleExpanded(`${tool}_dirs`)}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--accent)',
                                    cursor: 'pointer',
                                    fontSize: 11,
                                    padding: 0,
                                    textDecoration: 'underline',
                                  }}
                                >
                                  {expandedSections[`${tool}_dirs`]
                                    ? '▲ Show less'
                                    : `+${((fd.directories ?? fd.findings) as unknown[]).length - 8} more (click to expand)`}
                                </button>
                              </li>
                            )}
                          </ul>
                        </>
                      )}
                    {!['nmap', 'whatweb', 'nikto', 'gobuster', 'feroxbuster', 'dirb', 'nuclei'].includes(tool) && (
                      <div>
                        <div style={{ color: 'var(--fg-dim)', fontSize: 11 }}>{fd.summary}</div>
                        {typeof fd.raw === 'string' && fd.raw.length > 0 && (
                          <>
                            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                              <button
                                type="button"
                                onClick={() => navigate(`/decoder?input=${encodeURIComponent(fd.raw.slice(0, 2000))}`)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: 'var(--accent)',
                                  cursor: 'pointer',
                                  fontSize: 10,
                                  textDecoration: 'underline',
                                }}
                              >
                                Try decode output
                              </button>
                            </div>
                            <pre style={{ marginTop: 4, padding: 8, background: '#0a0a0a', fontSize: 10, overflow: 'auto', maxHeight: expandedSections[`${tool}_raw`] ? 400 : 120 }}>
                              {expandedSections[`${tool}_raw`] ? fd.raw : fd.raw.slice(0, 800)}{fd.raw.length > 800 && !expandedSections[`${tool}_raw`] ? '\n...' : ''}
                            </pre>
                            {fd.raw.length > 800 && (
                              <button
                                type="button"
                                onClick={() => toggleExpanded(`${tool}_raw`)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: 'var(--accent)',
                                  cursor: 'pointer',
                                  fontSize: 11,
                                  padding: '4px 0 0',
                                  textDecoration: 'underline',
                                }}
                              >
                                {expandedSections[`${tool}_raw`] ? '▲ Show less' : `+${fd.raw.length - 800} more chars (click to expand)`}
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Next attack direction */}
          {data.next_steps && data.next_steps.length > 0 && (
            <>
              <div
                className="section-title"
                style={{ marginBottom: 12, fontSize: 13 }}
              >
                [ NEXT ATTACK DIRECTION ]
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  marginBottom: 24,
                }}
              >
                {data.next_steps.map((step, idx) => (
                  <div
                    key={idx}
                    className="panel"
                    style={{
                      borderLeft: '3px solid var(--accent)',
                      padding: '12px 14px',
                    }}
                  >
                    {step.goal && (
                      <div
                        style={{
                          fontSize: 10,
                          color: 'var(--accent)',
                          marginBottom: 4,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        {step.goal}
                      </div>
                    )}
                    <div
                      style={{
                        color: 'var(--fg)',
                        marginBottom: 6,
                        fontSize: 13,
                      }}
                    >
                      {step.reason}
                    </div>
                    {editingIdx === idx ? (
                      <div style={{ marginTop: 8 }}>
                        <input
                          type="text"
                          className="cyber-input"
                          value={editingCmd}
                          onChange={(e) => setEditingCmd(e.target.value)}
                          style={{
                            width: '100%',
                            fontFamily: 'monospace',
                            fontSize: 11,
                            padding: '8px 10px',
                            marginBottom: 8,
                          }}
                          placeholder="Modify the command and run"
                        />
                      </div>
                    ) : (
                      <div
                        style={{
                          fontFamily: 'monospace',
                          fontSize: 11,
                          color: 'var(--warning)',
                          background: 'rgba(0,0,0,0.3)',
                          padding: '8px 10px',
                          borderRadius: 2,
                          wordBreak: 'break-all',
                        }}
                      >
                        $ {step.command}
                      </div>
                    )}
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="neon-btn green"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                        disabled={runningIdx === idx}
                        onClick={async () => {
                          const cmd = editingIdx === idx ? editingCmd.trim() : step.command
                          if (!cmd) {
                            setStepError({ idx, msg: 'Please enter a command' })
                            return
                          }
                          setStepError(null)
                          setRunningIdx(idx)
                          try {
                            const res = await api.nextStepExecute(cmd, data.target)
                            if (res.job_id) {
                              addJob(res.job_id)
                              setEditingIdx(null)
                              navigate('/terminal')
                            }
                          } catch (err) {
                            setStepError({ idx, msg: err instanceof Error ? err.message : String(err) })
                          } finally {
                            setRunningIdx(null)
                          }
                        }}
                      >
                        {runningIdx === idx ? '...' : editingIdx === idx ? 'RUN MODIFIED' : 'RUN'}
                      </button>
                      <button
                        type="button"
                        className="neon-btn"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                        onClick={() => {
                          if (editingIdx === idx) {
                            setEditingIdx(null)
                          } else {
                            setEditingIdx(idx)
                            setEditingCmd(step.command)
                          }
                        }}
                      >
                        {editingIdx === idx ? 'CANCEL EDIT' : 'EDIT & RUN'}
                      </button>
                      <button
                        type="button"
                        className="neon-btn"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                        onClick={() => {
                          navigator.clipboard.writeText(step.command)
                        }}
                      >
                        COPY COMMAND
                      </button>
                      {stepError?.idx === idx && (
                        <span style={{ color: 'var(--error)', fontSize: 11, alignSelf: 'center' }}>
                          {stepError.msg}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Raw source (collapsible) */}
          <div className="panel" style={{ marginTop: 16 }}>
            <button
              type="button"
              className="panel-header"
              style={{
                width: '100%',
                textAlign: 'left',
                border: 'none',
                background: 'none',
                color: 'var(--fg-dim)',
                cursor: 'pointer',
                fontSize: 11,
              }}
              onClick={() => setShowRaw(!showRaw)}
            >
              {showRaw ? '▼' : '▶'} RAW SOURCE (JSON)
            </button>
            {showRaw && (
              <pre
                style={{
                  margin: 0,
                  padding: 12,
                  background: '#0d1117',
                  overflow: 'auto',
                  fontSize: 11,
                  maxHeight: 400,
                  borderTop: '1px solid rgba(0,255,65,0.15)',
                }}
              >
                {JSON.stringify(data, null, 2)}
              </pre>
            )}
          </div>
        </>
      )}
    </div>
  )
}
