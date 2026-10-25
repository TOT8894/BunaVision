import { Link, useParams } from 'react-router'
import { Disclaimer, ErrorState, ProcessingState, StatusPill } from '../../components/common'
import { isApiError } from '../../api/apiClient'
import { useAssessment } from '../../hooks/useAssessment'
import { DefectTable } from './DefectTable'
import { ImageCompare } from './ImageCompare'
import { LimitationsPanel } from './LimitationsPanel'
import { SummaryCards } from './SummaryCards'

const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

export function AssessmentPage() {
  const { assessmentId } = useParams()
  const { data, error, isLoading, isProcessing, waitedTooLong, refetch } = useAssessment(assessmentId)
  if (!assessmentId) return <ErrorState title="Missing assessment ID" message="Choose an assessment from history." />
  if (isLoading || isProcessing) return <ProcessingState subtext={waitedTooLong ? 'This is taking longer than expected. You can return to history and check again later.' : undefined} />
  if (error) return <ErrorState errorCode={isApiError(error) ? error.code : undefined} message={error.message} onRetry={() => void refetch()} onBack={() => history.back()} />
  if (!data) return null
  if (data.status === 'failed') return <ErrorState title="Assessment failed" errorCode={data.error_code} message="The image was not assessed. Try another photo." onBack={() => history.back()} />
  const { result } = data
  return <main className="mx-auto max-w-6xl space-y-6 px-4 py-8"><div className="flex flex-wrap items-start justify-between gap-3"><div><Link to="/assessments" className="text-sm text-coffee-700 hover:underline">← Assessment history</Link><h1 className="mt-2 text-3xl font-bold">Assessment report</h1><p className="mt-1 text-sm text-slate-600">ID: {data.assessment_id}</p></div><StatusPill status={data.status} /></div>
    <Disclaimer variant="compact" /><SummaryCards summary={result.summary} /><ImageCompare images={result.images} onRefresh={() => void refetch()} /><DefectTable rows={result.summary.by_class} /><LimitationsPanel assessment={data} />
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold">Details</h2><dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-slate-500">Model version</dt><dd className="font-medium">{result.model_version}</dd></div><div><dt className="text-slate-500">Created</dt><dd className="font-medium">{formatDate(data.created_at)}</dd></div><div><dt className="text-slate-500">Processing time</dt><dd className="font-medium">{(data.processing_time_ms / 1000).toFixed(2)} seconds</dd></div><div><dt className="text-slate-500">Image URL expiry</dt><dd className="font-medium">{result.images.expires_in_s} seconds</dd></div></dl>{result.advisory.summary.en && <p className="mt-4 rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{result.advisory.summary.en}</p>}</section>
  </main>
}
