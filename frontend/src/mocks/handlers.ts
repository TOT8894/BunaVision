import { http, HttpResponse } from 'msw'
import {
  mockCompletedAssessment,
  mockNoAnnotatedImageAssessment,
  mockProcessingAssessment,
  mockFailedAssessment,
  mockEmptyHistory,
  mockPaginatedHistoryPage1,
  mockPaginatedHistoryPage2,
} from './fixtures'
import type { Assessment } from '../types/assessment'

// Polling simulation state: assessmentId -> poll count
const pollingCounts = new Map<string, number>()

export const handlers = [
  // POST /api/v1/assessments — Submit an image for assessment
  http.post('*/api/v1/assessments', async ({ request }) => {
    const url = new URL(request.url)
    const mockParam = url.searchParams.get('mock')

    // Allow tests or dev to trigger specific scenarios via ?mock=...
    if (mockParam === 'failed') {
      return HttpResponse.json(
        {
          error: {
            code: 'INFERENCE_FAILED',
            message: "The analysis didn't complete. Your image was not assessed.",
          },
        },
        { status: 500 },
      )
    }

    if (mockParam === 'rate_limited') {
      return HttpResponse.json(
        {
          error: {
            code: 'RATE_LIMITED',
            message: 'Too many requests. Please wait a moment and try again.',
          },
        },
        { status: 429, headers: { 'Retry-After': '5' } },
      )
    }

    if (mockParam === 'invalid_format') {
      return HttpResponse.json(
        {
          error: {
            code: 'UNSUPPORTED_FORMAT',
            message: "This file type isn't supported. Please upload a JPEG or PNG photo.",
          },
        },
        { status: 400 },
      )
    }

    if (mockParam === 'processing') {
      const processingId = `mock-asm-dyn-proc-${Date.now()}`
      pollingCounts.set(processingId, 0)
      return HttpResponse.json(
        {
          ...mockProcessingAssessment,
          assessment_id: processingId,
        },
        { status: 202 },
      )
    }

    // Default: synchronous completed assessment
    return HttpResponse.json(mockCompletedAssessment, { status: 201 })
  }),

  // GET /api/v1/assessments/:assessmentId — Fetch single assessment with polling support
  http.get('*/api/v1/assessments/:assessmentId', ({ params, request }) => {
    const { assessmentId } = params
    const id = String(assessmentId)
    const url = new URL(request.url)

    if (id === '404' || id === 'not-found') {
      return HttpResponse.json(
        {
          error: {
            code: 'ASSESSMENT_NOT_FOUND',
            message: "We couldn't find that assessment.",
          },
        },
        { status: 404 },
      )
    }

    if (id === mockNoAnnotatedImageAssessment.assessment_id) {
      return HttpResponse.json(mockNoAnnotatedImageAssessment)
    }

    if (id === mockFailedAssessment.assessment_id) {
      return HttpResponse.json(mockFailedAssessment)
    }

    // Handle dynamic or fixed processing assessment transitioning to completed
    if (id === mockProcessingAssessment.assessment_id || id.startsWith('mock-asm-dyn-proc-')) {
      const currentCount = pollingCounts.get(id) ?? 0
      pollingCounts.set(id, currentCount + 1)

      // Complete on third poll
      if (currentCount >= 2 || url.searchParams.get('finish') === 'true') {
        const finished: Assessment = {
          ...mockCompletedAssessment,
          assessment_id: id,
          completed_at: new Date().toISOString(),
        }
        return HttpResponse.json(finished)
      }

      return HttpResponse.json({
        ...mockProcessingAssessment,
        assessment_id: id,
      })
    }

    // Default to completed fixture
    return HttpResponse.json({
      ...mockCompletedAssessment,
      assessment_id: id,
    })
  }),

  // GET /api/v1/assessments — List assessment history
  http.get('*/api/v1/assessments', ({ request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') || '1')
    const isEmpty = url.searchParams.get('empty') === 'true'

    if (isEmpty) {
      return HttpResponse.json(mockEmptyHistory)
    }

    if (page === 2) {
      return HttpResponse.json(mockPaginatedHistoryPage2)
    }

    return HttpResponse.json(mockPaginatedHistoryPage1)
  }),
]

/**
 * Resets any in-memory state held by handlers (useful between tests).
 */
export function resetMockState() {
  pollingCounts.clear()
}
