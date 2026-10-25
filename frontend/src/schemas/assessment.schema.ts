import { z } from 'zod'
import { errorCodeSchema } from './api.schema'

const defectSchema = z.object({ key: z.string(), name: z.string(), category: z.enum(['primary', 'secondary']) })
const tallySchema = z.object({ defect: defectSchema, count: z.number().int().nonnegative(), mean_confidence: z.number().min(0).max(1) })
const detectionSchema = z.object({ defect: defectSchema, confidence: z.number().min(0).max(1), box: z.object({ x1: z.number(), y1: z.number(), x2: z.number(), y2: z.number() }) })
export const completedAssessmentSchema = z.object({
  assessment_id: z.string().min(1), status: z.literal('completed'), created_at: z.string(), processing_time_ms: z.number().int().nonnegative(),
  result: z.object({
    model_version: z.string().min(1), summary: z.object({ detection_count: z.number().int().nonnegative(), primary_detection_count: z.number().int().nonnegative(), secondary_detection_count: z.number().int().nonnegative(), by_class: z.array(tallySchema) }),
    detections: z.array(detectionSchema), coverage: z.object({ scanned: z.array(defectSchema), not_scanned: z.array(defectSchema) }), limitations: z.array(z.object({ code: z.string(), message: z.string() })),
    advisory: z.object({ generator_model: z.string(), summary: z.object({ en: z.string(), am: z.string() }), recommendations: z.array(z.object({ en: z.string(), am: z.string() })) }), images: z.object({ original_url: z.string().nullable(), annotated_url: z.string().nullable(), expires_in_s: z.number().int().positive() }),
  }),
})
export const failedAssessmentSchema = z.object({ assessment_id: z.string().min(1), status: z.literal('failed'), created_at: z.string(), processing_time_ms: z.number().int().nonnegative(), error_code: errorCodeSchema })
export const assessmentSchema = z.discriminatedUnion('status', [completedAssessmentSchema, failedAssessmentSchema])
export const assessmentListItemSchema = z.discriminatedUnion('status', [
  z.object({ assessment_id: z.string().min(1), status: z.literal('completed'), created_at: z.string(), model_version: z.string(), detection_count: z.number().int().nonnegative(), primary_detection_count: z.number().int().nonnegative(), secondary_detection_count: z.number().int().nonnegative() }),
  z.object({ assessment_id: z.string().min(1), status: z.literal('failed'), created_at: z.string(), error_code: errorCodeSchema }),
])
export const assessmentListResponseSchema = z.object({ items: z.array(assessmentListItemSchema), next_cursor: z.string().nullable() })
