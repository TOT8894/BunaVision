import type { Assessment, AssessmentListResponse } from '../../types/assessment'

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
  annotated_image_url: '/raw_beans_detected.png',
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
  predictions: [{ class_name: 'mock_defect_parchment_husk', confidence: 0.45, count: 1 }],
  original_image_url: '/raw_beans_detected.png',
  annotated_image_url: null,
  limitations: [
    'MOCK DATA: Development fixture only.',
    'Annotated image overlay is not supported or not available for this run.',
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

export const mockEmptyHistory: AssessmentListResponse = {
  items: [],
  next_cursor: null,
}

export const mockPaginatedHistoryPage1: AssessmentListResponse = {
  items: [mockCompletedAssessment, mockNoAnnotatedImageAssessment],
  next_cursor: 'mock-page-2',
}

export const mockPaginatedHistoryPage2: AssessmentListResponse = {
  items: [mockFailedAssessment],
  next_cursor: null,
}
