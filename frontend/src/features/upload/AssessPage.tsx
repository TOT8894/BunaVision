import { useState } from 'react'
import { useNavigate } from 'react-router'
import {
  Upload,
  Camera,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { CameraModal } from '../../components/CameraModal'
import { PRESET_SAMPLES } from '../../constants/data'
import type { PresetSample, UnifiedAssessment } from '../../types/app'
import { uploadAssessmentToBackend } from '../../services/assessmentService'

// Store assessments in memory for this session
let sessionAssessments: UnifiedAssessment[] = []
export function getSessionAssessments() {
  return sessionAssessments
}
export function addSessionAssessment(a: UnifiedAssessment) {
  sessionAssessments = [a, ...sessionAssessments.filter((x) => x.assessment_id !== a.assessment_id)]
}

export function AssessPage() {
  const { theme } = useTheme()
  const { authToken } = useAuth()
  const navigate = useNavigate()

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingStep, setProcessingStep] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [cameraOpen, setCameraOpen] = useState(false)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
  }`

  const handleFileInput = (file: File) => {
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setErrorMessage(null)
  }

  const handleSelectPreset = (preset: PresetSample) => {
    setPreviewUrl(preset.url)
    setSelectedFile(null)
    setErrorMessage(null)
  }

  const handleStartAnalysis = async () => {
    if (!previewUrl) {
      setErrorMessage('Please select or capture a coffee bean photograph.')
      return
    }

    if (!authToken) {
      navigate('/login', { state: { from: '/assess' } })
      return
    }

    setIsProcessing(true)
    setErrorMessage(null)
    setProcessingProgress(25)
    setProcessingStep('Reading image data…')

    try {
      let fileToUpload = selectedFile

      if (!fileToUpload && previewUrl) {
        setProcessingStep('Preparing sample image bytes…')
        const res = await fetch(previewUrl)
        if (!res.ok) throw new Error('Could not load preset sample image.')
        const blob = await res.blob()
        fileToUpload = new File([blob], 'sample.jpg', {
          type: blob.type || 'image/jpeg',
        })
      }

      if (!fileToUpload) {
        throw new Error('No valid image file available for assessment.')
      }

      setProcessingProgress(60)
      setProcessingStep('Uploading image to BunaVision Backend…')

      const idempotencyKey = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`

      const liveResult = await uploadAssessmentToBackend(
        fileToUpload,
        { idempotencyKey },
        authToken,
      )

      setProcessingProgress(100)
      setProcessingStep('Analysis finished successfully!')
      addSessionAssessment(liveResult)
      setIsProcessing(false)
      navigate(`/assessments/${liveResult.assessment_id}`)
    } catch (err: unknown) {
      setIsProcessing(false)
      setProcessingProgress(0)
      setProcessingStep('')
      const msg =
        err instanceof Error
          ? err.message
          : 'Backend assessment request failed. Please check network connectivity and backend service status.'
      setErrorMessage(msg)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* ── Top Header ── */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
          Assess Green Coffee Sample
        </h1>
        <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1.5">
          Upload a high-resolution photograph of pre-roast green coffee beans to run optical defect detection.
        </p>
      </div>

      {/* ── Error Banner ── */}
      {errorMessage && (
        <div className="p-4 rounded-2xl border border-red-300 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-700 dark:text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-red-900 dark:text-red-200 uppercase tracking-wide">
              Assessment Failed
            </h4>
            <p className="text-xs font-medium text-red-800 dark:text-red-300 leading-relaxed">
              {errorMessage}
            </p>
          </div>
        </div>
      )}

      {/* ── Main Layout Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Upload & presets (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className={`p-6 sm:p-7 ${card} space-y-5`}>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
                Select Sample Photograph
              </h2>
              <button
                type="button"
                onClick={() => setCameraOpen(true)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 cursor-pointer transition-colors ${
                  theme === 'dark'
                    ? 'bg-[#181513] border-[#382E26] text-[#D6D3D1] hover:bg-[#2C2723]'
                    : 'bg-[#FAF8F5] border-[#E2D9CF] text-[#44403C] hover:bg-stone-100'
                }`}
              >
                <Camera className="w-3.5 h-3.5 text-[#593D2B] dark:text-[#8BA470]" />
                <span>Device Camera</span>
              </button>
            </div>

            {/* Dropzone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const file = e.dataTransfer.files[0]
                if (file) handleFileInput(file)
              }}
              className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer ${
                previewUrl
                  ? 'border-[#8BA470] bg-[#8BA470]/5'
                  : theme === 'dark'
                    ? 'border-[#382E26] hover:border-[#8BA470]/50 bg-[#181513]/50'
                    : 'border-[#D1C7BD] hover:border-[#8BA470] bg-[#FAF8F5]'
              }`}
            >
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileInput(file)
                }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              {previewUrl ? (
                <div className="space-y-4">
                  <div className="relative mx-auto max-w-sm rounded-xl overflow-hidden aspect-video border border-[#E2D9CF] dark:border-[#382E26] shadow-xs">
                    <img
                      src={previewUrl}
                      alt="Sample preview"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      {selectedFile ? selectedFile.name : 'Sample Loaded'}
                    </p>
                    <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
                      Click or drag a new image file to replace
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-[#593D2B]/10 dark:bg-[#593D2B]/30 flex items-center justify-center mx-auto text-[#593D2B] dark:text-[#C4A882]">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                      Drag & drop green bean photo here, or click to browse
                    </p>
                    <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1]">
                      Supports JPEG, PNG, WEBP (Max 10MB)
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Presets */}
            <div className="space-y-2.5 pt-2">
              <p className="text-xs font-bold uppercase tracking-wider text-[#44403C] dark:text-[#D6D3D1]">
                Or select an inspection sample preset:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {PRESET_SAMPLES.slice(0, 3).map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handleSelectPreset(preset)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      previewUrl === preset.url
                        ? 'border-[#8BA470] bg-[#8BA470]/10 text-[#1C1917] dark:text-[#F9F7F2]'
                        : theme === 'dark'
                          ? 'bg-[#181513] border-[#382E26] text-[#D6D3D1] hover:border-[#593D2B]'
                          : 'bg-[#FAF8F5] border-[#E2D9CF] text-[#44403C] hover:border-[#D1C7BD]'
                    }`}
                  >
                    <div className="text-xs font-bold truncate">{preset.name}</div>
                    <div className="text-xs text-[#44403C] dark:text-[#D6D3D1] truncate mt-0.5">
                      {preset.station}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Action button */}
          <div>
            <button
              type="button"
              disabled={isProcessing || !previewUrl}
              onClick={handleStartAnalysis}
              className={`w-full py-3.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2 shadow-xs transition-all cursor-pointer ${
                !previewUrl || isProcessing
                  ? 'bg-stone-300 dark:bg-stone-800 text-stone-500 cursor-not-allowed'
                  : 'bg-[#593D2B] hover:bg-[#483020] text-white hover:scale-[1.005]'
              }`}
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing Assessment ({processingProgress}%)…</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Run Defect Assessment</span>
                </>
              )}
            </button>

            {isProcessing && (
              <div className="mt-3 space-y-1.5">
                <div className="w-full bg-stone-200 dark:bg-stone-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#8BA470] h-full transition-all duration-300"
                    style={{ width: `${processingProgress}%` }}
                  />
                </div>
                <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] text-center">
                  {processingStep}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Photography protocol */}
        <div className="space-y-6">
          <div className={`p-6 sm:p-7 ${card} space-y-5`}>
            <div>
              <h2 className="text-base font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
                Photography Protocol
              </h2>
              <p className="text-xs font-medium text-[#44403C] dark:text-[#D6D3D1] mt-1">
                Follow standard presentation guidelines to ensure clean boundary detection:
              </p>
            </div>

            <div className="space-y-2.5">
              <div className="p-3 rounded-xl border border-[#8BA470]/50 bg-[#8BA470]/10 text-[#3A5228] dark:text-[#B5CF97] text-xs font-semibold">
                ✓ Single Layer Layout: Beans must be spread flat without stacking.
              </div>

              <div className="p-3 rounded-xl border border-[#8BA470]/50 bg-[#8BA470]/10 text-[#3A5228] dark:text-[#B5CF97] text-xs font-semibold">
                ✓ High Contrast Surface: Place against a light, matte, shadowless tray.
              </div>

              <div className="p-3 rounded-xl border border-rose-300 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/20 text-rose-900 dark:text-rose-300 text-xs font-semibold">
                ✕ Avoid Direct Glare: Harsh overhead reflections degrade segmentation.
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <p className="text-xs font-bold text-[#1C1917] dark:text-[#F9F7F2]">
                Visual Setup Reference:
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5 text-center">
                  <div className="rounded-xl overflow-hidden aspect-square border border-[#8BA470]/50">
                    <img
                      src="/coffee_drying_closeup.jpg"
                      alt="Correct setup"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <span className="text-xs font-bold text-[#3A5228] dark:text-[#8BA470]">
                    ✓ Clean Flat Layout
                  </span>
                </div>

                <div className="space-y-1.5 text-center">
                  <div className="rounded-xl overflow-hidden aspect-square border border-rose-300 dark:border-rose-900/40">
                    <img
                      src="/coffee_drying_bed_overhead.jpg"
                      alt="Too cluttered"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <span className="text-xs font-bold text-rose-800 dark:text-rose-400">
                    ✕ Cluttered / Piled
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Capture Modal */}
      {cameraOpen && (
        <CameraModal
          onClose={() => setCameraOpen(false)}
          onCapture={(file) => {
            handleFileInput(file)
            setCameraOpen(false)
          }}
        />
      )}
    </div>
  )
}
