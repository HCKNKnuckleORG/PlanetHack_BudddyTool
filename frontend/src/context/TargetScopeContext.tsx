/**
 * Target & Scope context - persists current recon target and scope in the app.
 * Report History and Modules use this to remember the target across navigation.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const STORAGE_KEY_TARGET = 'planethack_target'
const STORAGE_KEY_SCOPE = 'planethack_scope'

function loadTarget(): string {
  try {
    const v = sessionStorage.getItem(STORAGE_KEY_TARGET)
    return v || ''
  } catch {}
  return ''
}

function loadScope(): string {
  try {
    const v = sessionStorage.getItem(STORAGE_KEY_SCOPE)
    return v || ''
  } catch {}
  return ''
}

function saveTarget(t: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY_TARGET, t)
  } catch {}
}

function saveScope(s: string) {
  try {
    sessionStorage.setItem(STORAGE_KEY_SCOPE, s)
  } catch {}
}

type TargetScopeContextValue = {
  target: string
  scope: string
  setTarget: (t: string) => void
  setScope: (s: string) => void
}

const TargetScopeContext = createContext<TargetScopeContextValue | null>(null)

export function TargetScopeProvider({ children }: { children: React.ReactNode }) {
  const [target, setTargetState] = useState(loadTarget)
  const [scope, setScopeState] = useState(loadScope)

  useEffect(() => {
    saveTarget(target)
  }, [target])

  useEffect(() => {
    saveScope(scope)
  }, [scope])

  const setTarget = useCallback((t: string) => {
    setTargetState(t.trim())
  }, [])

  const setScope = useCallback((s: string) => {
    setScopeState(s.trim())
  }, [])

  return (
    <TargetScopeContext.Provider value={{ target, scope, setTarget, setScope }}>
      {children}
    </TargetScopeContext.Provider>
  )
}

export function useTargetScope() {
  const ctx = useContext(TargetScopeContext)
  if (!ctx) throw new Error('useTargetScope must be used within TargetScopeProvider')
  return ctx
}
