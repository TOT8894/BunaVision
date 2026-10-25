import { apiClient } from '../api/apiClient'
import { assessmentListResponseSchema, assessmentSchema } from '../schemas/assessment.schema'
import type { Assessment, AssessmentListResponse } from '../types/assessment'

export const assessmentApi = {
  getAssessment: (assessmentId: string): Promise<Assessment> => apiClient.get(`/assessments/${encodeURIComponent(assessmentId)}`, { schema: assessmentSchema }),
  listAssessments: (params: { cursor?: string | null; limit?: number } = {}): Promise<AssessmentListResponse> => apiClient.get('/assessments', { params, schema: assessmentListResponseSchema }),
}
