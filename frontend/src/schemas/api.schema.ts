import { z } from 'zod'

export const errorCodeSchema = z.enum([
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
])

export const apiErrorBodySchema = z.object({
  error: z.object({
    code: errorCodeSchema,
    message: z.string(),
    details: z.unknown().optional(),
  }),
})

export function createPaginatedListResponseSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive(),
    has_more: z.boolean(),
  })
}
