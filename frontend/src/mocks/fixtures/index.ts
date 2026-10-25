import type { Assessment, AssessmentListResponse } from '../../types/assessment'

const fullBlack = { key: 'full_black', name: 'Full Black', category: 'primary' as const }
const partialBlack = { key: 'partial_black', name: 'Partial Black', category: 'secondary' as const }

export const mockCompletedAssessment: Assessment = {
  assessment_id: 'mock-asm-completed-001', status: 'completed', created_at: '2026-10-22T20:00:00.000Z', processing_time_ms: 3500,
  result: {
    model_version: 'MOCK-VISION-v0.1.0', summary: { detection_count: 5, primary_detection_count: 3, secondary_detection_count: 2, by_class: [{ defect: fullBlack, count: 3, mean_confidence: 0.94 }, { defect: partialBlack, count: 2, mean_confidence: 0.42 }] },
    detections: [], coverage: { scanned: [fullBlack, partialBlack], not_scanned: [] }, limitations: [{ code: 'MOCK_DATA', message: 'MOCK DATA: Development fixture only. Not a real coffee analysis.' }],
    advisory: { generator_model: 'mock-advisory', summary: { en: 'Example development result.', am: 'Mock advisory.' }, recommendations: [] }, images: { original_url: null, annotated_url: null, expires_in_s: 900 },
  },
}
export const mockFailedAssessment: Assessment = { assessment_id: 'mock-asm-failed-004', status: 'failed', created_at: '2026-10-22T20:10:00.000Z', processing_time_ms: 1800, error_code: 'INFERENCE_FAILED' }
export const mockEmptyHistory: AssessmentListResponse = { items: [], next_cursor: null }
export const mockPaginatedHistoryPage1: AssessmentListResponse = { items: [{ assessment_id: 'mock-asm-completed-001', status: 'completed', created_at: '2026-10-22T20:00:00.000Z', model_version: 'MOCK-VISION-v0.1.0', detection_count: 5, primary_detection_count: 3, secondary_detection_count: 2 }], next_cursor: 'mock-page-2' }
export const mockPaginatedHistoryPage2: AssessmentListResponse = { items: [{ assessment_id: 'mock-asm-failed-004', status: 'failed', created_at: '2026-10-22T20:10:00.000Z', error_code: 'INFERENCE_FAILED' }], next_cursor: null }
