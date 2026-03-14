/**
 * OWASP-aligned input validation for support tickets.
 * Client-side defense in depth - server validates as well.
 */

export const LIMITS = {
  title: { min: 5, max: 200 },
  target: { max: 500 },
  steps: { max: 10000 },
  expected: { max: 10000 },
  actual: { max: 10000 },
} as const;

const ALLOWED_TYPES = new Set(['bug', 'feature', 'question']);
const ALLOWED_COMPONENTS = new Set([
  'web', 'gui', 'cli', 'recon', 'modules', 'docker', 'frontend',
]);

const PATH_TRAVERSAL = /\.\.\/|\.\.\\|\/\.\.|\\\.\./;

export interface SupportTicketPayload {
  title: string;
  type: string;
  component: string;
  target: string;
  steps: string;
  expected: string;
  actual: string;
}

export function validateSupportTicket(
  payload: Partial<SupportTicketPayload>
): { valid: boolean; error?: string; sanitized?: SupportTicketPayload } {
  const title = (payload.title || '').trim();
  if (title.length < LIMITS.title.min) {
    return { valid: false, error: `Title must be at least ${LIMITS.title.min} characters` };
  }
  if (title.length > LIMITS.title.max) {
    return { valid: false, error: `Title must be at most ${LIMITS.title.max} characters` };
  }
  if (PATH_TRAVERSAL.test(title)) {
    return { valid: false, error: 'Title contains invalid characters' };
  }

  const type = (payload.type || 'bug').trim().toLowerCase();
  if (!ALLOWED_TYPES.has(type)) {
    return { valid: false, error: 'Invalid type' };
  }

  const component = (payload.component || 'web').trim().toLowerCase();
  if (!ALLOWED_COMPONENTS.has(component)) {
    return { valid: false, error: 'Invalid component' };
  }

  const target = (payload.target || '').trim().slice(0, LIMITS.target.max);
  const steps = (payload.steps || '').trim().slice(0, LIMITS.steps.max);
  const expected = (payload.expected || '').trim().slice(0, LIMITS.expected.max);
  const actual = (payload.actual || '').trim().slice(0, LIMITS.actual.max);

  return {
    valid: true,
    sanitized: { title, type, component, target, steps, expected, actual },
  };
}

/** Escape for safe HTML output (XSS prevention) */
export function escapeHtml(s: string): string {
  const div = document.createElement('div');
  div.textContent = s ?? '';
  return div.innerHTML;
}
