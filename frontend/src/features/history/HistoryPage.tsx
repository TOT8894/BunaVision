import { useState } from 'react'
import { Link } from 'react-router'
import { ErrorState, StatusPill } from '../../components/common'
import { isApiError } from '../../api/apiClient'
import { useAssessments } from '../../hooks/useAssessments'

const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

export function HistoryPage() {
  const [cursors, setCursors] = useState<(string | null)[]>([null])
  const [page, setPage] = useState(0)
  const { data, error, isLoading, isFetching, refetch } = useAssessments(cursors[page])
  const next = () => { if (!data?.next_cursor) return; setCursors((current) => [...current.slice(0, page + 1), data.next_cursor]); setPage((current) => current + 1) }
  if (isLoading) return <main className="mx-auto max-w-6xl px-4 py-8"><p role="status" className="text-slate-600">Loading assessment history…</p></main>
  if (error) return <main className="mx-auto max-w-2xl px-4 py-8"><ErrorState errorCode={isApiError(error) ? error.code : undefined} message={error.message} onRetry={() => void refetch()} /></main>
  const items = data?.items ?? []
  return <main className="mx-auto max-w-6xl px-4 py-8"><div className="flex items-start justify-between gap-4"><div><h1 className="text-3xl font-bold">Assessment history</h1><p className="mt-1 text-slate-600">Your most recent preliminary AI assessments.</p></div><Link to="/assess" className="rounded-lg bg-coffee-700 px-4 py-2 text-sm font-medium text-white no-underline hover:bg-coffee-800">New assessment</Link></div>
    {items.length === 0 ? <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center"><h2 className="text-lg font-semibold">No assessments yet</h2><p className="mt-2 text-sm text-slate-600">Upload a coffee sample image to create your first preliminary assessment.</p></div> : <div className="mt-6 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="p-4">Assessment</th><th className="p-4">Created</th><th className="p-4">Status</th><th className="p-4">Result</th></tr></thead><tbody>{items.map((item) => <tr key={item.assessment_id} className="border-t border-slate-100"><td className="p-4"><Link className="font-medium text-coffee-700 hover:underline" to={`/assessments/${encodeURIComponent(item.assessment_id)}`}>{item.assessment_id}</Link></td><td className="p-4">{formatDate(item.created_at)}</td><td className="p-4"><StatusPill status={item.status} size="sm" /></td><td className="p-4">{item.status === 'completed' ? `${item.detection_count} detected region${item.detection_count === 1 ? '' : 's'}` : 'Processing failed'}</td></tr>)}</tbody></table></div>}
    <nav className="mt-5 flex items-center justify-between" aria-label="History pagination"><button type="button" onClick={() => setPage((current) => current - 1)} disabled={page === 0 || isFetching} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50">Previous</button><span className="text-sm text-slate-600">Page {page + 1}{isFetching ? ' · Loading…' : ''}</span><button type="button" onClick={next} disabled={!data?.next_cursor || isFetching} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50">Next</button></nav>
  </main>
}
