"""
Job store for async recon/module execution and SSE streaming.
Shared by Flask routes and API blueprint.
Output is buffered so reconnects (e.g. after page refresh) can replay.
"""

import logging
import time
import uuid
import threading
from queue import Queue, Empty
from typing import Dict, Any, Optional, List


_MAX_BUFFER_ITEMS = 50000  # cap to prevent memory explosion from heavy tools (gobuster, nuclei)


class BufferedQueue(Queue):
    """Queue that keeps a buffer of all items for replay on reconnect. Capped to avoid VM overload."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer: List[Any] = []
        self._buf_lock = threading.Lock()

    def put(self, item, *args, **kwargs):
        with self._buf_lock:
            self._buffer.append(item)
            if len(self._buffer) > _MAX_BUFFER_ITEMS:
                # keep last N, drop oldest
                self._buffer = self._buffer[-_MAX_BUFFER_ITEMS:]
        super().put(item, *args, **kwargs)

    def get_buffer_snapshot(self) -> List[Any]:
        with self._buf_lock:
            return list(self._buffer)


_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()
_CLEANUP_AGE = 600  # seconds
_MAX_JOBS = 50  # prevent unbounded growth / overload

_log = logging.getLogger(__name__)


def cleanup_old_jobs() -> None:
    now = time.time()
    with _jobs_lock:
        stale = [jid for jid, j in _jobs.items() if now - j["created"] > _CLEANUP_AGE]
        for jid in stale:
            del _jobs[jid]
        if stale:
            _log.debug(f"cleanup_old_jobs: removed {len(stale)} stale job(s)")
        if len(_jobs) > _MAX_JOBS:
            oldest = sorted(_jobs.items(), key=lambda x: x[1]["created"])[: len(_jobs) - _MAX_JOBS]
            for jid, _ in oldest:
                del _jobs[jid]
            _log.warning(f"cleanup_old_jobs: job limit reached, evicted {len(oldest)} oldest job(s)")


def create_job(target: str = "") -> str:
    cleanup_old_jobs()
    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "queue": BufferedQueue(),
            "created": time.time(),
            "done": False,
            "target": target,
            "collected_output": {},
            "report": None,
            "confirm_event": threading.Event(),
            "confirm_choice": True,
        }
        _log.debug(f"create_job: job_id={job_id} target={target!r} total_jobs={len(_jobs)}")
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    with _jobs_lock:
        return _jobs.get(job_id)
