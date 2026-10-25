import type { ErrorCode } from './api'

// -------------------------------------------------------
// Shared enums and primitives
// -------------------------------------------------------
export type AssessmentStatus = 'completed' | 'failed' | 'processing' | 'pending'
export type DefectCategory = 'primary' | 'secondary'

export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface DefectClass {
  key: string
  name: string
  category: 'primary' | 'secondary'
}

export interface Detection {
  defect: DefectClass
  confidence: number
  box?: BoundingBox
}

export interface ClassTally {
  defect: DefectClass
  count: number
  mean_confidence: number
}

export interface BackendSummary {
  detection_count: number
  primary_detection_count: number
  secondary_detection_count: number
  by_class: ClassTally[]
}

export interface Coverage {
  scanned: DefectClass[]
  not_scanned: DefectClass[]
}

export interface Limitation {
  code: string
  message: string
}

export interface BilingualText {
  en: string
  am: string
}

export interface Advisory {
  generator_model: string
  summary: BilingualText
  recommendations: BilingualText[]
}

export interface Images {
  original_url: string | null
  annotated_url: string | null
  expires_in_s?: number
}

export interface BackendAssessmentResult {
  model_version: string
  image_check?: { is_coffee: true; coffee_confidence: number; validator_version: string }
  summary: BackendSummary
  detections: Detection[]
  coverage: Coverage
  limitations: Limitation[]
  advisory?: Advisory
  images: Images
}

export interface BackendCompletedAssessment {
  assessment_id: string
  status: 'completed'
  created_at: string
  processing_time_ms: number
  result: BackendAssessmentResult
}

export interface BackendFailedAssessment {
  assessment_id: string
  status: 'failed'
  created_at: string
  processing_time_ms: number
  error_code: ErrorCode
}

export type BackendAssessment = BackendCompletedAssessment | BackendFailedAssessment

export interface BackendAssessmentListItem {
  assessment_id: string
  status: 'completed' | 'failed'
  created_at: string
  model_version?: string
  detection_count?: number
  primary_detection_count?: number
  secondary_detection_count?: number
  error_code?: ErrorCode
}

export interface BackendAssessmentListResponse {
  items: BackendAssessmentListItem[]
  next_cursor: string | null
}

// -------------------------------------------------------
// Frontend UI unified data structures
// -------------------------------------------------------
export interface PredictionItem {
  class_name: string
  category_type: 'Healthy' | 'Primary Defect' | 'Secondary Defect'
  confidence: number
  count: number
}

export interface AssessmentSummaryUI {
  detection_count: number
  primary_detection_count: number
  secondary_detection_count: number
  by_class: ClassTally[]
}

export interface UnifiedAssessment {
  assessment_id: string
  station_id: string
  lot_number?: string
  moisture_level?: string
  varietal?: string
  status: AssessmentStatus
  model_version: string
  created_at: string
  processing_time_ms?: number
  summary: AssessmentSummaryUI
  predictions: PredictionItem[]
  detections?: Detection[]
  coverage?: Coverage
  limitations?: Limitation[]
  advisory?: Advisory
  original_image_url: string
  annotated_image_url: string
  notes?: string
  is_live_backend?: boolean
  error_code?: ErrorCode | null
}

// -------------------------------------------------------
// Legacy / assessmentApi.ts compat types
// -------------------------------------------------------
export interface AssessmentSummary {
  detected_classes: number
  detection_count: number
}

export interface Prediction {
  class_name: string
  confidence: number
  count: number
}

export interface Assessment {
  assessment_id: string
  status: AssessmentStatus
  model_version: string
  created_at: string
  completed_at?: string | null
  summary?: AssessmentSummary
  predictions?: Prediction[]
  original_image_url?: string | null
  annotated_image_url: string | null
  limitations: string[]
  error_code?: ErrorCode | null
  detection_count?: number
}

export interface AssessmentListResponse {
  items: Assessment[]
  next_cursor: string | null
}

// Type aliases for features/assessment components
export type CompletedAssessment = BackendCompletedAssessment
export type FailedAssessment = BackendFailedAssessment
