import { describe, it, expect } from 'vitest'
import {
  assessmentSchema,
  assessmentListResponseSchema,
} from '../schemas/assessment.schema'
import {
  mockCompletedAssessment,
  mockFailedAssessment,
  mockPaginatedHistoryPage1,
} from '../mocks/fixtures'

describe('Zod Schemas', () => {
  it('validates a completed assessment fixture correctly', () => {
    const result = assessmentSchema.safeParse(mockCompletedAssessment)
    expect(result.success).toBe(true)
  })

  it('validates a failed assessment fixture correctly', () => {
    const result = assessmentSchema.safeParse(mockFailedAssessment)
    expect(result.success).toBe(true)
  })

  it('validates a paginated list response correctly', () => {
    const result = assessmentListResponseSchema.safeParse(mockPaginatedHistoryPage1)
    expect(result.success).toBe(true)
  })

  it('rejects assessments with missing required fields', () => {
    const malformed = {
      assessment_id: '123',
      // missing status and model_version
    }
    const result = assessmentSchema.safeParse(malformed)
    expect(result.success).toBe(false)
  })
})
