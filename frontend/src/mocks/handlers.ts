import { http, HttpResponse } from 'msw'
import { mockCompletedAssessment, mockEmptyHistory, mockFailedAssessment, mockPaginatedHistoryPage1, mockPaginatedHistoryPage2 } from './fixtures'

export const handlers = [
  http.get('*/api/v1/assessments/:assessmentId', ({ params }) => {
    const id = String(params.assessmentId)
    if (id === '404' || id === 'not-found') return HttpResponse.json({ error: { code: 'ASSESSMENT_NOT_FOUND', message: "We couldn't find that assessment." } }, { status: 404 })
    if (id === mockFailedAssessment.assessment_id) return HttpResponse.json(mockFailedAssessment)
    return HttpResponse.json({ ...mockCompletedAssessment, assessment_id: id })
  }),
  http.get('*/api/v1/assessments', ({ request }) => {
    const url = new URL(request.url)
    if (url.searchParams.get('empty') === 'true') return HttpResponse.json(mockEmptyHistory)
    return HttpResponse.json(url.searchParams.get('cursor') === 'mock-page-2' ? mockPaginatedHistoryPage2 : mockPaginatedHistoryPage1)
  }),
]

export function resetMockState() {}
