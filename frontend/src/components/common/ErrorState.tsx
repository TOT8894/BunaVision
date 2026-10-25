import React from 'react'
import { AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react'
import type { ErrorCode } from '../../types/api'
import { getErrorMessage } from '../../utils/errorMessages'

export interface ErrorStateProps {
  title?: string
  message?: string
  nextStep?: string
  errorCode?: ErrorCode
  onRetry?: () => void
  onBack?: () => void
  retryLabel?: string
  backLabel?: string
  className?: string
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  nextStep,
  errorCode,
  onRetry,
  onBack,
  retryLabel = 'Try again',
  backLabel = 'Go back',
  className = '',
}) => {
  const errorInfo = errorCode ? getErrorMessage(errorCode) : null

  const displayTitle = title || (errorCode ? `Error: ${errorCode}` : 'Something went wrong')
  const displayMessage = message || errorInfo?.message || 'An unexpected problem occurred.'
  const displayNextStep = nextStep || errorInfo?.nextStep

  return (
    <div
      role="alert"
      className={`rounded-xl border border-rose-200 bg-rose-50/60 p-6 text-center text-slate-800 ${className}`}
    >
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-700">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
      </div>

      <h3 className="mt-3 text-base font-semibold text-rose-950 sm:text-lg">{displayTitle}</h3>

      <p className="mt-2 text-sm text-slate-700 max-w-md mx-auto">{displayMessage}</p>

      {displayNextStep && (
        <div className="mt-3 inline-block rounded-md bg-white/80 border border-rose-200/80 px-3 py-1.5 text-xs text-rose-900">
          <strong className="font-semibold">Recommended action:</strong> {displayNextStep}
        </div>
      )}

      {(onRetry || onBack) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-2 rounded-lg bg-coffee-700 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-coffee-800 focus:outline-hidden focus:ring-2 focus:ring-coffee-700/50 transition-colors"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              <span>{retryLabel}</span>
            </button>
          )}

          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-slate-400 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              <span>{backLabel}</span>
            </button>
          )}
        </div>
      )}
    </div>
  )
}
