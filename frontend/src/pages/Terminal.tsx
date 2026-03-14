import { Link, useSearchParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useTerminal } from '../context/TerminalContext'

function TerminalPane({
  jobId,
  output,
  done,
  progress,
  isActive,
}: {
  jobId: string
  output: string[]
  done: boolean
  progress: string | null
  isActive: boolean
}) {
  const preRef = useRef<HTMLPreElement>(null)

  useEffect(() => {
    if (isActive) preRef.current?.scrollTo(0, preRef.current.scrollHeight)
  }, [output, isActive])

  return (
    <div style={{ display: isActive ? 'block' : 'none', height: '100%' }}>
      {progress && (
        <div
          style={{
            fontSize: 10,
            color: 'var(--accent)',
            padding: '4px 8px',
            background: 'rgba(0,255,255,0.08)',
            marginBottom: 4,
          }}
        >
          {progress}
        </div>
      )}
      <pre
        ref={preRef}
        style={{
          margin: 0,
          padding: 12,
          background: '#0d1117',
          overflow: 'auto',
          height: 'calc(100% - 30px)',
          fontFamily: 'monospace',
          fontSize: 12,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {output.length === 0 && !done ? 'Waiting for output... (Switch tabs anytime — jobs keep running)' : output.join('')}
      </pre>
    </div>
  )
}

export default function Terminal() {
  const [searchParams, setSearchParams] = useSearchParams()
  const urlJob = searchParams.get('job')
  const { jobs, outputs, addJob, removeJob } = useTerminal()
  const [activeId, setActiveId] = useState<string | null>(null)

  useEffect(() => {
    if (urlJob) {
      addJob(urlJob)
      setActiveId(urlJob)
      setSearchParams({ job: urlJob }, { replace: true })
    }
  }, [urlJob, addJob, setSearchParams])

  useEffect(() => {
    if (!urlJob && jobs.length > 0 && !activeId) {
      setActiveId(jobs[jobs.length - 1])
    }
  }, [jobs, urlJob, activeId])

  const handleRemoveJob = (id: string) => {
    removeJob(id)
    setActiveId((curr) => (curr === id ? null : curr))
    setSearchParams({}, { replace: true })
  }

  const active = activeId || jobs[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)', minHeight: 400 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <Link to="/report-history" className="neon-btn" style={{ padding: '6px 12px', fontSize: 11 }}>
          &lt; DASHBOARD
        </Link>
        <span style={{ color: 'var(--fg-dim)', fontSize: 11 }}>
          Jobs keep running when you switch tabs. Refresh is safe — output is restored from the server.
        </span>
      </div>

      {jobs.length === 0 ? (
        <div className="panel" style={{ padding: 24, textAlign: 'center' }}>
          <p style={{ color: 'var(--fg-dim)' }}>No terminal yet. Run a module from Modules to start.</p>
          <Link to="/modules" className="neon-btn green" style={{ marginTop: 12, display: 'inline-block' }}>
            GO TO MODULES
          </Link>
        </div>
      ) : (
        <>
          <div
            style={{
              display: 'flex',
              gap: 2,
              marginBottom: 8,
              borderBottom: '1px solid var(--fg-dim)',
              paddingBottom: 4,
            }}
          >
            {jobs.map((id) => (
              <div
                key={id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  background: active === id ? 'rgba(0,255,65,0.15)' : 'transparent',
                  border: `1px solid ${active === id ? 'var(--fg)' : 'var(--fg-dim)'}`,
                  cursor: 'pointer',
                  fontSize: 11,
                }}
                onClick={() => {
                  setActiveId(id)
                  setSearchParams({ job: id })
                }}
              >
                {id}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveJob(id)
                  }}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--fg-dim)',
                    cursor: 'pointer',
                    padding: '0 4px',
                    fontSize: 14,
                  }}
                  aria-label="Close"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {jobs.map((id) => {
              const jobOutput = outputs[id] || { output: [], done: false, progress: null }
              return (
                <TerminalPane
                  key={id}
                  jobId={id}
                  output={jobOutput.output}
                  done={jobOutput.done}
                  progress={jobOutput.progress}
                  isActive={active === id}
                />
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
