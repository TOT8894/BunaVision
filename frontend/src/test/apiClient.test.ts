import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import { normalizeError, validateWithSchema, ApiError } from '../services/apiClient'

describe('apiClient utilities', () => {
  it('normalizes error correctly into ApiError instance', () => {
    const error = normalizeError(new Error('Network failure'))
    expect(error).toBeInstanceOf(ApiError)
    expect(error.code).toBe('INTERNAL_ERROR')
    expect(error.message).toBe('Network failure')
  })

  it('validates matching data against Zod schema successfully', () => {
    const schema = z.object({ name: z.string() })
    const data = { name: 'BunaVision' }
    const validated = validateWithSchema(data, schema)
    expect(validated).toEqual(data)
  })

  it('throws ApiError with INVALID_RESPONSE when schema does not match', () => {
    const schema = z.object({ count: z.number() })
    const invalidData = { count: 'not-a-number' }

    expect(() => validateWithSchema(invalidData, schema)).toThrowError(ApiError)
    try {
      validateWithSchema(invalidData, schema)
    } catch (err) {
      const apiErr = err as ApiError
      expect(apiErr.code).toBe('INVALID_RESPONSE')
    }
  })
})
