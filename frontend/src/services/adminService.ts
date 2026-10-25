import axios from 'axios'
import { env } from '../config/env'

const API_BASE = env.apiBaseUrl

export interface OutcomeItem {
  status: 'completed' | 'failed'
  error_code: string | null
  count: number
}

export interface AdminOverviewResponse {
  since: string
  window_hours: number
  outcomes: OutcomeItem[]
}

export interface ModelVersionUsage {
  model_version: string
  validator_version: string
  assessments: number
  first_seen: string
  last_seen: string
}

export interface AdminModelVersionsResponse {
  versions: ModelVersionUsage[]
}

export interface AdminLimitsResponse {
  max_image_bytes: number
  max_image_pixels: number
  min_image_side_px: number
  max_assessments_per_user_per_hour: number
  max_concurrent_assessments: number
  vision_timeout_s: number
  gemini_timeout_s: number
  image_url_ttl_s: number
  retain_original_image: boolean
}

export interface AdminAssessmentItem {
  assessment_id: string
  owner_id: string
  status: 'completed' | 'failed'
  created_at: string
  processing_time_ms: number
  error_code?: string | null
  model_version?: string
  validator_version?: string
  detection_count?: number
}

export interface AdminAssessmentListResponse {
  items: AdminAssessmentItem[]
  next_cursor: string | null
}

export interface AdminReloadModelResponse {
  reloaded: boolean
  engine: string
}

export async function fetchAdminOverview(
  windowHours = 24,
  token: string,
): Promise<AdminOverviewResponse> {
  const response = await axios.get<AdminOverviewResponse>(
    `${API_BASE}/admin/overview`,
    {
      params: { window_hours: windowHours },
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000,
    },
  )
  return response.data
}

export async function fetchAdminModelVersions(
  token: string,
): Promise<AdminModelVersionsResponse> {
  const response = await axios.get<AdminModelVersionsResponse>(
    `${API_BASE}/admin/model-versions`,
    {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000,
    },
  )
  return response.data
}

export async function fetchAdminLimits(token: string): Promise<AdminLimitsResponse> {
  const response = await axios.get<AdminLimitsResponse>(
    `${API_BASE}/admin/limits`,
    {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000,
    },
  )
  return response.data
}

export async function fetchAdminAssessments(
  token: string,
  filters?: {
    status?: 'completed' | 'failed'
    error_code?: string
    owner_id?: string
    cursor?: string
    limit?: number
  },
): Promise<AdminAssessmentListResponse> {
  const params: Record<string, string | number> = {}
  if (filters?.status) params.status = filters.status
  if (filters?.error_code) params.error_code = filters.error_code
  if (filters?.owner_id) params.owner_id = filters.owner_id
  if (filters?.cursor) params.cursor = filters.cursor
  if (filters?.limit) params.limit = filters.limit

  const response = await axios.get<AdminAssessmentListResponse>(
    `${API_BASE}/admin/assessments`,
    {
      params,
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000,
    },
  )
  return response.data
}

export async function reloadVisionModel(
  token: string,
): Promise<AdminReloadModelResponse> {
  const response = await axios.post<AdminReloadModelResponse>(
    `${API_BASE}/admin/vision/reload-model`,
    {},
    {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 25000,
    },
  )
  return response.data
}
