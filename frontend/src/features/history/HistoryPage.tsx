import { useState } from 'react'
import { Link } from 'react-router'
import {
  Upload,
  Search,
  RefreshCw,
  Clock,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { getSessionAssessments } from '../upload/AssessPage'
import { useAssessments } from '../../hooks/useAssessments'

interface HistoryRow {
  assessment_id: string
  station_name: string
  created_at: string
  defect_percentage: string
  status: 'completed' | 'failed' | 'processing'
}

export function HistoryPage() {
  const { theme } = useTheme()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all')

  const { data: remoteData, isLoading: remoteLoading, error: remoteError, refetch } =
    useAssessments(null)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-md shadow-black/20'
      : 'bg-white border-[#E8E0D5] shadow-xs'
  }`

  // Merge real session assessments with real remote assessments from the backend
  const sessionItems: HistoryRow[] = getSessionAssessments().map((a) => ({
    assessment_id: a.assessment_id,
    station_name: a.station_id || 'Washing Station (Direct Upload)',
    created_at: a.created_at,
    defect_percentage:
      a.status === 'completed' ? `${a.summary.defect_percentage}%` : '—',
    status: a.status as 'completed' | 'failed' | 'processing',
  }))

  const remoteItems: HistoryRow[] =
    remoteData?.items?.map((item) => ({
      assessment_id: item.assessment_id,
      station_name: 'Washing Station (Live API)',
      created_at: item.created_at,
      defect_percentage:
        item.status === 'completed'
          ? item.detection_count !== undefined
            ? `${item.detection_count} defects`
            : '0 defects'
          : '—',
      status: item.status as 'completed' | 'failed' | 'processing',
    })) ?? []

  // Combine unique by assessment_id
  const combinedMap = new Map<string, HistoryRow>()
  sessionItems.forEach((item) => combinedMap.set(item.assessment_id, item))
  remoteItems.forEach((item) => combinedMap.set(item.assessment_id, item))

  const allItems = Array.from(combinedMap.values())

  // Apply search & status filters
  const filteredItems = allItems.filter((item) => {
    const matchesSearch =
      item.assessment_id.toLowerCase().includes(search.toLowerCase()) ||
      item.station_name.toLowerCase().includes(search.toLowerCase())

    const matchesStatus =
      statusFilter === 'all' || item.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
            Assessment History
          </h1>
          <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB] mt-1.5">
            Audit log of all evaluated green coffee sample batches.
          </p>
        </div>

        <Link
          to="/assess"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-all no-underline shrink-0"
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
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-[#7B7569] dark:text-[#A8A193]" />
          <input
            type="text"
            placeholder="Search assessment ID or station..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`w-full pl-9 pr-4 py-2 rounded-xl text-xs border focus:outline-none focus:ring-2 focus:ring-[#8BA470] transition-colors ${
              theme === 'dark'
                ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#24211D]'
            }`}
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
          <span className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
            Status:
          </span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className={`px-3 py-2 rounded-xl text-xs border focus:outline-none cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#24211D]'
            }`}
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          {remoteLoading && (
            <span className="text-xs text-[#7B7569] flex items-center space-x-1">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Syncing…</span>
            </span>
          )}
        </div>
      </div>

      {/* ── Remote Error Banner if any ── */}
      {remoteError && (
        <div className="p-4 rounded-2xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <p className="text-xs text-amber-900 dark:text-amber-200">
              Backend sync: {remoteError.message}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void refetch()}
            className="text-xs font-semibold text-amber-800 dark:text-amber-300 hover:underline cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Table Card ── */}
      <div className={`p-6 sm:p-7 ${card} overflow-hidden`}>
        {remoteLoading && allItems.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470] mx-auto" />
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB]">
              Loading assessment records from backend…
            </p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <Clock className="w-10 h-10 text-stone-400 mx-auto" />
            <h3 className="text-base font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              No assessments found
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB]">
              {search || statusFilter !== 'all'
                ? 'Try adjusting your search criteria.'
                : 'Submit your first green coffee sample to see results here.'}
            </p>
            <div className="pt-2">
              <Link
                to="/assess"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#593D2B] text-white text-xs font-semibold no-underline"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Start New Assessment</span>
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E8E0D5] dark:border-[#382E26] text-[#7B7569] dark:text-[#A8A193]">
                  <th className="pb-3.5 font-semibold">Assessment ID</th>
                  <th className="pb-3.5 font-semibold">Washing Station</th>
                  <th className="pb-3.5 font-semibold">Created Date</th>
                  <th className="pb-3.5 font-semibold">Defect Ratio</th>
                  <th className="pb-3.5 font-semibold">Status</th>
                  <th className="pb-3.5 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0D5] dark:divide-[#382E26]">
                {filteredItems.map((item) => (
                  <tr
                    key={item.assessment_id}
                    className="hover:bg-stone-500/5 transition-colors"
                  >
                    <td className="py-4 font-bold text-[#24211D] dark:text-[#F9F7F2]">
                      <Link
                        to={`/assessments/${item.assessment_id}`}
                        className="hover:text-[#593D2B] dark:hover:text-[#C4A882] transition-colors"
                      >
                        {item.assessment_id}
                      </Link>
                    </td>

                    <td className="py-4 text-[#5A544C] dark:text-[#C8C2BB]">
                      {item.station_name}
                    </td>

                    <td className="py-4 text-[#7B7569] dark:text-[#A8A193]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-4 font-bold text-[#24211D] dark:text-[#F9F7F2]">
                      {item.defect_percentage}
                    </td>

                    <td className="py-4">
                      {item.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8BA470]/15 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/30">
                          COMPLETED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30">
                          FAILED
                        </span>
                      )}
                    </td>

                    <td className="py-4 text-right">
                      <Link
                        to={`/assessments/${item.assessment_id}`}
                        className="inline-flex items-center gap-1 font-semibold text-[#593D2B] dark:text-[#C4A882] hover:underline"
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
      </div>
    </div>
  )
}
