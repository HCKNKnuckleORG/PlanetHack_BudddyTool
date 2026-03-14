/**
 * PlanetHack API client - fetches from Python backend /api/v1
 */

const API_BASE = '/api/v1';

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

export const api = {
  health: () => fetchApi<{ status: string; api: string }>('/health'),
  quote: () => fetchApi<{ quote: string; movie: string }>('/quote'),
  modules: () => fetchApi<{ modules: Array<{ id: string; name: string; color: string; group?: string }> }>('/modules'),
  modulesReady: (target?: string) =>
    fetchApi<{ ready: string[]; not_ready: Array<{ id: string; reason: string }>; target: string }>(
      target ? `/modules/ready?target=${encodeURIComponent(target)}` : '/modules/ready'
    ),
  recon: {
    preflight: (target: string, preset: string) =>
      fetchApi('/recon/preflight', {
        method: 'POST',
        body: JSON.stringify({ target, preset }),
      }),
    plan: (target: string, preset: string) =>
      fetchApi<{ phases: unknown[]; target: string }>('/recon/plan', {
        method: 'POST',
        body: JSON.stringify({ target, preset }),
      }),
    execute: (phases: unknown[], target: string, preset?: string) =>
      fetchApi<{ job_id: string }>('/recon/execute', {
        method: 'POST',
        body: JSON.stringify({ phases, target, preset: preset || 'full' }),
      }),
    confirm: (jobId: string, cont: boolean) =>
      fetchApi('/recon/confirm/' + jobId, {
        method: 'POST',
        body: JSON.stringify({ continue: cont }),
      }),
  },
  stream: (jobId: string) => `${API_BASE}/stream/${jobId}`,
  findings: (jobId: string) => fetchApi<{ summary: unknown; next_steps: unknown[]; target: string }>(`/findings/${jobId}`),
  jobConfirmReport: (jobId: string) =>
    fetchApi<{ ok: boolean; target?: string }>(`/jobs/${jobId}/confirm-report`, { method: 'POST' }),
  session: {
    findings: () =>
      fetchApi<{ summary: unknown; findings_by_tool?: unknown; next_steps: unknown[]; history: unknown[]; target?: string; log_file?: string }>('/session/findings'),
  },
  nextStepExecute: (command: string, target?: string) =>
    fetchApi<{ job_id: string }>('/nextsteps/execute', {
      method: 'POST',
      body: JSON.stringify({ command, target: target || '' }),
    }),
  moduleCommand: (moduleId: string, target: string) =>
    fetchApi<{ command: string }>(`/modules/${moduleId}/command?target=${encodeURIComponent(target)}`),
  moduleRun: (moduleId: string, target: string, preset?: string, command?: string) =>
    fetchApi<{ job_id?: string; redirect?: string }>('/modules/run', {
      method: 'POST',
      body: JSON.stringify(
        Object.assign(
          { module_id: moduleId, target },
          preset ? { preset } : {},
          command ? { command } : {}
        )
      ),
    }),
  ai: {
    improvePayload: (payload: string, moduleId?: string) =>
      fetchApi<{ improved: string }>('/ai/improve-payload', {
        method: 'POST',
        body: JSON.stringify({ payload, module_id: moduleId || '' }),
      }),
    analyzeResponse: (command: string, output: string) =>
      fetchApi<{ analysis: string }>('/ai/analyze-response', {
        method: 'POST',
        body: JSON.stringify({ command, output }),
      }),
  },
  support: {
    submitTicket: (payload: {
      title: string;
      type?: string;
      component?: string;
      target?: string;
      steps?: string;
      expected?: string;
      actual?: string;
    }) =>
      fetchApi<{ ticket_id: string; path: string }>('/support/ticket', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
};
