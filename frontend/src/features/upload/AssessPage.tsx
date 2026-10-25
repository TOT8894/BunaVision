import { useState } from 'react'
import { useNavigate, Link } from 'react-router'
import {
  Upload,
  Camera,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  Info,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { CameraModal } from '../../components/CameraModal'
import { PRESET_SAMPLES, ETHIOPIAN_ORIGINS } from '../../constants/data'
import type { PresetSample, UnifiedAssessment } from '../../types/app'
import { uploadAssessmentToBackend } from '../../services/assessmentService'

// Store real assessments from this session in memory
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
  const [stationName, setStationName] = useState('')
  const [lotNumber, setLotNumber] = useState('')
  const [moistureLevel, setMoistureLevel] = useState('')
  const [varietal, setVarietal] = useState('')
  const [notes, setNotes] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingStep, setProcessingStep] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [cameraOpen, setCameraOpen] = useState(false)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-md shadow-black/20'
      : 'bg-white border-[#E8E0D5] shadow-xs'
  }`

  const inputCls = `w-full px-3 py-2 rounded-xl text-sm border focus:outline-none focus:ring-2 focus:ring-[#8BA470] transition-colors ${
    theme === 'dark'
      ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
      : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#24211D]'
  }`

  const handleFileInput = (file: File) => {
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setErrorMessage(null)
  }

  const handleSelectPreset = (preset: PresetSample) => {
    setPreviewUrl(preset.url)
    setSelectedFile(null)
    setStationName(preset.station)
    setLotNumber(preset.lot)
    setMoistureLevel(preset.moisture)
    setErrorMessage(null)
  }

  const handleSelectOrigin = (origin: (typeof ETHIOPIAN_ORIGINS)[0]) => {
    setStationName(`${origin.name} Station`)
    setVarietal(origin.defaultVarietal)
    setNotes(`Origin Altitude: ${origin.alt} | Soil type: ${origin.soil}`)
  }

  const handleStartAnalysis = async () => {
    if (!previewUrl) {
      setErrorMessage('Please select or upload a sample photograph first.')
      return
    }

    if (!authToken) {
      navigate('/login')
      return
    }

    setIsProcessing(true)
    setErrorMessage(null)
    setProcessingProgress(20)
    setProcessingStep('Preparing sample image bytes...')

    try {
      let fileToUpload = selectedFile

      // If preset URL was selected, fetch blob and turn into File
      if (!fileToUpload && previewUrl) {
        setProcessingStep('Loading sample preset image...')
        const res = await fetch(previewUrl)
        if (!res.ok) throw new Error('Failed to load preset sample image.')
        const blob = await res.blob()
        fileToUpload = new File([blob], 'coffee_sample.jpg', {
          type: blob.type || 'image/jpeg',
        })
      }

      if (!fileToUpload) {
        throw new Error('No valid image file available for assessment.')
      }

      setProcessingProgress(50)
      setProcessingStep('Transmitting to BunaVision FastAPI Backend...')

      const liveResult = await uploadAssessmentToBackend(
        fileToUpload,
        {
          station_id: stationName || undefined,
          lot_number: lotNumber || undefined,
          moisture_level: moistureLevel || undefined,
          varietal: varietal || undefined,
          notes: notes || undefined,
        },
        authToken,
      )

      setProcessingProgress(100)
      setProcessingStep('Assessment completed!')
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* ── Top Header ── */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
          Assess Coffee Bean Sample
        </h1>
        <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB] mt-1.5">
          Upload a photograph of pre-roast green coffee beans to generate a preliminary defect region report.
        </p>
      </div>

      {/* ── Error Banner if any ── */}
      {errorMessage && (
        <div className="p-4 rounded-2xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold text-red-800 dark:text-red-200">
              Assessment Failed
            </h4>
            <p className="text-xs text-red-700 dark:text-red-300 leading-relaxed">
              {errorMessage}
            </p>
          </div>
        </div>
      )}

      {/* ── Main 2-Column Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Form & Upload (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Card 1: Image Selector */}
          <div className={`p-6 sm:p-7 ${card} space-y-5`}>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                1. Select Sample Photograph
              </h2>
              <button
                type="button"
                onClick={() => setCameraOpen(true)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border flex items-center gap-1.5 cursor-pointer transition-colors ${
                  theme === 'dark'
                    ? 'bg-[#181513] border-[#382E26] text-[#C8C2BB] hover:bg-[#2C2723]'
                    : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#5A544C] hover:bg-stone-100'
                }`}
              >
                <Camera className="w-3.5 h-3.5 text-[#593D2B] dark:text-[#8BA470]" />
                <span>Use Device Camera</span>
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
                  ? 'border-[#8BA470]/60 bg-[#8BA470]/5'
                  : theme === 'dark'
                    ? 'border-[#382E26] hover:border-[#8BA470]/50 bg-[#181513]/50'
                    : 'border-[#DDD5C8] hover:border-[#8BA470] bg-[#FAF8F5]'
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
                  <div className="relative mx-auto max-w-xs rounded-xl overflow-hidden aspect-video border border-[#E8E0D5] dark:border-[#382E26] shadow-sm">
                    <img
                      src={previewUrl}
                      alt="Sample preview"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-[#3B2416] dark:text-[#F9F7F2]">
                      {selectedFile ? selectedFile.name : 'Preset Sample Loaded'}
                    </p>
                    <p className="text-[11px] text-[#7B7569] dark:text-[#A8A193]">
                      Click or drag a different file to replace
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-[#593D2B]/10 dark:bg-[#593D2B]/30 flex items-center justify-center mx-auto text-[#593D2B] dark:text-[#C4A882]">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-[#3B2416] dark:text-[#F9F7F2]">
                      Drag & drop sample photo here, or click to browse
                    </p>
                    <p className="text-xs text-[#7B7569] dark:text-[#A8A193]">
                      Supports JPEG & PNG up to 15MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Presets */}
            <div className="space-y-2.5 pt-2">
              <p className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                Or test instantly using a sample preset:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {PRESET_SAMPLES.slice(0, 3).map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handleSelectPreset(preset)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      previewUrl === preset.url
                        ? 'border-[#8BA470] bg-[#8BA470]/10 text-[#3B2416] dark:text-[#F9F7F2]'
                        : theme === 'dark'
                          ? 'bg-[#181513] border-[#382E26] text-[#C8C2BB] hover:border-[#593D2B]'
                          : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#5A544C] hover:border-[#DDD5C8]'
                    }`}
                  >
                    <div className="text-xs font-bold truncate">{preset.name}</div>
                    <div className="text-[11px] text-[#7B7569] dark:text-[#A8A193] truncate mt-0.5">
                      {preset.station}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Card 2: Batch Metadata */}
          <div className={`p-6 sm:p-7 ${card} space-y-5`}>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                2. Batch Metadata (Optional)
              </h2>
              <span className="text-[11px] text-[#7B7569] dark:text-[#A8A193]">
                Helps traceability in export logs
              </span>
            </div>

            {/* Quick Origin Select */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                Quick Origin Autofill:
              </label>
              <div className="flex flex-wrap gap-2">
                {ETHIOPIAN_ORIGINS.slice(0, 4).map((origin) => (
                  <button
                    key={origin.name}
                    type="button"
                    onClick={() => handleSelectOrigin(origin)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                      theme === 'dark'
                        ? 'bg-[#181513] border-[#382E26] text-[#C8C2BB] hover:bg-[#2C2723]'
                        : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#5A544C] hover:bg-stone-100'
                    }`}
                  >
                    {origin.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Washing Station / Field Lab
                </label>
                <input
                  type="text"
                  placeholder="e.g. Yirgacheffe Station #04"
                  value={stationName}
                  onChange={(e) => setStationName(e.target.value)}
                  className={inputCls}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Lot / Batch Identifier
                </label>
                <input
                  type="text"
                  placeholder="e.g. YIR-2026-102"
                  value={lotNumber}
                  onChange={(e) => setLotNumber(e.target.value)}
                  className={inputCls}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Moisture Level (%)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 11.0%"
                  value={moistureLevel}
                  onChange={(e) => setMoistureLevel(e.target.value)}
                  className={inputCls}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Varietal / Process
                </label>
                <input
                  type="text"
                  placeholder="e.g. Kurume / Fully Washed"
                  value={varietal}
                  onChange={(e) => setVarietal(e.target.value)}
                  className={inputCls}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                Agronomist Notes
              </label>
              <textarea
                rows={2}
                placeholder="Add any context regarding drying floor settings, weather conditions, or hulling machinery..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className={inputCls}
              />
            </div>
          </div>

          {/* Action Button */}
          <div>
            {!authToken ? (
              <div className="p-4 rounded-2xl border border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-950/20 flex items-center justify-between gap-4">
                <div className="flex items-center gap-2.5">
                  <Info className="w-5 h-5 text-amber-700 dark:text-amber-400 shrink-0" />
                  <p className="text-xs text-amber-900 dark:text-amber-300">
                    Please sign in to submit assessments to the backend.
                  </p>
                </div>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-xl bg-[#593D2B] text-white text-xs font-bold no-underline whitespace-nowrap"
                >
                  Sign In
                </Link>
              </div>
            ) : (
              <button
                type="button"
                disabled={isProcessing || !previewUrl}
                onClick={handleStartAnalysis}
                className={`w-full py-4 rounded-xl text-sm font-bold flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer ${
                  !previewUrl || isProcessing
                    ? 'bg-stone-300 dark:bg-stone-800 text-stone-500 cursor-not-allowed'
                    : 'bg-[#593D2B] hover:bg-[#483020] text-white hover:scale-[1.005]'
                }`}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Sample ({processingProgress}%)…</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-[#8BA470]" />
                    <span>Run AI Defect Assessment</span>
                  </>
                )}
              </button>
            )}

            {isProcessing && (
              <div className="mt-3 space-y-1.5">
                <div className="w-full bg-stone-200 dark:bg-stone-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#8BA470] h-full transition-all duration-300"
                    style={{ width: `${processingProgress}%` }}
                  />
                </div>
                <p className="text-[11px] text-[#7B7569] dark:text-[#A8A193] text-center">
                  {processingStep}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Photography Protocol */}
        <div className="space-y-6">
          <div className={`p-6 sm:p-7 ${card} space-y-6`}>
            <div>
              <h2 className="text-base font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                Sample Photography Protocol
              </h2>
              <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
                To ensure maximum accuracy from the YOLO defect model, follow these green bean presentation guidelines:
              </p>
            </div>

            <div className="space-y-2.5">
              <div className="p-3 rounded-xl border border-[#8BA470]/40 bg-[#8BA470]/10 text-[#3A5228] dark:text-[#B5CF97] text-xs font-medium">
                ✓ Single Layer Bean Spreading: Beans must not touch or overlap.
              </div>

              <div className="p-3 rounded-xl border border-[#8BA470]/40 bg-[#8BA470]/10 text-[#3A5228] dark:text-[#B5CF97] text-xs font-medium">
                ✓ High Contrast Surface: Place beans against a plain light matte tray.
              </div>

              <div className="p-3 rounded-xl border border-rose-200 dark:border-rose-900/40 bg-rose-50 dark:bg-rose-950/20 text-rose-800 dark:text-rose-300 text-xs font-medium">
                ✕ Avoid Overhead Glare: Harsh reflections degrade defect segmentation.
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <p className="text-xs font-bold text-[#5A544C] dark:text-[#C8C2BB]">
                Visual Setup Reference:
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5 text-center">
                  <div className="rounded-xl overflow-hidden aspect-square border border-[#8BA470]/40">
                    <img
                      src="/coffee_drying_closeup.jpg"
                      alt="Correct setup"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <span className="text-[11px] font-bold text-[#4F7335] dark:text-[#8BA470]">
                    ✓ Correct Setup
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
                  <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400">
                    ✕ Too Cluttered
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
