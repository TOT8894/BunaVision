import type { ErrorCode } from '../types/api'

export interface ErrorMessageDefinition {
  code: ErrorCode
  message: string
  nextStep: string
}

export const ERROR_MESSAGES: Record<ErrorCode, ErrorMessageDefinition> = {
  UNSUPPORTED_FORMAT: {
    code: 'UNSUPPORTED_FORMAT',
    message: "This file type isn't supported. Please upload a JPEG or PNG photo.",
    nextStep: 'Choose another file',
  },
  IMAGE_TOO_LARGE: {
    code: 'IMAGE_TOO_LARGE',
    message: 'This image is larger than the maximum allowed size. Try a lower-resolution photo.',
    nextStep: 'Choose another file',
  },
  INVALID_IMAGE: {
    code: 'INVALID_IMAGE',
    message: "We couldn't read this image. Try taking the photo again.",
    nextStep: 'Choose another file',
  },
  INFERENCE_FAILED: {
    code: 'INFERENCE_FAILED',
    message: "The analysis didn't complete. Your image was not assessed.",
    nextStep: 'Retry or try another photo',
  },
  ASSESSMENT_NOT_FOUND: {
    code: 'ASSESSMENT_NOT_FOUND',
    message: "We couldn't find that assessment.",
    nextStep: 'Return to assessment history',
  },
  UNAUTHORIZED: {
    code: 'UNAUTHORIZED',
    message: 'Please sign in to access this assessment.',
    nextStep: 'Sign in',
  },
  RATE_LIMITED: {
    code: 'RATE_LIMITED',
    message: 'Too many requests. Please wait a moment and try again.',
    nextStep: 'Wait a moment and retry',
  },
  INTERNAL_ERROR: {
    code: 'INTERNAL_ERROR',
    message: 'Something went wrong on our side. Please try again.',
    nextStep: 'Try again in a few moments',
  },
  NETWORK_ERROR: {
    code: 'NETWORK_ERROR',
    message: "Can't reach the server. Check your internet connection and try again.",
    nextStep: 'Check your connection and retry',
  },
  TIMEOUT: {
    code: 'TIMEOUT',
    message: 'The request took longer than expected and timed out.',
    nextStep: 'Check your connection and try again',
  },
  INVALID_RESPONSE: {
    code: 'INVALID_RESPONSE',
    message: 'We received an unexpected response format from the server.',
    nextStep: 'Try again later or contact support',
  },
}

export const DEFAULT_ERROR_MESSAGE: ErrorMessageDefinition = {
  code: 'INTERNAL_ERROR',
  message: 'An unexpected error occurred. Please try again.',
  nextStep: 'Try again in a few moments',
}

/**
 * Returns user-friendly error message and next recommended action for an ErrorCode.
 */
export function getErrorMessage(code?: string | null): ErrorMessageDefinition {
  if (!code) {
    return DEFAULT_ERROR_MESSAGE
  }

  const recognized = ERROR_MESSAGES[code as ErrorCode]
  if (recognized) {
    return recognized
  }

  return {
    code: 'INTERNAL_ERROR',
    message: 'An unexpected error occurred. Please try again.',
    nextStep: 'Try again in a few moments',
  }
}
