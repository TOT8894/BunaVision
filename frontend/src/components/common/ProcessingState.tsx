import React, { useEffect, useState } from 'react'
import { Loader2, Clock, XCircle } from 'lucide-react'

export interface ProcessingStateProps {
  statusText?: string
  subtext?: string
  showElapsed?: boolean
  onCancel?: () => void
  cancelLabel?: string
  delayWarningSeconds?: number
  className?: string
}

export const ProcessingState: React.FC<ProcessingStateProps> = ({
  statusText = 'Analyzing coffee sample...',
  subtext = 'Our computer vision model is detecting visible defects.',
  showElapsed = true,
  onCancel,
  cancelLabel = 'Cancel processing',
  delayWarningSeconds = 25,
  className = '',
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  useEffect(() => {
    if (!showElapsed) return

    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [showElapsed])

  const isTakingLong = elapsedSeconds >= delayWarningSeconds

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex flex-col items-center justify-center rounded-2xl border border-coffee-100 bg-white/90 p-8 text-center shadow-xs ${className}`}
    >
      {/* Animated spinner */}
      <div className="relative mb-5 flex h-16 w-16 items-center justify-center">
        <div className="absolute inset-0 rounded-full border-4 border-coffee-100 opacity-60" />
        <Loader2 className="h-10 w-10 animate-spin text-coffee-700" aria-hidden="true" />
      </div>

      <h3 className="text-lg font-semibold text-slate-900">{statusText}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-slate-600">{subtext}</p>

      {/* Elapsed time indicator */}
      {showElapsed && (
        <div className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          <Clock className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
          <span>Elapsed time: {elapsedSeconds}s</span>
        </div>
      )}

      {/* Long wait helper text */}
      {isTakingLong && (
        <p className="mt-3 max-w-xs text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
          Inference is taking longer than usual. Please remain on this page while the model
          processes your image.
        </p>
      )}

      {/* Optional Cancel button */}
      {onCancel && (
        <button
          type="button"
          onClick={onCancel}
          className="mt-6 inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-rose-700 focus:outline-hidden transition-colors"
        >
          <XCircle className="h-4 w-4" aria-hidden="true" />
          <span>{cancelLabel}</span>
        </button>
      )}
    </div>
  )
}
