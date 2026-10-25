export type ErrorCode =
  | 'INVALID_IMAGE'
  | 'IMAGE_TOO_LARGE'
  | 'UNSUPPORTED_FORMAT'
  | 'INFERENCE_FAILED'
  | 'ASSESSMENT_NOT_FOUND'
  | 'UNAUTHORIZED'
  | 'RATE_LIMITED'
  | 'INTERNAL_ERROR'
  | 'NETWORK_ERROR'
  | 'TIMEOUT'
  | 'INVALID_RESPONSE'

export interface ApiErrorDetail {
  field?: string
  issue?: string
  [key: string]: unknown
}

export interface ApiErrorBody {
  error: {
    code: ErrorCode
    message: string
    details?: unknown
  }
}

export interface PaginatedListResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}
