import React from 'react'
import { CheckCircle2, AlertCircle, Clock, Loader2 } from 'lucide-react'
import type { AssessmentStatus } from '../../types/assessment'

export interface StatusPillProps {
  status: AssessmentStatus
  className?: string
  size?: 'sm' | 'md'
}

interface StatusConfig {
  label: string
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>
  className: string
}

const STATUS_CONFIG: Record<AssessmentStatus, StatusConfig> = {
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    className: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
  },
  processing: {
    label: 'Processing',
    icon: Loader2,
    className: 'bg-amber-50 text-amber-800 border-amber-200/80 animate-pulse',
  },
  pending: {
    label: 'Pending',
    icon: Clock,
    className: 'bg-slate-100 text-slate-700 border-slate-200',
  },
  failed: {
    label: 'Failed',
    icon: AlertCircle,
    className: 'bg-rose-50 text-rose-800 border-rose-200/80',
  },
}

export const StatusPill: React.FC<StatusPillProps> = ({ status, className = '', size = 'md' }) => {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  const Icon = config.icon

  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-xs gap-1'
      : 'px-2.5 py-1 text-xs sm:text-sm font-medium gap-1.5'

  const iconSizeClasses = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'

  return (
    <span
      className={`inline-flex items-center rounded-full border ${sizeClasses} ${config.className} ${className}`}
      role="status"
      aria-label={`Status: ${config.label}`}
    >
      <Icon
        className={`${iconSizeClasses} shrink-0 ${status === 'processing' ? 'animate-spin' : ''}`}
        aria-hidden="true"
      />
      <span>{config.label}</span>
    </span>
  )
}
