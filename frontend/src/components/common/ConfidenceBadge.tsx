import React from 'react'
import { AlertTriangle } from 'lucide-react'
import { env } from '../../config/env'

export interface ConfidenceBadgeProps {
  confidence: number // 0 to 1
  threshold?: number // default to env.lowConfidenceThreshold
  showLabel?: boolean
  className?: string
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  threshold = env.lowConfidenceThreshold,
  showLabel = true,
  className = '',
}) => {
  // Clamp confidence to 0..1
  const clamped = Math.max(0, Math.min(1, confidence))
  const percentage = Math.round(clamped * 100)
  const isLowConfidence = clamped < threshold

  return (
    <div className={`inline-flex items-center gap-1.5 flex-wrap ${className}`}>
      <span
        className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold border ${
          isLowConfidence
            ? 'bg-amber-50 text-amber-950 border-amber-300'
            : 'bg-emerald-50 text-emerald-950 border-emerald-300'
        }`}
        title={`Model confidence: ${percentage}% (threshold: ${Math.round(threshold * 100)}%)`}
      >
        <span>{percentage}%</span>
        {showLabel && <span className="text-xs font-medium opacity-90">Model confidence</span>}
      </span>

      {isLowConfidence && (
        <span
          className="inline-flex items-center gap-1 rounded-md bg-amber-100 text-amber-900 border border-amber-300/80 px-2 py-0.5 text-xs font-semibold"
          title="Prediction confidence is below threshold; please verify manually"
        >
          <AlertTriangle className="h-3 w-3 text-amber-700 shrink-0" aria-hidden="true" />
          <span>Review manually</span>
        </span>
      )}
    </div>
  )
}
