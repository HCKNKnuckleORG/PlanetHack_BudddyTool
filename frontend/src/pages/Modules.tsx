import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useNavigate } from 'react-router-dom'
import { useTerminal } from '../context/TerminalContext'
import { useTargetScope } from '../context/TargetScopeContext'

type RunError = {
  message: string
  moduleId: string
  suggestedFix?: string
}

export default function Modules() {
  const { addJob } = useTerminal()
  const { target, setTarget, scope, setScope } = useTargetScope()
  const [modules, setModules] = useState<Array<{ id: string; name: string; color: string; group?: string }>>([])
  const [readySet, setReadySet] = useState<Set<string>>(new Set())
  const [notReadyReasons, setNotReadyReasons] = useState<Record<string, string>>({})
  const [payloadOverride, setPayloadOverride] = useState('')
  const [improveLoading, setImproveLoading] = useState(false)
  const [analyzeOutput, setAnalyzeOutput] = useState('')
  const [analyzeCommand, setAnalyzeCommand] = useState('')
  const [analysisResult, setAnalysisResult] = useState('')
  const [analyzeLoading, setAnalyzeLoading] = useState(false)
  const [preset, setPreset] = useState<'full' | 'htb' | 'web'>('htb')
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [runError, setRunError] = useState<RunError | null>(null)
  const [customCmd, setCustomCmd] = useState('')
  const [customCmdRunning, setCustomCmdRunning] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.modules().then((r) => setModules(r.modules)).catch(() => setModules([]))
  }, [])

  useEffect(() => {
    api.modulesReady(target.trim() || undefined).then((r) => {
      setReadySet(new Set(r.ready))
      const reasons: Record<string, string> = {}
      for (const nr of r.not_ready) reasons[nr.id] = nr.reason
      setNotReadyReasons(reasons)
    }).catch(() => {
      setReadySet(new Set())
      setNotReadyReasons({})
    })
  }, [target])

  useEffect(() => {
    api.session.findings().then((r) => {
      const t = (r as { target?: string }).target
      if (t && typeof t === 'string' && t.trim() && !target.trim())
        setTarget(t.trim())
    }).catch(() => {})
  }, [target, setTarget])

  const handleImprovePayload = async () => {
    const p = payloadOverride.trim()
    if (!p) return
    setImproveLoading(true)
    setRunError(null)
    try {
      const r = await api.ai.improvePayload(p)
      if (r.improved) setPayloadOverride(r.improved)
    } catch (err) {
      setRunError({
        message: err instanceof Error ? err.message : String(err),
        moduleId: 'ai',
        suggestedFix: 'Ensure Ollama is running and enabled in config.',
      })
    } finally {
      setImproveLoading(false)
    }
  }

  const handleAnalyzeOutput = async () => {
    const out = analyzeOutput.trim()
    if (!out) return
    setAnalyzeLoading(true)
    setRunError(null)
    setAnalysisResult('')
    try {
      const r = await api.ai.analyzeResponse(analyzeCommand.trim(), out)
      if (r.analysis) setAnalysisResult(r.analysis)
    } catch (err) {
      setRunError({
        message: err instanceof Error ? err.message : String(err),
        moduleId: 'ai',
        suggestedFix: 'Ensure Ollama is running and enabled in config.',
      })
    } finally {
      setAnalyzeLoading(false)
    }
  }

  const handleLoadDefault = async (moduleId: string) => {
    if (!target.trim()) return
    try {
      const r = await api.moduleCommand(moduleId, target.trim())
      setPayloadOverride(r.command || '')
    } catch {
      setPayloadOverride('')
    }
  }

  const handleRun = async (moduleId: string) => {
    if (!target.trim()) {
      setRunError({ message: 'Please enter a target (IP, domain, or URL)', moduleId })
      return
    }
    setRunError(null)
    setLoading(true)
    setSelected(moduleId)
    try {
      const cmd = payloadOverride.trim() && moduleId !== 'recon' ? payloadOverride.trim() : undefined
      const res = await api.moduleRun(
        moduleId,
        target.trim(),
        moduleId === 'recon' ? preset : undefined,
        cmd
      )
      if ((res as { redirect?: string }).redirect) {
        navigate((res as { redirect: string }).redirect)
      } else if ((res as { job_id?: string }).job_id) {
        addJob((res as { job_id: string }).job_id)
        navigate('/terminal')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      const isToolError = msg.toLowerCase().includes('tool') || msg.toLowerCase().includes('not found')
      setRunError({
        message: msg,
        moduleId,
        suggestedFix: isToolError
          ? `Try running a custom command with the correct path below.`
          : undefined,
      })
      if (isToolError) {
        setCustomCmd(`gobuster dir -u http://${target.trim()} -w /usr/share/wordlists/dirb/common.txt -t 50`)
      }
    } finally {
      setLoading(false)
      setSelected(null)
    }
  }

  const handleCustomRun = async () => {
    const cmd = customCmd.trim()
    if (!cmd) return
    setRunError(null)
    setCustomCmdRunning(true)
    try {
      const res = await api.nextStepExecute(cmd, target.trim() || undefined)
      if ((res as { error?: string }).error) {
        setRunError({ message: (res as { error: string }).error, moduleId: 'custom' })
        return
      }
      if ((res as { job_id?: string }).job_id) {
        addJob((res as { job_id: string }).job_id)
        navigate('/terminal')
      }
    } catch (err) {
      setRunError({
        message: err instanceof Error ? err.message : String(err),
        moduleId: 'custom',
      })
    } finally {
      setCustomCmdRunning(false)
    }
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <Link to="/report-history" className="neon-btn" style={{ padding: '6px 14px', fontSize: 11, marginBottom: 16, display: 'inline-block' }}>
        &lt; DASHBOARD
      </Link>

      <div className="section-title">[ BUG BOUNTY MODULES ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>

      <div
        className="panel"
        style={{
          marginBottom: 20,
          padding: '12px 16px',
          background: 'rgba(0,255,105,0.06)',
          border: '1px solid rgba(0,255,105,0.3)',
        }}
      >
        <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold', marginBottom: 10 }}>
          [ RECON GOALS — run RECON first to feed later modules ]
        </div>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11, color: 'var(--fg-dim)', lineHeight: 1.7 }}>
          <li><strong style={{ color: 'var(--fg)' }}>Identifying assets</strong> — Ports (nmap), subdomains, tech stack (whatweb).</li>
          <li><strong style={{ color: 'var(--fg)' }}>Discovering hidden information</strong> — Directories & files (gobuster), backups/configs (.bak, .env, .git).</li>
          <li><strong style={{ color: 'var(--fg)' }}>Analysing attack surface</strong> — Web vulns (nikto), template checks (nuclei).</li>
          <li><strong style={{ color: 'var(--fg)' }}>Gathering intelligence</strong> — Technologies, headers, and patterns for exploitation.</li>
        </ul>
      </div>

      <div style={{ marginBottom: 16 }}>
        <span style={{ color: 'var(--fg-dim)', fontWeight: 'bold', marginRight: 8 }}>TARGET:</span>
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="cyber-input"
          placeholder="https://example.com or IP"
          style={{ maxWidth: 400, display: 'inline-block', marginRight: 16 }}
        />
        <span style={{ color: 'var(--fg-dim)', fontWeight: 'bold', marginRight: 8 }}>SCOPE:</span>
        <input
          type="text"
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          className="cyber-input"
          placeholder="e.g. *.example.com, 10.0.0.0/8"
          style={{ maxWidth: 320, display: 'inline-block' }}
        />
      </div>
      <div style={{ marginBottom: 24, fontSize: 11, color: 'var(--fg-dim)' }}>
        <span style={{ fontWeight: 'bold', marginRight: 8 }}>RECON PRESET (for RECON module only):</span>
        <label style={{ marginRight: 12 }}><input type="radio" checked={preset === 'htb'} onChange={() => setPreset('htb')} /> HTB/CTF</label>
        <label style={{ marginRight: 12 }}><input type="radio" checked={preset === 'web'} onChange={() => setPreset('web')} /> WEB</label>
        <label style={{ marginRight: 12 }}><input type="radio" checked={preset === 'full'} onChange={() => setPreset('full')} /> FULL (heavy)</label>
        <span style={{ marginLeft: 8, fontSize: 10 }}>
          — HTB/CTF: ports + whatweb + dir discovery. WEB: + nikto + nuclei. FULL: all ports, heavier — may stress VM.
        </span>
      </div>

      {runError && (
        <div
          className="panel"
          style={{
            marginBottom: 20,
            border: '1px solid var(--error)',
            background: 'rgba(255,0,64,0.08)',
          }}
        >
          <div style={{ color: 'var(--error)', fontWeight: 'bold', marginBottom: 8 }}>
            [ MODULE FAILED: {runError.moduleId.toUpperCase()} ]
          </div>
          <div style={{ color: 'var(--fg)', marginBottom: runError.suggestedFix ? 12 : 0 }}>
            {runError.message}
          </div>
          {runError.suggestedFix && (
            <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 12 }}>
              {runError.suggestedFix}
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <button
              type="button"
              className="neon-btn"
              style={{ padding: '6px 12px', fontSize: 11 }}
              onClick={() => setRunError(null)}
            >
              DISMISS
            </button>
            <span style={{ color: 'var(--fg-dim)', fontSize: 11 }}>
              Or modify the command below and run it manually
            </span>
          </div>
        </div>
      )}

      <div style={{ marginBottom: 20 }}>
        <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold', marginBottom: 8 }}>
          [ OWASP TOP 10 2025 ]{' '}
          <a
            href="https://owasp.org/Top10/2025/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--fg-dim)', fontSize: 10, textDecoration: 'underline' }}
          >
            owasp.org/Top10/2025
          </a>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {modules.filter((m) => (m as { group?: string }).group === 'owasp2025').map((m) => {
            const isReady = readySet.has(m.id)
            const reason = notReadyReasons[m.id]
            return (
              <button
                key={m.id}
                className="neon-btn"
                style={{
                  borderColor: m.color,
                  color: isReady ? m.color : 'var(--fg-dim)',
                  padding: '8px 16px',
                  fontSize: 12,
                  opacity: isReady ? 1 : 0.6,
                }}
                onClick={() => handleRun(m.id)}
                disabled={loading || !target.trim() || !readySet.has(m.id)}
                title={reason || undefined}
              >
                {selected === m.id ? '...' : m.name}
              </button>
            )
          })}
        </div>
      </div>
      <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold', marginBottom: 8 }}>
        [ OTHER MODULES ]
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {modules.filter((m) => (m as { group?: string }).group !== 'owasp2025').map((m) => {
          const isReady = readySet.has(m.id)
          const reason = notReadyReasons[m.id]
          return (
            <button
              key={m.id}
              className="neon-btn"
              style={{
                borderColor: m.color,
                color: isReady ? m.color : 'var(--fg-dim)',
                padding: '8px 16px',
                fontSize: 12,
                opacity: isReady ? 1 : 0.6,
              }}
              onClick={() => handleRun(m.id)}
              disabled={loading || !target.trim() || !readySet.has(m.id)}
              title={reason || undefined}
            >
              {selected === m.id ? '...' : m.name}
            </button>
          )
        })}
      </div>

      <div className="panel" style={{ marginTop: 24 }}>
        <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold', marginBottom: 8 }}>
          [ PAYLOAD / COMMAND OVERRIDE ]
        </div>
        <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 8 }}>
          Optional: run a custom command instead of the module. Load default for a module, edit, then run that module.
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-start', marginBottom: 12 }}>
          <select
            id="payload-module-select"
            className="cyber-input"
            style={{ minWidth: 160, fontSize: 11 }}
            onChange={(e) => e.target.value && handleLoadDefault(e.target.value)}
          >
            <option value="">-- Load default for --</option>
            {modules.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <input
            type="text"
            className="cyber-input"
            value={payloadOverride}
            onChange={(e) => setPayloadOverride(e.target.value)}
            placeholder="Custom command (e.g. sqlmap -u TARGET ...)"
            style={{ flex: '1 1 400px', fontFamily: 'monospace', fontSize: 11 }}
          />
          <button
            type="button"
            className="neon-btn"
            style={{ padding: '6px 12px', fontSize: 11 }}
            onClick={handleImprovePayload}
            disabled={improveLoading || !payloadOverride.trim()}
            title="Use Ollama to improve this payload (requires Ollama running)"
          >
            {improveLoading ? '...' : 'IMPROVE WITH AI'}
          </button>
        </div>
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(0,255,105,0.2)' }}>
          <div style={{ color: 'var(--fg-dim)', fontSize: 11, marginBottom: 8 }}>
            Paste command output to analyze:
          </div>
          <input
            type="text"
            className="cyber-input"
            value={analyzeCommand}
            onChange={(e) => setAnalyzeCommand(e.target.value)}
            placeholder="Command (optional)"
            style={{ width: '100%', marginBottom: 8, fontFamily: 'monospace', fontSize: 11 }}
          />
          <textarea
            className="cyber-input"
            value={analyzeOutput}
            onChange={(e) => setAnalyzeOutput(e.target.value)}
            placeholder="Paste command output here..."
            rows={4}
            style={{ width: '100%', fontFamily: 'monospace', fontSize: 11 }}
          />
          <button
            type="button"
            className="neon-btn"
            style={{ marginTop: 8, padding: '6px 12px', fontSize: 11 }}
            onClick={handleAnalyzeOutput}
            disabled={analyzeLoading || !analyzeOutput.trim()}
            title="Use Ollama to analyze output (requires Ollama running)"
          >
            {analyzeLoading ? '...' : 'ANALYZE WITH AI'}
          </button>
          {analysisResult && (
            <div
              className="panel"
              style={{ marginTop: 12, padding: 12, background: 'rgba(0,255,105,0.06)', border: '1px solid rgba(0,255,105,0.3)' }}
            >
              <div style={{ fontSize: 11, color: 'var(--accent)', marginBottom: 8 }}>Analysis:</div>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 11, color: 'var(--fg)' }}>{analysisResult}</pre>
            </div>
          )}
        </div>
      </div>

      <div className="panel" style={{ marginTop: 24 }}>
        <div style={{ color: 'var(--accent)', fontSize: 11, fontWeight: 'bold', marginBottom: 8 }}>
          [ RUN CUSTOM COMMAND ]
        </div>
        <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 8 }}>
          Modify syntax and run a command manually (e.g. if a tool path or option needs fixing)
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <input
            type="text"
            className="cyber-input"
            value={customCmd}
            onChange={(e) => setCustomCmd(e.target.value)}
            placeholder="e.g. gobuster dir -u http://TARGET -w /usr/share/wordlists/dirb/common.txt"
            style={{ flex: '1 1 400px', fontFamily: 'monospace', fontSize: 12 }}
            onKeyDown={(e) => e.key === 'Enter' && handleCustomRun()}
          />
          <button
            type="button"
            className="neon-btn green"
            style={{ padding: '8px 16px', fontSize: 12 }}
            onClick={handleCustomRun}
            disabled={customCmdRunning || !customCmd.trim()}
          >
            {customCmdRunning ? '...' : 'RUN'}
          </button>
        </div>
        {runError && runError.moduleId === 'custom' && (
          <div style={{ marginTop: 8, color: 'var(--error)', fontSize: 11 }}>
            {runError.message}
          </div>
        )}
      </div>
    </div>
  )
}
