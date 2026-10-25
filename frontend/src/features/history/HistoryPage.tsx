import { useState, useEffect } from 'react'
import { Link } from 'react-router'
import {
  Upload,
  Search,
  RefreshCw,
  Clock,
  ChevronRight,
  AlertTriangle,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { getSessionAssessments } from '../upload/AssessPage'
import { useAssessments } from '../../hooks/useAssessments'
import {
  getDemoAssessments,
  deleteDemoData,
  loadDemoData,
  hasDemoData,
} from '../../services/demoService'

interface HistoryRow {
  assessment_id: string
  model_version?: string
  created_at: string
  detection_count?: number
  status: 'completed' | 'failed' | 'processing'
  error_code?: string
  isDemo?: boolean
}

export function HistoryPage() {
  const { theme } = useTheme()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all')
  const [, setDemoStateToken] = useState(0)

  const [cursors, setCursors] = useState<(string | null)[]>([null])
  const [page, setPage] = useState(0)

  const { data: remoteData, isLoading: remoteLoading, error: remoteError, isFetching, refetch } =
    useAssessments(cursors[page])

  useEffect(() => {
    const handleDemoUpdate = () => setDemoStateToken((c) => c + 1)
    window.addEventListener('bv_demo_data_changed', handleDemoUpdate)
    return () => window.removeEventListener('bv_demo_data_changed', handleDemoUpdate)
  }, [])

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
  }`

  const next = () => {
    if (!remoteData?.next_cursor) return
    setCursors((current) => [...current.slice(0, page + 1), remoteData.next_cursor])
    setPage((current) => current + 1)
  }

  // Merge real session assessments with real remote assessments from the backend
  const sessionItems: HistoryRow[] = getSessionAssessments().map((a) => ({
    assessment_id: a.assessment_id,
    model_version: a.model_version,
    created_at: a.created_at,
    detection_count: a.summary.detection_count,
    status: a.status as 'completed' | 'failed' | 'processing',
    error_code: a.error_code ?? undefined,
  }))

  const demoItems: HistoryRow[] = getDemoAssessments().map((a) => ({
    assessment_id: a.assessment_id,
    model_version: a.model_version,
    created_at: a.created_at,
    detection_count: a.summary.detection_count,
    status: a.status as 'completed' | 'failed' | 'processing',
    isDemo: true,
  }))

  const remoteItems: HistoryRow[] =
    remoteData?.items?.map((item) => ({
      assessment_id: item.assessment_id,
      model_version: item.model_version || 'YOLOv8',
      created_at: item.created_at,
      detection_count: item.detection_count,
      status: item.status as 'completed' | 'failed' | 'processing',
      error_code: item.error_code ?? undefined,
    })) ?? []

  // Combine unique by assessment_id: remote items take priority, followed by session, followed by demo
  const combinedMap = new Map<string, HistoryRow>()
  demoItems.forEach((item) => combinedMap.set(item.assessment_id, item))
  sessionItems.forEach((item) => combinedMap.set(item.assessment_id, item))
  remoteItems.forEach((item) => combinedMap.set(item.assessment_id, item))

  const allItems = Array.from(combinedMap.values())
  const demoIsActive = hasDemoData() && demoItems.length > 0

  // Apply search & status filters
  const filteredItems = allItems.filter((item) => {
    const matchesSearch =
      item.assessment_id.toLowerCase().includes(search.toLowerCase()) ||
      (item.model_version && item.model_version.toLowerCase().includes(search.toLowerCase()))

    const matchesStatus =
      statusFilter === 'all' || item.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Assessment History
          </h1>
          <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1.5">
            Audit log of all your evaluated green coffee sample batches (newest first).
          </p>
        </div>

        <Link
          to="/assess"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold shadow-xs transition-all no-underline shrink-0"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Assess New Sample</span>
        </Link>
      </div>

      {/* ── Search & Filter Bar ── */}
      <div
        className={`p-4 ${card} flex flex-col sm:flex-row items-center justify-between gap-4`}
      >
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#44403C] dark:text-[#D6D3D1]" />
          <input
            type="text"
            placeholder="Search assessment ID or model…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`w-full pl-9 pr-4 py-2 rounded-xl text-xs font-medium border focus:outline-none focus:ring-2 focus:ring-[#8BA470] transition-colors ${
              theme === 'dark'
                ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                : 'bg-[#FAF8F5] border-[#E2D9CF] text-[#1C1917]'
            }`}
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
          <span className="text-xs font-bold text-[#44403C] dark:text-[#D6D3D1]">
            Status:
          </span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className={`px-3 py-2 rounded-xl text-xs font-bold border focus:outline-none cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                : 'bg-[#FAF8F5] border-[#E2D9CF] text-[#1C1917]'
            }`}
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed Only</option>
            <option value="failed">Failed Only</option>
          </select>

          {remoteLoading && (
            <span className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] flex items-center space-x-1">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Syncing…</span>
            </span>
          )}
        </div>
      </div>

      {/* ── Remote Error Banner ── */}
      {remoteError && (
        <div className="p-4 rounded-2xl border border-amber-300 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-700 dark:text-amber-400 shrink-0" />
            <p className="text-xs font-medium text-amber-950 dark:text-amber-200">
              Backend sync: {remoteError.message}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void refetch()}
            className="text-xs font-bold text-amber-900 dark:text-amber-300 hover:underline cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Demo Active Notification Banner ── */}
      {demoIsActive && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-950 dark:text-amber-200">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-amber-700 dark:text-amber-400 shrink-0" />
            <p className="text-xs font-semibold">
              Demo sample assessments are active for UI/UX preview. You can delete them cleanly anytime.
            </p>
          </div>
          <button
            type="button"
            onClick={() => deleteDemoData()}
            className="px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Demo Data</span>
          </button>
        </div>
      )}

      {/* ── Table Card ── */}
      <div className={`p-6 sm:p-7 ${card} overflow-hidden`}>
        {remoteLoading && allItems.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470] mx-auto" />
            <p className="text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1]">
              Loading assessment records from backend…
            </p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <Clock className="w-10 h-10 text-stone-400 mx-auto" />
            <h3 className="text-base font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              No assessments found
            </h3>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
              {search || statusFilter !== 'all'
                ? 'Try adjusting your search criteria.'
                : 'Upload a green coffee sample to create your first preliminary assessment.'}
            </p>
            <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/assess"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold no-underline"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Start First Assessment</span>
              </Link>
              <button
                type="button"
                onClick={() => loadDemoData()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-[#8BA470]/50 bg-[#8BA470]/15 hover:bg-[#8BA470]/25 text-[#3A5228] dark:text-[#B5CF97] text-xs font-bold transition-colors cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Load Demo Data (Preview)</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2D9CF] dark:border-[#382E26] text-[#44403C] dark:text-[#D6D3D1]">
                  <th className="pb-3.5 font-bold">Assessment ID</th>
                  <th className="pb-3.5 font-bold">Created Date</th>
                  <th className="pb-3.5 font-bold">Vision Model</th>
                  <th className="pb-3.5 font-bold">Defect Tally</th>
                  <th className="pb-3.5 font-bold">Status</th>
                  <th className="pb-3.5 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2D9CF] dark:divide-[#382E26]">
                {filteredItems.map((item) => (
                  <tr
                    key={item.assessment_id}
                    className="hover:bg-stone-500/5 transition-colors"
                  >
                    <td className="py-4 font-mono font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      <div className="flex items-center gap-1.5">
                        <Link
                          to={`/assessments/${item.assessment_id}`}
                          className="hover:text-[#593D2B] dark:hover:text-[#C4A882] transition-colors"
                        >
                          {item.assessment_id}
                        </Link>
                        {item.isDemo && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/20 text-amber-800 dark:text-amber-300">
                            Demo
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-4 text-[#44403C] dark:text-[#D6D3D1]">
                      {new Date(item.created_at).toLocaleString()}
                    </td>

                    <td className="py-4 font-mono text-[#44403C] dark:text-[#D6D3D1]">
                      {item.model_version || 'YOLOv8'}
                    </td>

                    <td className="py-4 font-mono font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      {item.status === 'completed'
                        ? `${item.detection_count ?? 0} defect regions`
                        : item.error_code || 'Processing Failed'}
                    </td>

                    <td className="py-4">
                      {item.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-[#8BA470]/20 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/30">
                          COMPLETED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-rose-500/15 text-rose-800 dark:text-rose-400 border border-rose-500/30">
                          FAILED
                        </span>
                      )}
                    </td>

                    <td className="py-4 text-right">
                      <Link
                        to={`/assessments/${item.assessment_id}`}
                        className="inline-flex items-center gap-1 font-bold text-[#593D2B] dark:text-[#C4A882] hover:underline"
                      >
                        <span>Open Report</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination nav */}
        {remoteData?.next_cursor && (
          <div className="mt-5 pt-3 border-t border-[#E2D9CF] dark:border-[#382E26] flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={() => setPage((current) => current - 1)}
              disabled={page === 0 || isFetching}
              className="px-3.5 py-2 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] font-bold text-[#44403C] dark:text-[#D6D3D1] disabled:opacity-40 cursor-pointer"
            >
              Previous Page
            </button>
            <span className="font-semibold text-[#44403C] dark:text-[#D6D3D1]">
              Page {page + 1} {isFetching ? '· Syncing…' : ''}
            </span>
            <button
              type="button"
              onClick={next}
              disabled={!remoteData?.next_cursor || isFetching}
              className="px-3.5 py-2 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] font-bold text-[#44403C] dark:text-[#D6D3D1] disabled:opacity-40 cursor-pointer"
            >
              Next Page
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
