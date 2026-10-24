import type { ErrorCode } from './api'

export type AssessmentStatus = 'completed' | 'failed' | 'processing' | 'pending'

export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface DefectClass {
  key: string
  name: string
  category: 'primary' | 'secondary' | 'Healthy' | 'Primary Defect' | 'Secondary Defect'
}

export interface Detection {
  defect: DefectClass
  confidence: number // 0 to 1
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

// ----------------------------------------------------
// Frontend UI Unified Data Structures
// ----------------------------------------------------
export interface PredictionItem {
  class_name: string
  category_type: 'Healthy' | 'Primary Defect' | 'Secondary Defect'
  confidence: number // 0 to 1
  count: number
}

export interface AssessmentSummaryUI {
  total_beans_estimated: number
  normal_beans_count: number
  defect_regions_count: number
  defect_percentage: number
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

// ----------------------------------------------------
// Legacy / MSW Mock Compat Types
// ----------------------------------------------------
export interface Prediction {
  class_name: string
  confidence: number
  count: number
}

export interface AssessmentSummary {
  detected_classes: number
  detection_count: number
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
}
