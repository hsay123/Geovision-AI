"""Google Earth Engine client initialization and connectivity checks."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

import ee

GEE_PROJECT_ID = "project-326ab593-31e9-43ed-8cd"

_initialized = False


class GeeUnavailableError(RuntimeError):
    """Raised when GEE cannot be reached or the project is not authorized."""


def initialize(project: str = GEE_PROJECT_ID) -> None:
    """Initialize the Earth Engine session exactly once per process."""
    global _initialized
    if _initialized:
        return
    try:
        ee.Initialize(project=project)
    except Exception as exc:  # ee.EEException / auth errors
        raise GeeUnavailableError(
            f"Failed to initialize Google Earth Engine with project '{project}': {exc}"
        ) from exc
    _initialized = True


def check_connectivity(project: str = GEE_PROJECT_ID, timeout_s: float = 8.0) -> bool:
    """Return True if GEE is reachable and responds to a trivial request.

    The probe runs on a worker thread with a hard ``timeout_s`` so a GEE
    network outage can never wedge the server (the ee client has no read
    timeout of its own and would otherwise hang startup /health for minutes).
    """
    initialize(project)

    def _probe() -> bool:
        # Cheap round-trip that proves auth + network + project access.
        return ee.Number(1).add(1).getInfo() == 2

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(_probe)
        try:
            return future.result(timeout=timeout_s)
        except FutureTimeout:
            return False
        except Exception:
            return False
    finally:
        # Never block on the abandoned probe thread (GEE has no read timeout).
        pool.shutdown(wait=False)
