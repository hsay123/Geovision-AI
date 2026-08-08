const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

//: Hard client-side cap so the UI can never hang forever on a stalled request
//: (Phase 19d). Independent of backend timeouts — belt and suspenders.
//: 180 s (was 90 s) — tonight's elevated GEE latency made legitimate live runs
//: (thumbnails especially) exceed 90 s while still progressing.
export const ANALYZE_TIMEOUT_MS = 180_000;

async function postAnalyze(payload, signal) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  let body;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    let message;
    if (Array.isArray(body?.detail)) {
      message = body.detail.map((d) => d.msg).filter(Boolean).join(" ");
    } else {
      message = body?.detail?.error ?? body?.detail ?? body?.error;
    }
    message = message ?? `Request failed (HTTP ${res.status})`;
    throw new Error(message);
  }
  return body;
}

async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) return { status: "degraded", gee_connected: false };
  try {
    return await res.json();
  } catch {
    return { status: "degraded", gee_connected: false };
  }
}

async function getWatchlist() {
  const res = await fetch(`${API_BASE}/watchlist`);
  if (!res.ok) throw new Error(`Watchlist request failed (HTTP ${res.status})`);
  const body = await res.json();
  return Array.isArray(body) ? body : [];
}

export { postAnalyze, getHealth, getWatchlist };
