"""
OWASP-aligned input validation for user-supplied data.
Used for support tickets, recon targets, and other untrusted input.

References: OWASP Top 10 2021
- A03: Injection (XSS, command, path traversal)
- A04: Insecure Design (DoS via oversized input)
"""

import re
from typing import Tuple, Optional
from html import escape as html_escape

# ── Limits (OWASP: prevent DoS, storage exhaustion) ─────────────────────────
MAX_TITLE_LEN = 200
MIN_TITLE_LEN = 5
MAX_TARGET_LEN = 500
MAX_TEXT_FIELD_LEN = 10_000
MAX_REQUEST_BODY_BYTES = 64 * 1024  # 64KB

# ── Allowlists (A03: Injection prevention) ──────────────────────────────────
ALLOWED_TICKET_TYPES = frozenset({"bug", "feature", "question"})
ALLOWED_COMPONENTS = frozenset(
    {
        "web",
        "gui",
        "cli",
        "recon",
        "modules",
        "docker",
        "frontend",
    }
)

# Dangerous patterns (strip or reject)
NULL_BYTE = re.compile(r"\x00")
PATH_TRAVERSAL = re.compile(r"\.\./|\.\.\\|/\.\.|\\\.\.")
SCRIPT_TAGS = re.compile(r"<script[^>]*>.*?</script>", re.I | re.S)
EVENT_HANDLERS = re.compile(r"\s+on\w+\s*=", re.I)
JAVASCRIPT_URI = re.compile(r"javascript\s*:", re.I)
DATA_URI = re.compile(r"data\s*:\s*[^,]*base64", re.I)


def strip_null_bytes(s: str) -> str:
    """Remove null bytes (injection vector)."""
    return NULL_BYTE.sub("", s) if s else ""


def sanitize_for_display(s: str) -> str:
    """Escape for safe HTML output (XSS prevention)."""
    if not isinstance(s, str):
        return ""
    return html_escape(s, quote=True)


def sanitize_for_storage(s: str) -> str:
    """Remove XSS vectors from text before storing (e.g. in markdown)."""
    if not s:
        return ""
    s = SCRIPT_TAGS.sub("", s)
    s = EVENT_HANDLERS.sub(" ", s)
    s = JAVASCRIPT_URI.sub(" ", s)
    s = DATA_URI.sub(" ", s)
    return s


def sanitize_for_filename(s: str, max_len: int = 60) -> str:
    """Safe filename segment: alphanumeric, dash, underscore only."""
    if not s:
        return "ticket"
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in s)
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe[:max_len] if safe else "ticket"


def validate_support_ticket(data: dict) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Validate support ticket payload. OWASP-aligned.
    Returns (ok, error_message, sanitized_data).
    """
    if not isinstance(data, dict):
        return False, "Invalid request body", None

    # Length check (A04 - DoS)
    raw = str(data)[:1000]  # rough check
    if len(raw.encode("utf-8", errors="replace")) > MAX_REQUEST_BODY_BYTES:
        return False, f"Payload too large (max {MAX_REQUEST_BODY_BYTES} bytes)", None

    # Title (required)
    title = (data.get("title") or "").strip()
    title = strip_null_bytes(title)
    if len(title) < MIN_TITLE_LEN:
        return False, f"Title must be at least {MIN_TITLE_LEN} characters", None
    if len(title) > MAX_TITLE_LEN:
        return False, f"Title must be at most {MAX_TITLE_LEN} characters", None
    if PATH_TRAVERSAL.search(title):
        return False, "Title contains invalid path characters", None
    title = sanitize_for_storage(title)

    # Type (allowlist)
    ticket_type = (data.get("type") or "bug").strip().lower()
    if ticket_type not in ALLOWED_TICKET_TYPES:
        ticket_type = "bug"

    # Component (allowlist)
    component = (data.get("component") or "web").strip().lower()
    if component not in ALLOWED_COMPONENTS:
        component = "web"

    # Target (optional, bounded)
    target = (data.get("target") or "").strip()
    target = strip_null_bytes(target)
    if len(target) > MAX_TARGET_LEN:
        target = target[:MAX_TARGET_LEN]
    target = sanitize_for_storage(target)

    # Text fields (optional, bounded, strip nulls)
    def clamp(s: str, max_len: int) -> str:
        s = strip_null_bytes((s or "").strip())
        return s[:max_len] if len(s) > max_len else s

    steps = sanitize_for_storage(clamp(data.get("steps") or "", MAX_TEXT_FIELD_LEN))
    expected = sanitize_for_storage(
        clamp(data.get("expected") or "", MAX_TEXT_FIELD_LEN)
    )
    actual = sanitize_for_storage(clamp(data.get("actual") or "", MAX_TEXT_FIELD_LEN))

    return (
        True,
        None,
        {
            "title": title,
            "type": ticket_type,
            "component": component,
            "target": target,
            "steps": steps,
            "expected": expected,
            "actual": actual,
        },
    )
