import { Link } from 'react-router-dom'
import { useState } from 'react'
import { api } from '../api/client'
import { useNavigate } from 'react-router-dom'

export default function Recon() {
  const [target, setTarget] = useState('')
  const [preset, setPreset] = useState<'full' | 'htb' | 'web'>('full')
  const [phases, setPhases] = useState<Array<{ phase: number; purpose: string; tool: string; resolved_cmd: string; tool_available: boolean }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleBuildPlan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!target.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.recon.plan(target.trim(), preset)
      setPhases(res.phases as typeof phases)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build plan')
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (phases.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.recon.execute(phases, target.trim(), preset)
      navigate(`/terminal?job=${res.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute')
    } finally {
      setLoading(false)
    }
  }

  const availableCount = phases.filter((p) => p.tool_available).length

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <Link to="/" className="neon-btn" style={{ padding: '6px 14px', fontSize: 11, marginBottom: 16, display: 'inline-block' }}>
        &lt; BACK
      </Link>

      <div className="section-title">[ RECONNAISSANCE MODULE ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>

      <form onSubmit={handleBuildPlan}>
        <div className="panel" style={{ marginBottom: 16 }}>
          <div className="input-row" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <span className="label" style={{ color: 'var(--fg-dim)' }}>TARGET &gt;</span>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="cyber-input"
              placeholder="IP address, domain, or URL"
              required
            />
          </div>
        </div>

        <div style={{ margin: '12px 0' }}>
          <span style={{ color: 'var(--fg-dim)', fontWeight: 'bold', fontSize: 12 }}>PRESET:</span>
          <div className="cyber-radio-group" style={{ marginTop: 6 }}>
            <label style={{ marginRight: 16 }}>
              <input type="radio" name="preset" value="full" checked={preset === 'full'} onChange={() => setPreset('full')} />
              {' '}FULL RECON
            </label>
            <label style={{ marginRight: 16 }}>
              <input type="radio" name="preset" value="htb" checked={preset === 'htb'} onChange={() => setPreset('htb')} />
              {' '}HTB / CTF
            </label>
            <label>
              <input type="radio" name="preset" value="web" checked={preset === 'web'} onChange={() => setPreset('web')} />
              {' '}WEB FOCUS
            </label>
          </div>
        </div>

        <button type="submit" className="neon-btn green wide" disabled={loading}>
          {loading ? '...' : '>>> BUILD RECON PLAN <<<'}
        </button>
      </form>

      {error && <div style={{ color: 'var(--error)', marginTop: 12 }}>{error}</div>}

      {phases.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div className="section-title">[ PLAN ] ({availableCount} tools available)</div>
          <pre style={{ background: 'var(--bg-panel)', padding: 16, overflow: 'auto', fontSize: 12 }}>
            {phases.map((p) => (
              <div key={p.phase} style={{ color: p.tool_available ? 'var(--fg)' : 'var(--fg-dim)', marginBottom: 8 }}>
                Phase {p.phase}: {p.purpose} ({p.tool})
                {p.tool_available ? '' : ' [NOT FOUND]'}
                {'\n'}  $ {p.resolved_cmd}
              </div>
            ))}
          </pre>
          <button
            type="button"
            className="neon-btn cyan"
            onClick={handleExecute}
            disabled={loading || availableCount === 0}
            style={{ marginTop: 12 }}
          >
            >>> EXECUTE <<<
          </button>
        </div>
      )}
    </div>
  )
}
