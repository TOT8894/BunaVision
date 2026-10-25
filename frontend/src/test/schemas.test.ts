import { describe, it, expect } from 'vitest'
import {
  assessmentSchema,
  predictionSchema,
  assessmentListResponseSchema,
} from '../schemas/assessment.schema'
import {
  mockCompletedAssessment,
  mockNoAnnotatedImageAssessment,
  mockFailedAssessment,
  mockPaginatedHistoryPage1,
} from '../mocks/fixtures'

describe('Zod Schemas', () => {
  it('validates a completed assessment fixture correctly', () => {
    const result = assessmentSchema.safeParse(mockCompletedAssessment)
    expect(result.success).toBe(true)
  })

  it('validates an assessment with no annotated image correctly', () => {
    const result = assessmentSchema.safeParse(mockNoAnnotatedImageAssessment)
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

  it('rejects predictions with confidence out of 0..1 bounds', () => {
    const invalidPrediction = { class_name: 'full_black', confidence: 1.5, count: 2 }
    const result = predictionSchema.safeParse(invalidPrediction)
    expect(result.success).toBe(false)
  })

  it('rejects assessments with missing required fields', () => {
    const malformed = { assessment_id: '123' }
    const result = assessmentSchema.safeParse(malformed)
    expect(result.success).toBe(false)
  })
})
