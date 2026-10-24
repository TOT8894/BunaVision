import { describe, it, expect } from 'vitest'
import { getErrorMessage, ERROR_MESSAGES } from '../utils/errorMessages'
import type { ErrorCode } from '../types/api'

describe('errorMessages', () => {
  const errorCodes: ErrorCode[] = [
    'INVALID_IMAGE',
    'IMAGE_TOO_LARGE',
    'UNSUPPORTED_FORMAT',
    'INFERENCE_FAILED',
    'ASSESSMENT_NOT_FOUND',
    'UNAUTHORIZED',
    'RATE_LIMITED',
    'INTERNAL_ERROR',
    'NETWORK_ERROR',
    'TIMEOUT',
    'INVALID_RESPONSE',
  ]

  it('maps every documented error code to a message and a next action', () => {
    for (const code of errorCodes) {
      const entry = ERROR_MESSAGES[code]
      expect(entry).toBeDefined()
      expect(entry.code).toBe(code)
      expect(entry.message).toBeTruthy()
      expect(entry.nextStep).toBeTruthy()

      const helperResult = getErrorMessage(code)
      expect(helperResult.code).toBe(code)
      expect(helperResult.message).toBe(entry.message)
      expect(helperResult.nextStep).toBe(entry.nextStep)
    }
  })

  it('returns a fallback message for undefined or unknown error codes', () => {
    const fromNull = getErrorMessage(null)
    expect(fromNull.message).toBeTruthy()
    expect(fromNull.nextStep).toBeTruthy()

    const fromUnknown = getErrorMessage('SOME_RANDOM_CODE')
    expect(fromUnknown.code).toBe('INTERNAL_ERROR')
    expect(fromUnknown.message).toBeTruthy()
  })
})
