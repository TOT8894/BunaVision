import type { ErrorCode } from './api'

export type AssessmentStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Prediction {
  class_name: string
  confidence: number // 0..1, model confidence
  count: number // count of detected defect instances/regions
}

export interface AssessmentSummary {
  detected_classes: number
  detection_count: number
}

export interface Assessment {
  assessment_id: string
  status: AssessmentStatus
  model_version: string
  created_at: string // ISO 8601 string
  completed_at?: string | null
  summary?: AssessmentSummary
  predictions?: Prediction[]
  original_image_url?: string | null // presigned, short-lived URL
  annotated_image_url: string | null // presigned URL, or null if unsupported
  limitations: string[]
  error_code?: ErrorCode | null
}
