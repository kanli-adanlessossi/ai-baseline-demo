// The only HTTP client in this service (see services/web/AGENTS.md).
const DEFAULT_TIMEOUT_MS = 5000;

export type Fetch = typeof fetch;

export async function getJson(url: string, fetchImpl: Fetch = fetch): Promise<unknown> {
  const res = await fetchImpl(url, { signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS) });
  if (!res.ok) throw new Error(`GET ${url} failed with status ${res.status}`);
  return res.json();
}
