import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { assessmentApi } from '../services/assessmentApi'

export function useAssessments(cursor: string | null, limit = 20) {
  return useQuery({ queryKey: ['assessments', cursor, limit], queryFn: () => assessmentApi.listAssessments({ cursor, limit }), placeholderData: keepPreviousData })
}
