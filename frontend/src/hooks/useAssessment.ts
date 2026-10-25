import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { env } from '../config/env'
import { assessmentApi } from '../services/assessmentApi'

const MAX_WAIT_MS = 60_000

export function useAssessment(assessmentId: string | undefined) {
  const [waitedTooLong, setWaitedTooLong] = useState(false)
  const query = useQuery({
    queryKey: ['assessment', assessmentId], queryFn: () => assessmentApi.getAssessment(assessmentId!), enabled: Boolean(assessmentId),
    // The current contract is terminal; this activates if an in-progress status is later added.
    refetchInterval: (state) => ((state.state.data as { status?: string } | undefined)?.status === 'processing' ? env.pollIntervalMs : false),
  })
  const isProcessing = (query.data as { status?: string } | undefined)?.status === 'processing'
  useEffect(() => {
    setWaitedTooLong(false)
    if (!isProcessing) return
    const timer = window.setTimeout(() => setWaitedTooLong(true), MAX_WAIT_MS)
    return () => window.clearTimeout(timer)
  }, [assessmentId, isProcessing])
  return { ...query, isProcessing, waitedTooLong }
}
