import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router'
import {
  ArrowLeft,
  Upload,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Info,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { getSessionAssessments } from '../upload/AssessPage'
import {
  fetchAssessmentByIdFromBackend,
  mapBackendToUnified,
} from '../../services/assessmentService'
import {
  getDemoAssessmentById,
  deleteDemoData,
} from '../../services/demoService'
import type { UnifiedAssessment, BackendCompletedAssessment } from '../../types/assessment'

export function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const { theme } = useTheme()
  const { authToken } = useAuth()
  const navigate = useNavigate()

  const [assessment, setAssessment] = useState<UnifiedAssessment | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'annotated' | 'original'>('annotated')
  const [languageMode, setLanguageMode] = useState<'en' | 'am'>('en')

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
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
      const foundInSession = sessionList.find((a) => a.assessment_id === id)
      if (foundInSession) {
        if (isMounted) {
          setAssessment(foundInSession)
          setIsLoading(false)
        }
        return
      }

      // 2. Check stored demo assessments
      const demoItem = getDemoAssessmentById(id)
      if (demoItem) {
        if (isMounted) {
          setAssessment(demoItem)
          setIsLoading(false)
        }
        return
      }

      // 3. Fetch directly from the real backend API
      try {
        const remote = await fetchAssessmentByIdFromBackend(id, authToken ?? undefined)
        if (!isMounted) return

        if (remote.status === 'completed') {
          const unified = mapBackendToUnified(remote as BackendCompletedAssessment)
          setAssessment(unified)
        } else {
          setErrorMessage(
            `Assessment failed during processing with error code: ${remote.error_code || 'PROCESSING_FAILED'}.`,
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

  const handleDeleteDemo = () => {
    deleteDemoData()
    navigate('/assessments')
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-8 h-8 animate-spin text-[#8BA470]" />
        <p className="text-sm font-semibold text-[#44403C] dark:text-[#D6D3D1]">
          Loading assessment report from backend…
        </p>
      </div>
    )
  }

  if (errorMessage || !assessment) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Assessment Not Available
          </h2>
          <p className="text-sm text-[#44403C] dark:text-[#D6D3D1] max-w-md mx-auto leading-relaxed">
            {errorMessage || 'The requested assessment could not be loaded from the backend.'}
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/assessments"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold no-underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Assessment History</span>
          </Link>
        </div>
      </div>
    )
  }

  const { summary } = assessment
  const scannedCount = assessment.coverage?.scanned?.length ?? 3
  const totalClassesCount = scannedCount + (assessment.coverage?.not_scanned?.length ?? 10)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* ── Top Toolbar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <Link
            to="/assessments"
            className={`p-2.5 rounded-xl border transition-colors cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#D6D3D1] hover:bg-[#2C2723]'
                : 'bg-white border-[#E2D9CF] text-[#44403C] hover:bg-stone-50'
            }`}
            title="Back to History"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-2xl sm:text-3xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
                {assessment.assessment_id}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-[#8BA470]/20 text-[#3A5228] dark:text-[#A7BF8C] border border-[#8BA470]/30">
                {assessment.status.toUpperCase()}
              </span>
            </div>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
              Assessed on {new Date(assessment.created_at).toLocaleString()} • Vision Model:{' '}
              <span className="font-mono font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                {assessment.model_version}
              </span>
              {assessment.processing_time_ms ? ` (${assessment.processing_time_ms}ms)` : ''}
            </p>
          </div>
        </div>

        <div>
          <Link
            to="/assess"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-bold shadow-xs transition-all no-underline"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Assess Another Sample</span>
          </Link>
        </div>
      </div>

      {/* ── Demo Notice Banner ── */}
      {assessment.assessment_id.startsWith('BV-DEMO-') && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-950 dark:text-amber-200">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-amber-700 dark:text-amber-400 shrink-0" />
            <p className="text-xs font-semibold">
              You are viewing an interactive demo green coffee screening report.
            </p>
          </div>
          <button
            type="button"
            onClick={handleDeleteDemo}
            className="px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Demo Data</span>
          </button>
        </div>
      )}

      {/* ── 4 Real Summary Metric Cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Defect Regions */}
        <div className={`p-5 ${card}`}>
          <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
            Total Defect Regions
          </p>
          <p className="text-3xl font-extrabold font-serif text-[#1C1917] dark:text-[#F9F7F2] mt-2">
            {summary.detection_count}
          </p>
          <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
            Bounding regions segmented
          </p>
        </div>

        {/* Primary Defects */}
        <div className={`p-5 ${card}`}>
          <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
            Primary Defects
          </p>
          <p className="text-3xl font-extrabold font-serif text-rose-700 dark:text-rose-400 mt-2">
            {summary.primary_detection_count}
          </p>
          <p className="text-xs font-medium text-rose-700 dark:text-rose-400 mt-1">
            Severe defect regions (Full Black)
          </p>
        </div>

        {/* Secondary Defects */}
        <div className={`p-5 ${card}`}>
          <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
            Secondary Defects
          </p>
          <p className="text-3xl font-extrabold font-serif text-amber-700 dark:text-amber-400 mt-2">
            {summary.secondary_detection_count}
          </p>
          <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
            Minor defect regions (Partial, Husk)
          </p>
        </div>

        {/* Scanned Classes */}
        <div className={`p-5 ${card}`}>
          <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
            Model Coverage
          </p>
          <p className="text-3xl font-extrabold font-serif text-[#3A5228] dark:text-[#8BA470] mt-2">
            {scannedCount} of {totalClassesCount}
          </p>
          <p className="text-xs font-medium text-[#3A5228] dark:text-[#8BA470] mt-1">
            Supported ECX defect classes
          </p>
        </div>
      </div>

      {/* ── Optical Inspection Image ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-5`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Optical Defect Localization
            </h3>
            <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-0.5">
              Inspect bounding boxes localized by the vision inference model.
            </p>
          </div>

          <div className="inline-flex p-1 rounded-xl border bg-[#FAF8F5] dark:bg-[#181513] border-[#E2D9CF] dark:border-[#382E26]">
            {(['annotated', 'original'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === mode
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#44403C] dark:text-[#D6D3D1] hover:text-[#1C1917] dark:hover:text-[#F9F7F2]'
                }`}
              >
                {mode === 'annotated' ? 'Annotated Defect View' : 'Original Sample Photo'}
              </button>
            ))}
          </div>
        </div>

        {/* Image Display */}
        <div className="relative rounded-2xl overflow-hidden aspect-video max-h-[540px] bg-stone-900 border border-[#E2D9CF] dark:border-[#382E26] flex items-center justify-center">
          <img
            src={
              viewMode === 'annotated'
                ? assessment.annotated_image_url || assessment.original_image_url
                : assessment.original_image_url
            }
            alt="Sample Visual Inspection"
            className="w-full h-full object-contain"
          />
        </div>
      </div>

      {/* ── Defect Classification Breakdown ── */}
      <div className={`p-6 sm:p-7 ${card} space-y-5`}>
        <div>
          <h3 className="text-lg font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
            Granular Defect Class Tally
          </h3>
          <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-0.5">
            Detections grouped by recognized ECX defect taxonomy class.
          </p>
        </div>

        {assessment.summary.by_class.length === 0 ? (
          <div className="py-8 text-center text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
            Zero defects detected across scanned defect classes.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2D9CF] dark:border-[#382E26] text-[#44403C] dark:text-[#D6D3D1]">
                  <th className="pb-3.5 font-bold">Defect Class</th>
                  <th className="pb-3.5 font-bold">ECX Category</th>
                  <th className="pb-3.5 font-bold">Detected Regions</th>
                  <th className="pb-3.5 font-bold text-right">Mean Model Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2D9CF] dark:divide-[#382E26]">
                {assessment.summary.by_class.map((tally) => {
                  const confPercent = (tally.mean_confidence * 100).toFixed(1)
                  const isPrimary = tally.defect.category === 'primary'

                  return (
                    <tr key={tally.defect.key} className="hover:bg-stone-500/5">
                      <td className="py-3.5 font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                        {tally.defect.name}
                      </td>

                      <td className="py-3.5">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            isPrimary
                              ? 'bg-rose-500/15 text-rose-800 dark:text-rose-300 border border-rose-500/30'
                              : 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30'
                          }`}
                        >
                          {isPrimary ? 'Primary Defect' : 'Secondary Defect'}
                        </span>
                      </td>

                      <td className="py-3.5 font-mono font-bold text-sm text-[#1C1917] dark:text-[#F9F7F2]">
                        {tally.count}
                      </td>

                      <td className="py-3.5 text-right font-mono font-bold text-sm text-[#382416] dark:text-[#C4A882]">
                        {confPercent}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Real Coverage & Model Limitations ── */}
      {assessment.limitations && assessment.limitations.length > 0 && (
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-[#593D2B] dark:text-[#8BA470]" />
            <h3 className="text-base font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Standard Model Limitations & Transparency Notice
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {assessment.limitations.map((lim, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-[#E2D9CF] dark:border-[#382E26] bg-[#FAF8F5] dark:bg-[#181513] space-y-1"
              >
                <div className="font-mono text-xs font-bold text-[#593D2B] dark:text-[#A7BF8C]">
                  {lim.code}
                </div>
                <div className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] leading-relaxed">
                  {lim.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Gemini Agronomy Advisory (if returned by backend) ── */}
      {assessment.advisory?.summary && (
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <Sparkles className="w-5 h-5 text-[#593D2B] dark:text-[#8BA470]" />
              <h3 className="font-bold text-base font-serif text-[#382416] dark:text-[#F9F7F2]">
                Gemini Advisory ({assessment.advisory.generator_model})
              </h3>
            </div>

            <div className="flex items-center space-x-1.5 bg-[#FAF8F5] dark:bg-[#181513] p-1 rounded-xl border border-[#E2D9CF] dark:border-[#382E26]">
              <button
                type="button"
                onClick={() => setLanguageMode('en')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  languageMode === 'en'
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#44403C] dark:text-[#D6D3D1]'
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLanguageMode('am')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  languageMode === 'am'
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#44403C] dark:text-[#D6D3D1]'
                }`}
              >
                አማርኛ
              </button>
            </div>
          </div>

          <p className="text-sm font-medium leading-relaxed text-[#1C1917] dark:text-[#F9F7F2] bg-[#FAF8F5] dark:bg-[#181513] p-4 rounded-xl border border-[#E2D9CF] dark:border-[#382E26]">
            {languageMode === 'en'
              ? assessment.advisory.summary.en
              : assessment.advisory.summary.am}
          </p>

          {assessment.advisory.recommendations?.length > 0 && (
            <div className="space-y-2 pt-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
                Recommended Actions:
              </span>
              <ul className="list-disc pl-5 space-y-1.5 text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
                {assessment.advisory.recommendations.map((rec, i) => (
                  <li key={i}>
                    {languageMode === 'en' ? rec.en : rec.am}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── Mandatory AI Notice ── */}
      <div className="p-4 rounded-2xl border border-amber-300 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-800 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="text-xs text-amber-950 dark:text-amber-200 leading-relaxed font-medium">
          <strong>Decision-Support Notice:</strong> BunaVision provides automated optical defect region
          segmentation for pre-roast green coffee bean samples. It is not an official ECX or SCA grade certificate
          and must not be presented as one. Final batch classification requires physical inspection, sensory cup
          evaluation, and certified Q-grader verification.
        </p>
      </div>
    </div>
  )
}
