import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router'
import {
  ArrowLeft,
  Upload,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Info,
  Check,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { getSessionAssessments } from '../upload/AssessPage'
import {
  fetchAssessmentByIdFromBackend,
  mapBackendToUnified,
} from '../../services/assessmentService'
import type { UnifiedAssessment, BackendCompletedAssessment } from '../../types/assessment'

export function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const { theme } = useTheme()
  const { authToken } = useAuth()

  const [assessment, setAssessment] = useState<UnifiedAssessment | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'annotated' | 'original'>('annotated')
  const [languageMode, setLanguageMode] = useState<'en' | 'am'>('en')
  const [qGraderConfirmed, setQGraderConfirmed] = useState(false)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-md shadow-black/20'
      : 'bg-white border-[#E8E0D5] shadow-xs'
  }`

  useEffect(() => {
    let isMounted = true

    async function loadData() {
      if (!id) {
        setIsLoading(false)
        setErrorMessage('No assessment ID specified.')
        return
      }

      setIsLoading(true)
      setErrorMessage(null)

      // 1. Check in-memory session assessments from current session
      const sessionList = getSessionAssessments()
      const foundInSession = sessionList.find(
        (a) => a.assessment_id === id,
      )
      if (foundInSession) {
        if (isMounted) {
          setAssessment(foundInSession)
          setIsLoading(false)
        }
        return
      }

      // 2. Fetch directly from the real backend API
      try {
        const remote = await fetchAssessmentByIdFromBackend(id, authToken ?? undefined)
        if (!isMounted) return

        if (remote.status === 'completed') {
          const unified = mapBackendToUnified(remote as BackendCompletedAssessment)
          setAssessment(unified)
        } else {
          setErrorMessage(
            `Assessment processing status: ${remote.status}. Defect evaluation could not be completed.`,
          )
        }
      } catch (err: unknown) {
        if (!isMounted) return
        const msg =
          err instanceof Error
            ? err.message
            : 'Failed to retrieve assessment data from backend service.'
        setErrorMessage(msg)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadData()
    return () => {
      isMounted = false
    }
  }, [id, authToken])

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470]" />
        <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB]">
          Loading assessment report from backend…
        </p>
      </div>
    )
  }

  if (errorMessage || !assessment) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center space-y-5">
        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
            Assessment Not Available
          </h2>
          <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB] max-w-md mx-auto">
            {errorMessage || 'The requested assessment could not be loaded from the backend.'}
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/assessments"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold no-underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Assessment History</span>
          </Link>
        </div>
      </div>
    )
  }

  const { summary } = assessment
  const normalPercent = summary.total_beans_estimated
    ? ((summary.normal_beans_count / summary.total_beans_estimated) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* ── Top Toolbar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <Link
            to="/assessments"
            className={`p-2.5 rounded-xl border transition-colors cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#C8C2BB] hover:bg-[#2C2723]'
                : 'bg-white border-[#DDD5C8] text-[#5A544C] hover:bg-[#FAF8F5]'
            }`}
            title="Back to History"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-2xl sm:text-3xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                {assessment.assessment_id}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wide bg-[#8BA470]/15 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/30">
                {assessment.status.toUpperCase()}
              </span>
            </div>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
              Assessed on {new Date(assessment.created_at).toLocaleString()} • Model:{' '}
              {assessment.model_version}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {!qGraderConfirmed ? (
            <button
              type="button"
              onClick={() => setQGraderConfirmed(true)}
              className="bg-[#8BA470] hover:bg-[#78935c] text-white px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-xs transition-all cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Confirm Q-Grader Review</span>
            </button>
          ) : (
            <div className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#8BA470]/20 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/40 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#4F7335] dark:text-[#8BA470]" />
              <span>Verified by Q-Grader</span>
            </div>
          )}

          <Link
            to="/assess"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-all no-underline"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Assess Another Sample</span>
          </Link>
        </div>
      </div>

      {/* ── 4 Top Summary Stat Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Beans */}
        <div className={`p-5 ${card}`}>
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Total Beans Est.
          </p>
          <p className="text-3xl font-extrabold font-serif text-[#24211D] dark:text-[#F9F7F2] mt-2">
            {summary.total_beans_estimated}
          </p>
          <p className="text-[11px] text-[#7B7569] dark:text-[#A8A193] mt-1">
            Boundaries Segmented
          </p>
        </div>

        {/* Normal Green Beans */}
        <div className={`p-5 ${card}`}>
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Normal Green Beans
          </p>
          <p className="text-3xl font-extrabold font-serif text-[#4F7335] dark:text-[#8BA470] mt-2">
            {summary.normal_beans_count}
          </p>
          <p className="text-[11px] text-[#4F7335] dark:text-[#8BA470] mt-1">
            {normalPercent}% Healthy Ratio
          </p>
        </div>

        {/* Defect Anomalies */}
        <div className={`p-5 ${card}`}>
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Defect Anomalies
          </p>
          <p className="text-3xl font-extrabold font-serif text-amber-600 dark:text-amber-400 mt-2">
            {summary.defect_regions_count}
          </p>
          <p className="text-[11px] text-[#7B7569] dark:text-[#A8A193] mt-1">
            Surface Regions Identified
          </p>
        </div>

        {/* Defect Ratio */}
        <div className={`p-5 ${card}`}>
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Defect Ratio
          </p>
          <p className="text-3xl font-extrabold font-serif text-rose-600 dark:text-rose-400 mt-2">
            {summary.defect_percentage}%
          </p>
          <p className="text-[11px] text-[#7B7569] dark:text-[#A8A193] mt-1">
            Pre-Roast Sample Quality Metric
          </p>
        </div>
      </div>

      {/* ── Optical Bounding Box Inspection ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-5`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Optical Bounding Box Inspection
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-0.5">
              Compare raw sample image with computer vision segmentation output.
            </p>
          </div>

          <div className="inline-flex p-1 rounded-xl border bg-[#FAF8F5] dark:bg-[#181513] border-[#E8E0D5] dark:border-[#382E26]">
            {(['annotated', 'original'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  viewMode === mode
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#7B7569] dark:text-[#A8A193] hover:text-[#24211D] dark:hover:text-[#F9F7F2]'
                }`}
              >
                {mode === 'annotated' ? 'Annotated AI View' : 'Original Sample Image'}
              </button>
            ))}
          </div>
        </div>

        {/* Image Display */}
        <div className="relative rounded-2xl overflow-hidden aspect-video max-h-[520px] bg-stone-900 border border-[#E8E0D5] dark:border-[#382E26] flex items-center justify-center">
          <img
            src={
              viewMode === 'annotated'
                ? assessment.annotated_image_url || assessment.original_image_url
                : assessment.original_image_url
            }
            alt="Sample Visual Inspection"
            className="w-full h-full object-cover"
          />
        </div>
      </div>

      {/* ── Granular Classification Breakdown ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-5`}>
        <div>
          <h3 className="text-lg font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
            Granular Classification Breakdown
          </h3>
          <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-0.5">
            Measured defect region tallies grouped by ECX defect category.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E8E0D5] dark:border-[#382E26] text-[#7B7569] dark:text-[#A8A193]">
                <th className="pb-3.5 font-semibold">Class Name</th>
                <th className="pb-3.5 font-semibold">Category Type</th>
                <th className="pb-3.5 font-semibold">Region Count</th>
                <th className="pb-3.5 font-semibold">Model Confidence</th>
                <th className="pb-3.5 font-semibold text-right">Verification Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E0D5] dark:divide-[#382E26]">
              {assessment.predictions.map((pred, idx) => {
                const confPercent = (pred.confidence * 100).toFixed(1)
                const isHighConf = pred.confidence >= 0.8
                return (
                  <tr
                    key={idx}
                    className="hover:bg-stone-500/5 transition-colors"
                  >
                    <td className="py-3.5 font-semibold text-[#24211D] dark:text-[#F9F7F2]">
                      {pred.class_name}
                    </td>

                    <td className="py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          pred.category_type === 'Healthy'
                            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
                            : pred.category_type === 'Primary Defect'
                              ? 'bg-red-500/10 text-red-700 dark:text-red-300 border border-red-500/20'
                              : 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20'
                        }`}
                      >
                        {pred.category_type}
                      </span>
                    </td>

                    <td className="py-3.5 font-bold text-[#24211D] dark:text-[#F9F7F2]">
                      {pred.count}
                    </td>

                    <td className="py-3.5">
                      <div className="flex items-center space-x-2.5">
                        <span className="font-mono w-11 text-[#5A544C] dark:text-[#C8C2BB]">
                          {confPercent}%
                        </span>
                        <div className="w-24 bg-stone-200 dark:bg-stone-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${
                              isHighConf ? 'bg-[#8BA470]' : 'bg-amber-500'
                            }`}
                            style={{ width: `${confPercent}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 text-right">
                      {isHighConf ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-[#8BA470]/15 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/30">
                          <CheckCircle2 className="w-3 h-3" />
                          High Confidence
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30">
                          <AlertTriangle className="w-3 h-3" />
                          Review Manually (&lt;80%)
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Gemini Agronomy Advisory ── */}
      {assessment.advisory?.summary && (
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#593D2B]/10 dark:bg-[#593D2B]/30 flex items-center justify-center text-[#593D2B] dark:text-[#C4A882]">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-base font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                Gemini AI Agronomy Advisory
              </h3>
            </div>

            <div className="flex items-center space-x-1.5 bg-[#FAF8F5] dark:bg-[#181513] p-1 rounded-xl border border-[#E8E0D5] dark:border-[#382E26]">
              <button
                type="button"
                onClick={() => setLanguageMode('en')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-all cursor-pointer ${
                  languageMode === 'en'
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#7B7569] dark:text-[#A8A193]'
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLanguageMode('am')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-all cursor-pointer ${
                  languageMode === 'am'
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#7B7569] dark:text-[#A8A193]'
                }`}
              >
                አማርኛ (Amharic)
              </button>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-[#4A4540] dark:text-[#C8C2BB] bg-[#FAF8F5] dark:bg-[#181513] p-4 rounded-xl border border-[#E8E0D5] dark:border-[#382E26]">
            {languageMode === 'en'
              ? assessment.advisory.summary.en
              : assessment.advisory.summary.am}
          </p>
        </div>
      )}

      {/* ── Mandatory AI Limitation Notice ── */}
      <div className="p-5 rounded-2xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="text-xs leading-relaxed text-amber-900 dark:text-amber-300">
          <strong>Decision-Support Notice:</strong> BunaVision provides automated optical defect region
          segmentation for pre-roast green coffee bean samples. It is not an official ECX / SCA grade certificate
          and must not be presented as one. Final batch classification requires sensory cup evaluation and
          certified Q-grader verification.
        </p>
      </div>
    </div>
  )
}
