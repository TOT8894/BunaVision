const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

function integerEnvironmentValue(name: string, fallback: number): number { const value = import.meta.env[name]; if (!value) return fallback; const parsed = Number(value); return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback }

export const env = { apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL, maxUploadMb: integerEnvironmentValue('VITE_MAX_UPLOAD_MB', 15), minImagePx: integerEnvironmentValue('VITE_MIN_IMAGE_PX', 640), requestTimeoutMs: integerEnvironmentValue('VITE_REQUEST_TIMEOUT_MS', 60_000) } as const
