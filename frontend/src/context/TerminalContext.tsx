/**
 * Terminal jobs context - keeps stream connections alive across navigation.
 * Jobs continue running when user switches to Report Dashboard or other pages.
 * Output is persisted to sessionStorage so it survives tab switches and remounts.
 */

import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { api } from '../api/client'

const STORAGE_KEY_JOBS = 'planethack_terminal_jobs'
const STORAGE_KEY_OUTPUT_PREFIX = 'planethack_output_'
const MAX_STORED_CHARS = 400_000  // ~400KB per job to avoid sessionStorage limits

function loadJobs(): string[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY_JOBS)
    if (raw) return JSON.parse(raw)
  } catch {}
  return []
}

function saveJobs(jobs: string[]) {
  try {
    sessionStorage.setItem(STORAGE_KEY_JOBS, JSON.stringify(jobs))
  } catch {}
}

function loadOutput(jobId: string): { output: string[]; done: boolean } | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY_OUTPUT_PREFIX + jobId)
    if (raw) return JSON.parse(raw)
  } catch {}
  return null
}

function saveOutput(jobId: string, out: { output: string[]; done: boolean }) {
  try {
    let data = out
    let text = JSON.stringify(data)
    if (text.length > MAX_STORED_CHARS) {
      const joined = out.output.join('')
      const trim = Math.floor(MAX_STORED_CHARS / 2)
      data = { output: [joined.slice(-trim)], done: out.done }
      text = JSON.stringify(data)
    }
    sessionStorage.setItem(STORAGE_KEY_OUTPUT_PREFIX + jobId, text)
  } catch {}
}

function clearOutput(jobId: string) {
  try {
    sessionStorage.removeItem(STORAGE_KEY_OUTPUT_PREFIX + jobId)
  } catch {}
}

export type JobOutput = {
  output: string[]
  done: boolean
  progress: string | null
}

type TerminalContextValue = {
  jobs: string[]
  outputs: Record<string, JobOutput>
  addJob: (id: string) => void
  removeJob: (id: string) => void
}

const TerminalContext = createContext<TerminalContextValue | null>(null)

function loadInitialOutputs(jobIds: string[]): Record<string, JobOutput> {
  const out: Record<string, JobOutput> = {}
  for (const id of jobIds) {
    const saved = loadOutput(id)
    if (saved) {
      out[id] = { ...saved, progress: null }
    }
  }
  return out
}

export function TerminalProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<string[]>(loadJobs)
  const [outputs, setOutputs] = useState<Record<string, JobOutput>>(() =>
    loadInitialOutputs(loadJobs())
  )
  const esRefs = useRef<Record<string, EventSource>>({})
  const lastPersistRef = useRef<Record<string, number>>({})
  const PERSIST_THROTTLE_MS = 100

  const addJob = useCallback((id: string) => {
    setJobs((prev) => {
      if (prev.includes(id)) return prev
      const next = [...prev, id]
      saveJobs(next)
      return next
    })
    setOutputs((prev) => {
      const existing = prev[id] || loadOutput(id)
      const base = existing?.output && Array.isArray(existing.output)
        ? { output: existing.output, done: Boolean(existing.done) }
        : { output: [] as string[], done: false }
      return {
        ...prev,
        [id]: { ...base, progress: null },
      }
    })
  }, [])

  const removeJob = useCallback((id: string) => {
    const es = esRefs.current[id]
    if (es) {
      es.close()
      delete esRefs.current[id]
    }
    clearOutput(id)
    setJobs((prev) => {
      const next = prev.filter((j) => j !== id)
      saveJobs(next)
      return next
    })
    setOutputs((prev) => {
      const next = { ...prev }
      delete next[id]
      return next
    })
  }, [])

  useEffect(() => {
    saveJobs(jobs)
  }, [jobs])

  // Persist outputs when tab is hidden (e.g. user switches browser tabs) so we never lose data
  useEffect(() => {
    const onHide = () => {
      for (const jobId of jobs) {
        const out = outputs[jobId]
        if (out) saveOutput(jobId, { output: out.output, done: out.done })
      }
    }
    document.addEventListener('visibilitychange', onHide)
    return () => document.removeEventListener('visibilitychange', onHide)
  }, [jobs, outputs])

  // Keep EventSource connections alive for each job - never close on unmount (navigation)
  useEffect(() => {
    for (const jobId of jobs) {
      if (esRefs.current[jobId]) continue // already connected
      const url = api.stream(jobId)
      const es = new EventSource(url)
      esRefs.current[jobId] = es

      es.onmessage = (e) => {
        const d = e.data
        if (d === 'complete') {
          setOutputs((prev) => {
            const next = { ...prev, [jobId]: { ...prev[jobId], done: true, progress: null } }
            queueMicrotask(() => saveOutput(jobId, { output: next[jobId].output, done: true }))
            return next
          })
          es.close()
          delete esRefs.current[jobId]
          return
        }
        const chunk = (d || '').replace(/\\n/g, '\n')
        setOutputs((prev) => {
          const newOutput = [...(prev[jobId]?.output ?? []), chunk]
          const next = { ...prev, [jobId]: { ...prev[jobId], output: newOutput, done: false } }
          queueMicrotask(() => {
            const now = Date.now()
            const last = lastPersistRef.current[jobId] ?? 0
            if (last === 0 || now - last >= PERSIST_THROTTLE_MS) {
              saveOutput(jobId, { output: newOutput, done: false })
              lastPersistRef.current[jobId] = now
            }
          })
          return next
        })
      }

      es.addEventListener('progress', (e) => {
        const d = (e as MessageEvent).data
        if (d) {
          const parts = String(d).split('|')
          const progress = parts.length >= 4
            ? `Phase ${parts[0]}/${parts[1]}: ${parts[2]} — ${parts[3]}`
            : d
          setOutputs((prev) => ({
            ...prev,
            [jobId]: { ...prev[jobId], progress },
          }))
        }
      })

      es.addEventListener('done', () => {
        setOutputs((prev) => {
          const next = { ...prev, [jobId]: { ...prev[jobId], done: true, progress: null } }
          queueMicrotask(() => saveOutput(jobId, { output: next[jobId].output, done: true }))
          return next
        })
        es.close()
        delete esRefs.current[jobId]
      })

      es.onerror = () => {
        setOutputs((prev) => {
          const next = { ...prev, [jobId]: { ...prev[jobId], done: true, progress: null } }
          queueMicrotask(() => saveOutput(jobId, { output: next[jobId].output, done: true }))
          return next
        })
        es.close()
        delete esRefs.current[jobId]
      }
    }
    // Only close EventSources when job is explicitly removed (handled in removeJob)
    return () => {}
  }, [jobs])

  const value: TerminalContextValue = {
    jobs,
    outputs,
    addJob,
    removeJob,
  }

  return (
    <TerminalContext.Provider value={value}>
      {children}
    </TerminalContext.Provider>
  )
}

export function useTerminal() {
  const ctx = useContext(TerminalContext)
  if (!ctx) throw new Error('useTerminal must be used within TerminalProvider')
  return ctx
}
