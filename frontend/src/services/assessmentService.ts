import axios from 'axios'
import { env } from '../config/env'
import type {
  BackendAssessment,
  BackendCompletedAssessment,
  BackendAssessmentListResponse,
  UnifiedAssessment,
  PredictionItem,
} from '../types/assessment'

const API_BASE = env.apiBaseUrl // e.g. 'http://localhost:8000/api/v1'

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
  const totalDefects = summary.detection_count

  // The model scans defect regions. For sample context, estimate bean spread
  const estimatedTotalBeans = Math.max(totalDefects * 6, 120)
  const normalBeans = Math.max(estimatedTotalBeans - totalDefects, 0)
  const defectPct =
    estimatedTotalBeans > 0
      ? parseFloat(((totalDefects / estimatedTotalBeans) * 100).toFixed(1))
      : 0

  const predictions: PredictionItem[] = [
    {
      class_name: 'Normal Green Bean',
      category_type: 'Healthy',
      confidence: 0.965,
      count: normalBeans,
    },
    ...summary.by_class.map((item) => ({
      class_name: item.defect.name,
      category_type: (item.defect.category === 'primary'
        ? 'Primary Defect'
        : 'Secondary Defect') as 'Primary Defect' | 'Secondary Defect',
      confidence: item.mean_confidence,
      count: item.count,
    })),
  ]

  const originalUrl =
    result.images.original_url ||
    extra?.fallbackImageUrl ||
    '/raw_beans_detected.png'

  const annotatedUrl =
    result.images.annotated_url || originalUrl

  return {
    assessment_id: backend.assessment_id,
    station_id: extra?.station_id || 'Yirgacheffe Station #04',
    lot_number: extra?.lot_number || 'YIR-2026-102',
    moisture_level: extra?.moisture_level || '11.0%',
    varietal: extra?.varietal || 'Heirloom',
    status: backend.status,
    model_version: result.model_version,
    created_at: backend.created_at,
    processing_time_ms: backend.processing_time_ms,
    summary: {
      total_beans_estimated: estimatedTotalBeans,
      normal_beans_count: normalBeans,
      defect_regions_count: totalDefects,
      defect_percentage: defectPct,
    },
    predictions,
    detections: result.detections,
    coverage: result.coverage,
    limitations: result.limitations,
    advisory: result.advisory,
    original_image_url: originalUrl,
    annotated_image_url: annotatedUrl,
    notes: extra?.notes || 'Live inference completed via BunaVision Backend API.',
    is_live_backend: true,
  }
}

/**
 * Attempts to submit an image file to the live backend POST /assessments
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
): Promise<UnifiedAssessment> {
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {
    'Content-Type': 'multipart/form-data',
  }

  if (options?.idempotencyKey) {
    headers['Idempotency-Key'] = options.idempotencyKey
  }

  const response = await axios.post<BackendCompletedAssessment>(
    `${API_BASE}/assessments`,
    formData,
    {
      headers,
      timeout: 35000,
    },
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
 * Fetches assessment history from live backend GET /assessments
 */
export async function fetchAssessmentsFromBackend(
  limit = 20,
  cursor?: string,
): Promise<BackendAssessmentListResponse> {
  const params: Record<string, string | number> = { limit }
  if (cursor) {
    params.cursor = cursor
  }
  const response = await axios.get<BackendAssessmentListResponse>(
    `${API_BASE}/assessments`,
    {
      params,
      timeout: 10000,
    },
  )
  return response.data
}

/**
 * Fetches single assessment from live backend GET /assessments/:id
 */
export async function fetchAssessmentByIdFromBackend(
  id: string,
): Promise<BackendAssessment> {
  const response = await axios.get<BackendAssessment>(
    `${API_BASE}/assessments/${encodeURIComponent(id)}`,
    { timeout: 10000 },
  )
  return response.data
}
