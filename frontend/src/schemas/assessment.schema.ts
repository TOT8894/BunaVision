import { z } from 'zod'
import { errorCodeSchema } from './api.schema'

export const assessmentStatusSchema = z.enum(['pending', 'processing', 'completed', 'failed'])

export const predictionSchema = z.object({
  class_name: z.string(),
  confidence: z.number().min(0).max(1),
  count: z.number().int().nonnegative(),
})

export const assessmentSummarySchema = z.object({
  detected_classes: z.number().int().nonnegative(),
  detection_count: z.number().int().nonnegative(),
})

export const assessmentSchema = z.object({
  assessment_id: z.string().min(1),
  status: assessmentStatusSchema,
  model_version: z.string().min(1),
  created_at: z.string(),
  completed_at: z.string().nullable().optional(),
  summary: assessmentSummarySchema.optional(),
  predictions: z.array(predictionSchema).optional(),
  original_image_url: z.string().nullable().optional(),
  annotated_image_url: z.string().nullable(),
  limitations: z.array(z.string()),
  error_code: errorCodeSchema.nullable().optional(),
  detection_count: z.number().int().nonnegative().optional(),
})

export const assessmentListResponseSchema = z.object({
  items: z.array(assessmentSchema),
  next_cursor: z.string().nullable(),
})
