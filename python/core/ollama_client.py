"""
Ollama client for AI-assisted payload improvement and response analysis.
Uses local Ollama instance (e.g. http://localhost:11434).
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _get_config():
    try:
        from flask import current_app
        cfg = current_app.config.get("PH_CONFIG")
        if cfg is None:
            return {}
        if isinstance(cfg, dict):
            return cfg.get("ollama", {}) or {}
        return getattr(cfg, "ollama", {}) or {}
    except Exception:
        return {}


def ollama_generate(prompt: str, system: Optional[str] = None) -> Tuple[bool, str]:
    """
    Call Ollama /api/generate with the given prompt.
    Returns (success, response_text or error_message).
    """
    config = _get_config()
    if not config.get("enabled", False):
        return False, "Ollama is disabled in config"
    url = (config.get("url") or "http://localhost:11434").rstrip("/") + "/api/generate"
    model = config.get("model") or "llama3"

    try:
        import requests
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
        return True, text
    except Exception as e:
        logger.warning("Ollama generate failed: %s", e)
        return False, str(e)


def improve_payload(payload: str, module_context: str = "") -> Tuple[bool, str]:
    """
    Ask Ollama to improve a security testing payload/command.
    Returns (success, improved_payload_or_error).
    """
    system = (
        "You are a helpful security testing assistant. "
        "Given a security testing command or payload, suggest an improved version. "
        "Return ONLY the improved command or payload, no explanation. "
        "Keep it practical and ready to run."
    )
    ctx = f" (module context: {module_context})" if module_context else ""
    prompt = f"Improve this security testing command/payload{ctx}.\n\nOriginal:\n{payload}\n\nImproved (command/payload only, no explanation):"
    return ollama_generate(prompt, system=system)


def analyze_response(command: str, output: str) -> Tuple[bool, str]:
    """
    Ask Ollama to analyze command output for security findings.
    Returns (success, analysis_text_or_error).
    """
    system = (
        "You are a helpful security analyst. "
        "Analyze the command output and summarize: potential vulnerabilities, interesting findings, suggested next steps. "
        "Be concise and actionable."
    )
    prompt = f"Command run:\n{command}\n\nOutput:\n{output[:8000]}\n\nAnalysis (concise):"
    return ollama_generate(prompt, system=system)
