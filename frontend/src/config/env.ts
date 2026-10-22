const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

function parseIntegerEnv(key: string, fallback: number): number {
  const raw = import.meta.env[key]
  if (!raw) return fallback
  const parsed = Number.parseInt(String(raw), 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function parseFloatEnv(key: string, fallback: number): number {
  const raw = import.meta.env[key]
  if (!raw) return fallback
  const parsed = Number.parseFloat(String(raw))
  return Number.isFinite(parsed) && parsed >= 0 && parsed <= 1 ? parsed : fallback
}

function parseBooleanEnv(key: string, fallback: boolean): boolean {
  const raw = import.meta.env[key]
  if (raw === undefined || raw === null || raw === '') return fallback
  return String(raw).toLowerCase() === 'true'
}

export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL,
  maxUploadMb: parseIntegerEnv('VITE_MAX_UPLOAD_MB', 10),
  minImagePx: parseIntegerEnv('VITE_MIN_IMAGE_PX', 640),
  lowConfidenceThreshold: parseFloatEnv('VITE_LOW_CONFIDENCE_THRESHOLD', 0.5),
  pollIntervalMs: parseIntegerEnv('VITE_POLL_INTERVAL_MS', 2000),
  requestTimeoutMs: parseIntegerEnv('VITE_REQUEST_TIMEOUT_MS', 60_000),
  useMocks: parseBooleanEnv('VITE_USE_MOCKS', false),
} as const

export type EnvConfig = typeof env
