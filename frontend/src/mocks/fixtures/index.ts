<<<<<<< HEAD
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
=======
import type { Assessment } from '../../types/assessment'
import type { PaginatedListResponse } from '../../types/api'

/**
 * Clearly labeled mock fixtures for development and testing.
 * All class names, model versions, and text explicitly declare mock status
 * to prevent accidental confusion with real inference results.
 */

export const mockCompletedAssessment: Assessment = {
  assessment_id: 'mock-asm-completed-001',
  status: 'completed',
  model_version: 'MOCK-VISION-v0.1.0',
  created_at: '2026-10-22T20:00:00.000Z',
  completed_at: '2026-10-22T20:00:03.500Z',
  summary: {
    detected_classes: 2,
    detection_count: 5,
  },
  predictions: [
    { class_name: 'mock_defect_full_black', confidence: 0.94, count: 3 },
    { class_name: 'mock_defect_partial_black', confidence: 0.82, count: 2 },
  ],
  original_image_url: '/raw_beans_detected.png',
  annotated_image_url:
    '/raw_beans_detected.png',
  limitations: [
    'MOCK DATA: Development fixture only. Not a real coffee analysis.',
    'Results are preliminary AI predictions and not an official grade.',
    'Only supported visible defect classes are assessed.',
  ],
  error_code: null,
}

export const mockNoAnnotatedImageAssessment: Assessment = {
  assessment_id: 'mock-asm-no-annotated-002',
  status: 'completed',
  model_version: 'MOCK-VISION-v0.1.0',
  created_at: '2026-10-22T20:05:00.000Z',
  completed_at: '2026-10-22T20:05:02.100Z',
  summary: {
    detected_classes: 1,
    detection_count: 1,
  },
  predictions: [
    { class_name: 'mock_defect_parchment_husk', confidence: 0.45, count: 1 }, // < 0.50 threshold to test low-confidence badge
  ],
  original_image_url: '/raw_beans_detected.png',
  annotated_image_url: null, // Model did not produce an annotated image
  limitations: [
    'MOCK DATA: Development fixture only.',
    'Annotated image overlay is not supported or not available for this run.',
    'Hidden defects cannot be determined from a photograph.',
  ],
  error_code: null,
}

export const mockProcessingAssessment: Assessment = {
  assessment_id: 'mock-asm-processing-003',
  status: 'processing',
  model_version: 'MOCK-VISION-v0.1.0',
  created_at: new Date().toISOString(),
  completed_at: null,
  original_image_url: '/raw_beans_detected.png',
  annotated_image_url: null,
  limitations: ['MOCK DATA: Analysis is currently running in background.'],
}

export const mockFailedAssessment: Assessment = {
  assessment_id: 'mock-asm-failed-004',
  status: 'failed',
  model_version: 'MOCK-VISION-v0.1.0',
  created_at: '2026-10-22T20:10:00.000Z',
  completed_at: '2026-10-22T20:10:01.800Z',
  original_image_url: null,
  annotated_image_url: null,
  limitations: ['MOCK DATA: Image analysis could not be completed.'],
  error_code: 'INFERENCE_FAILED',
}

export const mockEmptyHistory: PaginatedListResponse<Assessment> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  has_more: false,
}

export const mockPaginatedHistoryPage1: PaginatedListResponse<Assessment> = {
  items: [mockCompletedAssessment, mockNoAnnotatedImageAssessment],
  total: 3,
  page: 1,
  page_size: 2,
  has_more: true,
}

export const mockPaginatedHistoryPage2: PaginatedListResponse<Assessment> = {
  items: [mockFailedAssessment],
  total: 3,
  page: 2,
  page_size: 2,
  has_more: false,
}
>>>>>>> 8e9eed04022f2410189e1110f0aad676a0e42e78
