import type { ErrorCode } from './api'

export type AssessmentStatus = 'completed' | 'failed'
export type DefectCategory = 'primary' | 'secondary'
export interface DefectClass { key: string; name: string; category: DefectCategory }
export interface ClassTally { defect: DefectClass; count: number; mean_confidence: number }
export interface Detection { defect: DefectClass; confidence: number; box: { x1: number; y1: number; x2: number; y2: number } }
export interface CompletedAssessment {
  assessment_id: string; status: 'completed'; created_at: string; processing_time_ms: number
  result: {
    model_version: string
    summary: { detection_count: number; primary_detection_count: number; secondary_detection_count: number; by_class: ClassTally[] }
    detections: Detection[]
    coverage: { scanned: DefectClass[]; not_scanned: DefectClass[] }
    limitations: { code: string; message: string }[]
    advisory: { generator_model: string; summary: { en: string; am: string }; recommendations: { en: string; am: string }[] }
    images: { original_url: string | null; annotated_url: string | null; expires_in_s: number }
  }
}
export interface FailedAssessment { assessment_id: string; status: 'failed'; created_at: string; processing_time_ms: number; error_code: ErrorCode }
export type Assessment = CompletedAssessment | FailedAssessment
export type AssessmentListItem =
  | (Pick<CompletedAssessment, 'assessment_id' | 'status' | 'created_at'> & { model_version: string; detection_count: number; primary_detection_count: number; secondary_detection_count: number })
  | (Pick<FailedAssessment, 'assessment_id' | 'status' | 'created_at' | 'error_code'>)
export interface AssessmentListResponse { items: AssessmentListItem[]; next_cursor: string | null }
