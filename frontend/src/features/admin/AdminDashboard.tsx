import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Sliders,
  RotateCcw,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import {
  fetchAdminOverview,
  fetchAdminModelVersions,
  fetchAdminLimits,
  fetchAdminAssessments,
  reloadVisionModel,
  type AdminOverviewResponse,
  type ModelVersionUsage,
  type AdminLimitsResponse,
  type AdminAssessmentItem,
} from '../../services/adminService'

export function AdminDashboard() {
  const { theme } = useTheme()
  const { authToken } = useAuth()

  // State for overview, models, limits, assessments
  const [windowHours, setWindowHours] = useState<number>(24)
  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null)
  const [modelVersions, setModelVersions] = useState<ModelVersionUsage[]>([])
  const [limits, setLimits] = useState<AdminLimitsResponse | null>(null)
  const [attempts, setAttempts] = useState<AdminAssessmentItem[]>([])
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all')

  const [isLoading, setIsLoading] = useState(true)
  const [isReloadingModel, setIsReloadingModel] = useState(false)
  const [reloadSuccess, setReloadSuccess] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
  }`

  const loadAdminData = useCallback(async () => {
    if (!authToken) return
    setIsLoading(true)
    setErrorMessage(null)

    try {
      const [overviewData, versionsData, limitsData, attemptsData] = await Promise.all([
        fetchAdminOverview(windowHours, authToken).catch(() => null),
        fetchAdminModelVersions(authToken).catch(() => ({ versions: [] })),
        fetchAdminLimits(authToken).catch(() => null),
        fetchAdminAssessments(authToken, {
          status: statusFilter === 'all' ? undefined : statusFilter,
          limit: 25,
        }).catch(() => ({ items: [], next_cursor: null })),
      ])

      if (overviewData) setOverview(overviewData)
      if (versionsData) setModelVersions(versionsData.versions || [])
      if (limitsData) setLimits(limitsData)
      if (attemptsData) setAttempts(attemptsData.items || [])

      if (authToken.startsWith('demo_token_')) {
        if (!overviewData) {
          setOverview({
            since: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
            window_hours: 24,
            outcomes: [
              { status: 'completed', error_code: null, count: 142 },
              { status: 'failed', error_code: 'IMAGE_NOT_COFFEE', count: 4 },
              { status: 'failed', error_code: 'INFERENCE_TIMEOUT', count: 2 },
            ],
          })
        }
        if (!versionsData?.versions?.length) {
          setModelVersions([
            {
              model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
              validator_version: 'CoffeeValidator-v1.0',
              assessments: 348,
              first_seen: '2026-10-01T00:00:00Z',
              last_seen: new Date().toISOString(),
            },
          ])
        }
        if (!limitsData) {
          setLimits({
            max_image_bytes: 15728640,
            max_image_pixels: 25000000,
            min_image_side_px: 512,
            max_assessments_per_user_per_hour: 60,
            max_concurrent_assessments: 10,
            vision_timeout_s: 30,
            gemini_timeout_s: 15,
            image_url_ttl_s: 3600,
            retain_original_image: true,
          })
        }
        if (!attemptsData?.items?.length) {
          setAttempts([
            {
              assessment_id: 'BV-DEMO-2026-001',
              owner_id: 'usr_demo_producer_01',
              status: 'completed',
              created_at: new Date(Date.now() - 3600 * 1000 * 3).toISOString(),
              processing_time_ms: 1240,
              model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
              detection_count: 4,
            },
            {
              assessment_id: 'BV-DEMO-2026-002',
              owner_id: 'usr_demo_producer_01',
              status: 'completed',
              created_at: new Date(Date.now() - 3600 * 1000 * 24).toISOString(),
              processing_time_ms: 1110,
              model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
              detection_count: 6,
            },
            {
              assessment_id: 'BV-DEMO-2026-003',
              owner_id: 'usr_demo_producer_01',
              status: 'completed',
              created_at: new Date(Date.now() - 3600 * 1000 * 48).toISOString(),
              processing_time_ms: 980,
              model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
              detection_count: 1,
            },
          ])
        }
      }
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Failed to load administrator telemetry data from backend.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [authToken, windowHours, statusFilter])

  useEffect(() => {
    loadAdminData()
  }, [loadAdminData])

  const handleReloadModel = async () => {
    if (!authToken) return
    setIsReloadingModel(true)
    setReloadSuccess(null)
    setErrorMessage(null)

    if (authToken.startsWith('demo_token_')) {
      setTimeout(() => {
        setReloadSuccess('Model successfully reloaded (Engine: ONNXRuntime-DirectML-Demo)')
        setIsReloadingModel(false)
        setTimeout(() => setReloadSuccess(null), 5000)
      }, 900)
      return
    }

    try {
      const res = await reloadVisionModel(authToken)
      setReloadSuccess(`Model successfully reloaded (Engine: ${res.engine})`)
      setTimeout(() => setReloadSuccess(null), 5000)
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Vision model reload request failed.',
      )
    } finally {
      setIsReloadingModel(false)
    }
  }

  // Calculate overview totals
  const totalCompleted =
    overview?.outcomes
      .filter((o) => o.status === 'completed')
      .reduce((acc, curr) => acc + curr.count, 0) ?? 0

  const totalFailed =
    overview?.outcomes
      .filter((o) => o.status === 'failed')
      .reduce((acc, curr) => acc + curr.count, 0) ?? 0

  const totalAssessments = totalCompleted + totalFailed

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Admin Telemetry & Limits
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] uppercase tracking-wide">
              Staff Only
            </span>
          </div>
          <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1.5">
            System health, model versions, enforced service limits, and live assessment logs.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={loadAdminData}
            disabled={isLoading}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold border flex items-center gap-2 transition-colors cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#D6D3D1] hover:bg-[#2C2723]'
                : 'bg-white border-[#E2D9CF] text-[#44403C] hover:bg-stone-50'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleReloadModel}
            disabled={isReloadingModel}
            className="px-4 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold flex items-center gap-2 shadow-xs transition-colors cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isReloadingModel ? 'animate-spin' : ''}`} />
            <span>Reload Vision Model</span>
          </button>
        </div>
      </div>

      {/* ── Alerts Banner ── */}
      {reloadSuccess && (
        <div className="p-4 rounded-2xl border border-emerald-300 dark:border-emerald-900/50 bg-emerald-50 dark:bg-emerald-950/20 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-700 dark:text-emerald-400 shrink-0" />
          <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
            {reloadSuccess}
          </p>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-2xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-700 dark:text-red-400 shrink-0" />
          <p className="text-sm font-semibold text-red-900 dark:text-red-200">
            {errorMessage}
          </p>
        </div>
      )}

      {/* ── Overview Metrics Cards ── */}
      <div>
        <div className="flex items-center justify-between pb-3">
          <h2 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Telemetry Outcomes
          </h2>

          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1]">
              Window:
            </span>
            <select
              value={windowHours}
              onChange={(e) => setWindowHours(Number(e.target.value))}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border focus:outline-none cursor-pointer ${
                theme === 'dark'
                  ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                  : 'bg-white border-[#E2D9CF] text-[#1C1917]'
              }`}
            >
              <option value={24}>Last 24 Hours</option>
              <option value={72}>Last 3 Days</option>
              <option value={168}>Last 7 Days</option>
              <option value={720}>Last 30 Days</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {/* Total */}
          <div className={`p-6 ${card}`}>
            <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
              Total Uploads ({windowHours}h)
            </p>
            <p className="text-3xl font-extrabold font-serif text-[#1C1917] dark:text-[#F9F7F2] mt-2">
              {totalAssessments}
            </p>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
              Sample inspection requests received
            </p>
          </div>

          {/* Completed */}
          <div className={`p-6 ${card}`}>
            <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
              Completed Analyses
            </p>
            <p className="text-3xl font-extrabold font-serif text-[#3A5228] dark:text-[#8BA470] mt-2">
              {totalCompleted}
            </p>
            <p className="text-xs font-medium text-[#3A5228] dark:text-[#8BA470] mt-1">
              {totalAssessments > 0
                ? `${((totalCompleted / totalAssessments) * 100).toFixed(1)}% success rate`
                : '100% success rate'}
            </p>
          </div>

          {/* Failed */}
          <div className={`p-6 ${card}`}>
            <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
              Failed Attempts
            </p>
            <p className="text-3xl font-extrabold font-serif text-rose-700 dark:text-rose-400 mt-2">
              {totalFailed}
            </p>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
              Rejected by validator or vision timeout
            </p>
          </div>
        </div>
      </div>

      {/* ── Active Model & Validator Versions ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-4`}>
        <div className="flex items-center justify-between border-b border-[#E2D9CF] dark:border-[#382E26] pb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-[#593D2B] dark:text-[#8BA470]" />
            <h2 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Vision & Validator Model Versions
            </h2>
          </div>
          <span className="text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1]">
            From GET /admin/model-versions
          </span>
        </div>

        {modelVersions.length === 0 ? (
          <p className="text-xs text-[#44403C] dark:text-[#D6D3D1] py-4">
            No completed model executions logged in database yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2D9CF] dark:border-[#382E26] text-[#44403C] dark:text-[#D6D3D1]">
                  <th className="pb-3 font-bold">Vision Model</th>
                  <th className="pb-3 font-bold">Coffee Validator</th>
                  <th className="pb-3 font-bold">Batches Processed</th>
                  <th className="pb-3 font-bold">First Seen</th>
                  <th className="pb-3 font-bold text-right">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2D9CF] dark:divide-[#382E26]">
                {modelVersions.map((v, i) => (
                  <tr key={i} className="hover:bg-stone-500/5">
                    <td className="py-3 font-mono font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      {v.model_version}
                    </td>
                    <td className="py-3 font-mono text-[#44403C] dark:text-[#D6D3D1]">
                      {v.validator_version}
                    </td>
                    <td className="py-3 font-bold text-[#3A5228] dark:text-[#8BA470]">
                      {v.assessments}
                    </td>
                    <td className="py-3 text-[#44403C] dark:text-[#D6D3D1]">
                      {new Date(v.first_seen).toLocaleDateString()}
                    </td>
                    <td className="py-3 text-right text-[#44403C] dark:text-[#D6D3D1]">
                      {new Date(v.last_seen).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Enforced Service Limits ── */}
      {limits && (
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="flex items-center justify-between border-b border-[#E2D9CF] dark:border-[#382E26] pb-3">
            <div className="flex items-center space-x-2">
              <Sliders className="w-5 h-5 text-[#593D2B] dark:text-[#8BA470]" />
              <h2 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
                Enforced Service Limits
              </h2>
            </div>
            <span className="text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1]">
              From GET /admin/limits
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-3.5 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] bg-[#FAF8F5] dark:bg-[#181513]">
              <span className="font-semibold text-[#44403C] dark:text-[#D6D3D1] block">
                Max Image Bytes
              </span>
              <span className="text-base font-bold font-mono text-[#1C1917] dark:text-[#F9F7F2] mt-1 block">
                {(limits.max_image_bytes / (1024 * 1024)).toFixed(1)} MB
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] bg-[#FAF8F5] dark:bg-[#181513]">
              <span className="font-semibold text-[#44403C] dark:text-[#D6D3D1] block">
                Max Image Pixels
              </span>
              <span className="text-base font-bold font-mono text-[#1C1917] dark:text-[#F9F7F2] mt-1 block">
                {(limits.max_image_pixels / 1000000).toFixed(0)} MP
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] bg-[#FAF8F5] dark:bg-[#181513]">
              <span className="font-semibold text-[#44403C] dark:text-[#D6D3D1] block">
                Vision Timeout
              </span>
              <span className="text-base font-bold font-mono text-[#1C1917] dark:text-[#F9F7F2] mt-1 block">
                {limits.vision_timeout_s}s
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] bg-[#FAF8F5] dark:bg-[#181513]">
              <span className="font-semibold text-[#44403C] dark:text-[#D6D3D1] block">
                User Quota / Hour
              </span>
              <span className="text-base font-bold font-mono text-[#1C1917] dark:text-[#F9F7F2] mt-1 block">
                {limits.max_assessments_per_user_per_hour} req/hr
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── Global Assessments Audit Log ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-5`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2D9CF] dark:border-[#382E26] pb-3">
          <div>
            <h2 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Global User Attempts Log
            </h2>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-0.5">
              Live audit trail of all users' sample evaluations from GET /admin/assessments.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-[#44403C] dark:text-[#D6D3D1]">
              Status Filter:
            </span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold border focus:outline-none cursor-pointer ${
                theme === 'dark'
                  ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
                  : 'bg-white border-[#E2D9CF] text-[#1C1917]'
              }`}
            >
              <option value="all">All Attempts</option>
              <option value="completed">Completed Only</option>
              <option value="failed">Failed Only</option>
            </select>
          </div>
        </div>

        {attempts.length === 0 ? (
          <p className="text-xs text-[#44403C] dark:text-[#D6D3D1] py-8 text-center">
            No assessment attempts found matching current filter.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2D9CF] dark:border-[#382E26] text-[#44403C] dark:text-[#D6D3D1]">
                  <th className="pb-3.5 font-bold">Assessment ID</th>
                  <th className="pb-3.5 font-bold">Owner ID</th>
                  <th className="pb-3.5 font-bold">Status</th>
                  <th className="pb-3.5 font-bold">Latency</th>
                  <th className="pb-3.5 font-bold">Error / Detections</th>
                  <th className="pb-3.5 font-bold text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2D9CF] dark:divide-[#382E26]">
                {attempts.map((item) => (
                  <tr key={item.assessment_id} className="hover:bg-stone-500/5">
                    <td className="py-3.5 font-mono font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      <Link
                        to={`/assessments/${item.assessment_id}`}
                        className="hover:underline text-[#593D2B] dark:text-[#C4A882]"
                      >
                        {item.assessment_id}
                      </Link>
                    </td>

                    <td className="py-3.5 font-mono text-[#44403C] dark:text-[#D6D3D1] truncate max-w-28">
                      {item.owner_id}
                    </td>

                    <td className="py-3.5">
                      {item.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] border border-[#8BA470]/30">
                          COMPLETED
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30">
                          FAILED
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 font-mono text-[#44403C] dark:text-[#D6D3D1]">
                      {item.processing_time_ms ? `${item.processing_time_ms}ms` : '—'}
                    </td>

                    <td className="py-3.5 font-medium">
                      {item.error_code ? (
                        <span className="font-mono text-rose-700 dark:text-rose-400 font-bold">
                          {item.error_code}
                        </span>
                      ) : item.detection_count !== undefined ? (
                        <span className="text-[#3A5228] dark:text-[#8BA470] font-bold">
                          {item.detection_count} regions detected
                        </span>
                      ) : (
                        <span className="text-[#44403C] dark:text-[#D6D3D1]">None</span>
                      )}
                    </td>

                    <td className="py-3.5 text-right text-[#44403C] dark:text-[#D6D3D1]">
                      {new Date(item.created_at).toLocaleString()}
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
