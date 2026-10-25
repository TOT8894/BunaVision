import axios from 'axios'
import { env } from '../config/env'
import type {
  BackendAssessment,
  BackendCompletedAssessment,
  BackendAssessmentListResponse,
  UnifiedAssessment,
  PredictionItem,
} from '../types/assessment'

const API_BASE = env.apiBaseUrl

/**
 * Checks if the backend server is reachable via /health
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const origin = API_BASE.replace(/\/api\/v1\/?$/, '')
    const res = await axios.get(`${origin}/health`, { timeout: 2500 })
    return res.status === 200 && res.data?.status === 'ok'
  } catch {
    return false
  }
}

/**
 * Transforms a real BackendCompletedAssessment into the UI's UnifiedAssessment model
 */
export function mapBackendToUnified(
  backend: BackendCompletedAssessment,
  extra?: {
    station_id?: string
    lot_number?: string
    moisture_level?: string
    varietal?: string
    notes?: string
    fallbackImageUrl?: string
  },
): UnifiedAssessment {
  const result = backend.result
  const summary = result.summary

  const predictions: PredictionItem[] = summary.by_class.map((item) => ({
    class_name: item.defect.name,
    category_type: (item.defect.category === 'primary'
      ? 'Primary Defect'
      : 'Secondary Defect') as 'Primary Defect' | 'Secondary Defect',
    confidence: item.mean_confidence,
    count: item.count,
  }))

  const originalUrl =
    result.images.original_url || extra?.fallbackImageUrl || '/raw_beans_detected.png'

  const annotatedUrl = result.images.annotated_url || originalUrl

  return {
    assessment_id: backend.assessment_id,
    station_id: extra?.station_id || 'Primary Washing Station',
    lot_number: extra?.lot_number,
    moisture_level: extra?.moisture_level,
    varietal: extra?.varietal,
    status: backend.status,
    model_version: result.model_version,
    created_at: backend.created_at,
    processing_time_ms: backend.processing_time_ms,
    summary: {
      detection_count: summary.detection_count,
      primary_detection_count: summary.primary_detection_count,
      secondary_detection_count: summary.secondary_detection_count,
      by_class: summary.by_class,
    },
    predictions,
    detections: result.detections,
    coverage: result.coverage,
    limitations: result.limitations,
    advisory: result.advisory,
    original_image_url: originalUrl,
    annotated_image_url: annotatedUrl,
    notes: extra?.notes,
    is_live_backend: true,
  }
}

/**
 * Submits an image file to the live backend POST /api/v1/assessments
 */
export async function uploadAssessmentToBackend(
  file: File,
  options?: {
    idempotencyKey?: string
    station_id?: string
    lot_number?: string
    moisture_level?: string
    varietal?: string
    notes?: string
  },
  token?: string,
): Promise<UnifiedAssessment> {
  const formData = new FormData()
  formData.append('image', file)

  const headers: Record<string, string> = {}
  if (options?.idempotencyKey) {
    headers['Idempotency-Key'] = options.idempotencyKey
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await axios.post<BackendCompletedAssessment>(
    `${API_BASE}/assessments`,
    formData,
    { headers, timeout: 35000 },
  )

  const previewFallback = URL.createObjectURL(file)
  return mapBackendToUnified(response.data, {
    station_id: options?.station_id,
    lot_number: options?.lot_number,
    moisture_level: options?.moisture_level,
    varietal: options?.varietal,
    notes: options?.notes,
    fallbackImageUrl: previewFallback,
  })
}

/**
 * Fetches assessment history from the backend GET /api/v1/assessments
 */
export async function fetchAssessmentsFromBackend(
  limit = 20,
  cursor?: string,
  token?: string,
): Promise<BackendAssessmentListResponse> {
  const params: Record<string, string | number> = { limit }
  if (cursor) params.cursor = cursor

  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await axios.get<BackendAssessmentListResponse>(`${API_BASE}/assessments`, {
    params,
    headers,
    timeout: 10000,
  })
  return response.data
}

/**
 * Fetches a single assessment from the backend GET /api/v1/assessments/:id
 */
export async function fetchAssessmentByIdFromBackend(
  id: string,
  token?: string,
): Promise<BackendAssessment> {
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await axios.get<BackendAssessment>(
    `${API_BASE}/assessments/${encodeURIComponent(id)}`,
    { headers, timeout: 10000 },
  )
  return response.data
}
