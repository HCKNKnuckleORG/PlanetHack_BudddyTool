import { useState } from 'react'
import { api } from '../api/client'
import { validateSupportTicket, escapeHtml, LIMITS } from '../utils/validation'

export default function Support() {
  const [title, setTitle] = useState('')
  const [type, setType] = useState('bug')
  const [component, setComponent] = useState('web')
  const [target, setTarget] = useState('')
  const [steps, setSteps] = useState('')
  const [expected, setExpected] = useState('')
  const [actual, setActual] = useState('')
  const [status, setStatus] = useState('')
  const [result, setResult] = useState<{ ticket_id: string; path: string } | null>(null)
  const [errorColor, setErrorColor] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = { title, type, component, target, steps, expected, actual }
    const { valid, error, sanitized } = validateSupportTicket(payload)
    if (!valid || !sanitized) {
      setStatus(`Validation: ${error}`)
      setErrorColor(true)
      return
    }
    setErrorColor(false)
    setStatus('Submitting...')
    try {
      const res = await api.support.submitTicket(sanitized)
      setResult(res)
      setStatus('Saved.')
      setTitle('')
      setType('bug')
      setComponent('web')
      setTarget('')
      setSteps('')
      setExpected('')
      setActual('')
    } catch (err) {
      setStatus(`Error: ${escapeHtml(err instanceof Error ? err.message : String(err))}`)
      setErrorColor(true)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="section-title">[ SUPPORT / ISSUE TICKET ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>

      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-header" style={{ color: 'var(--cyan)' }}>[ HOW TO REPORT A BUG FAST ]</div>
        <div style={{ fontSize: 12, color: 'var(--fg)', padding: '8px 10px' }}>
          Include: <span style={{ color: 'var(--yellow)' }}>what you did</span>,{' '}
          <span style={{ color: 'var(--yellow)' }}>what you expected</span>,{' '}
          <span style={{ color: 'var(--yellow)' }}>what actually happened</span>, and any{' '}
          <span style={{ color: 'var(--yellow)' }}>error output</span>.
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="panel">
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10, flexWrap: 'wrap' }}>
            <span style={{ minWidth: 110, color: 'var(--fg-dim)' }}>TYPE</span>
            <select value={type} onChange={(e) => setType(e.target.value)} className="cyber-input" style={{ maxWidth: 240 }}>
              <option value="bug">Bug</option>
              <option value="feature">Feature request</option>
              <option value="question">Question</option>
            </select>
            <span style={{ minWidth: 120, color: 'var(--fg-dim)' }}>COMPONENT</span>
            <select value={component} onChange={(e) => setComponent(e.target.value)} className="cyber-input" style={{ maxWidth: 260 }}>
              <option value="web">Web UI (Flask)</option>
              <option value="gui">GUI (Tkinter)</option>
              <option value="cli">CLI</option>
              <option value="recon">Recon workflow</option>
              <option value="modules">Modules</option>
              <option value="docker">Docker</option>
              <option value="frontend">TypeScript SPA</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ minWidth: 110, color: 'var(--fg-dim)' }}>TITLE</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="cyber-input"
              placeholder={`Short summary (${LIMITS.title.min}–${LIMITS.title.max} chars)`}
              required
              maxLength={LIMITS.title.max}
              style={{ flex: 1 }}
            />
            <span style={{ fontSize: 10, color: 'var(--fg-dim)' }}>{title.length}/{LIMITS.title.max}</span>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
            <span style={{ minWidth: 110, color: 'var(--fg-dim)' }}>TARGET</span>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="cyber-input"
              placeholder="(optional) IP / hostname / URL"
              maxLength={LIMITS.target.max}
              style={{ flex: 1 }}
            />
          </div>

          <div style={{ display: 'grid', gap: 10 }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 4 }}>STEPS TO REPRODUCE (max {LIMITS.steps.max})</div>
              <textarea
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
                name="steps"
                className="cyber-input"
                rows={5}
                maxLength={LIMITS.steps.max}
                style={{ width: '100%' }}
                placeholder={'1) ...\n2) ...\n3) ...'}
              />
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 4 }}>EXPECTED (max {LIMITS.expected.max})</div>
              <textarea
                value={expected}
                onChange={(e) => setExpected(e.target.value)}
                className="cyber-input"
                rows={3}
                maxLength={LIMITS.expected.max}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 4 }}>ACTUAL (max {LIMITS.actual.max})</div>
              <textarea
                value={actual}
                onChange={(e) => setActual(e.target.value)}
                className="cyber-input"
                rows={3}
                maxLength={LIMITS.actual.max}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 12 }}>
            <button type="submit" className="neon-btn green">
              SUBMIT TICKET
            </button>
            <span
              style={{
                fontSize: 11,
                color: errorColor ? 'var(--error)' : 'var(--fg-dim)',
              }}
            >
              {status}
            </span>
          </div>
        </div>
      </form>

      {result && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="panel-header" style={{ color: 'var(--fg)' }}>[ TICKET SAVED ]</div>
          <div style={{ fontSize: 12, padding: '8px 10px' }}>
            <div><span style={{ color: 'var(--accent)' }}>ID:</span> {result.ticket_id}</div>
            <div><span style={{ color: 'var(--accent)' }}>FILE:</span> {result.path}</div>
          </div>
        </div>
      )}
    </div>
  )
}
