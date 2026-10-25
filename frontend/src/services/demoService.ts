import type { UnifiedAssessment } from '../types/assessment'
import type { UserOut } from '../types/auth'

export const DEMO_USER: UserOut = {
  user_id: 'usr_demo_producer_01',
  email: 'demo.producer@bunavision.et',
  role: 'user',
  created_at: '2026-10-20T10:00:00Z',
}

export const DEMO_ADMIN: UserOut = {
  user_id: 'usr_demo_admin_01',
  email: 'admin.inspector@bunavision.et',
  role: 'admin',
  created_at: '2026-10-18T08:30:00Z',
}

const DEMO_STORAGE_KEY = 'bv_demo_assessments_store'

export const INITIAL_DEMO_ASSESSMENTS: UnifiedAssessment[] = [
  {
    assessment_id: 'BV-DEMO-2026-001',
    station_id: 'Yirgacheffe Washing Station #04 (Gedeo)',
    lot_number: 'YIR-2026-LOT-088',
    moisture_level: '11.2%',
    varietal: 'Kurume & Dega (Washed Green)',
    status: 'completed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
    created_at: new Date(Date.now() - 3600 * 1000 * 3).toISOString(),
    processing_time_ms: 1240,
    summary: {
      detection_count: 4,
      primary_detection_count: 1,
      secondary_detection_count: 3,
      by_class: [
        {
          defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
          count: 1,
          mean_confidence: 0.942,
        },
        {
          defect: { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
          count: 2,
          mean_confidence: 0.887,
        },
        {
          defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
          count: 1,
          mean_confidence: 0.814,
        },
      ],
    },
    predictions: [
      { class_name: 'Full Black', category_type: 'Primary Defect', confidence: 0.942, count: 1 },
      { class_name: 'Partial Black', category_type: 'Secondary Defect', confidence: 0.887, count: 2 },
      { class_name: 'Coffee Husk / Parchment', category_type: 'Secondary Defect', confidence: 0.814, count: 1 },
    ],
    detections: [
      {
        defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
        confidence: 0.942,
        box: { x1: 210, y1: 180, x2: 295, y2: 265 },
      },
      {
        defect: { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        confidence: 0.912,
        box: { x1: 430, y1: 120, x2: 505, y2: 195 },
      },
      {
        defect: { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        confidence: 0.862,
        box: { x1: 520, y1: 310, x2: 600, y2: 390 },
      },
      {
        defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
        confidence: 0.814,
        box: { x1: 310, y1: 380, x2: 380, y2: 440 },
      },
    ],
    coverage: {
      scanned: [
        { key: 'full_black', name: 'Full Black', category: 'primary' },
        { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
      ],
      not_scanned: [
        { key: 'sour_bean', name: 'Sour / Fermented Bean', category: 'primary' },
        { key: 'insect_damage', name: 'Insect Damage / Borer Hole', category: 'secondary' },
        { key: 'immature_bean', name: 'Immature / Unripe Bean', category: 'secondary' },
      ],
    },
    limitations: [
      {
        code: 'LIMITED_TAXONOMY',
        message: 'This computer vision model version supports 3 visible defect classes only.',
      },
      {
        code: 'SURFACE_ONLY',
        message: 'Internal or chemical defects cannot be evaluated from a 2D photograph.',
      },
    ],
    advisory: {
      generator_model: 'gemini-1.5-flash-coffee-expert',
      summary: {
        en: 'Sample displays low primary defect occurrence with minimal black bean formation. Verify parchment removal before export bagging.',
        am: 'ናሙናው አነስተኛ የመጀመሪያ ደረጃ ጉድለት (Full Black) ያሳያል። ወደ ውጭ ከመላኩ በፊት የቡና ገለባ (parchment) በደንብ መወገዱን ያረጋግጡ።',
      },
      recommendations: [
        {
          en: 'Calibrate optical sorter sensitivity for partial black surface discoloration.',
          am: 'ከፊል ጥቁር የቡና ፍሬዎችን ለመለየት የኦፕቲካል መለያ ማሽን ንፅፅርን ያስተካክሉ።',
        },
        {
          en: 'Maintain moisture at current 11.2% range to preserve screen integrity.',
          am: 'የእርጥበት መጠኑ አሁን ባለው 11.2% እንዲቆይ ያድርጉ።',
        },
      ],
    },
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '/raw_beans_detected.png',
    notes: 'Interactive demo sample for Yirgacheffe washing station inspection.',
    is_live_backend: false,
  },
  {
    assessment_id: 'BV-DEMO-2026-002',
    station_id: 'Sidama Bensa Cooperative #12',
    lot_number: 'SID-2026-LOT-044',
    moisture_level: '10.8%',
    varietal: '74110 & 74112 (Natural Sun-dried)',
    status: 'completed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
    created_at: new Date(Date.now() - 3600 * 1000 * 24).toISOString(),
    processing_time_ms: 1110,
    summary: {
      detection_count: 6,
      primary_detection_count: 2,
      secondary_detection_count: 4,
      by_class: [
        {
          defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
          count: 2,
          mean_confidence: 0.956,
        },
        {
          defect: { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
          count: 3,
          mean_confidence: 0.871,
        },
        {
          defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
          count: 1,
          mean_confidence: 0.785,
        },
      ],
    },
    predictions: [
      { class_name: 'Full Black', category_type: 'Primary Defect', confidence: 0.956, count: 2 },
      { class_name: 'Partial Black', category_type: 'Secondary Defect', confidence: 0.871, count: 3 },
      { class_name: 'Coffee Husk / Parchment', category_type: 'Secondary Defect', confidence: 0.785, count: 1 },
    ],
    detections: [
      {
        defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
        confidence: 0.965,
        box: { x1: 180, y1: 150, x2: 260, y2: 230 },
      },
      {
        defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
        confidence: 0.947,
        box: { x1: 340, y1: 220, x2: 410, y2: 290 },
      },
    ],
    coverage: {
      scanned: [
        { key: 'full_black', name: 'Full Black', category: 'primary' },
        { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
      ],
      not_scanned: [],
    },
    limitations: [],
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '/raw_beans_detected.png',
    notes: 'Sidama natural lot demonstration report.',
    is_live_backend: false,
  },
  {
    assessment_id: 'BV-DEMO-2026-003',
    station_id: 'Guji Hambela Estate Dry Mill',
    lot_number: 'GUJ-2026-LOT-102',
    moisture_level: '11.5%',
    varietal: 'Indigenous Heirloom Varieties',
    status: 'completed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1.2',
    created_at: new Date(Date.now() - 3600 * 1000 * 48).toISOString(),
    processing_time_ms: 980,
    summary: {
      detection_count: 1,
      primary_detection_count: 0,
      secondary_detection_count: 1,
      by_class: [
        {
          defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
          count: 1,
          mean_confidence: 0.892,
        },
      ],
    },
    predictions: [
      { class_name: 'Coffee Husk / Parchment', category_type: 'Secondary Defect', confidence: 0.892, count: 1 },
    ],
    detections: [
      {
        defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
        confidence: 0.892,
        box: { x1: 290, y1: 200, x2: 360, y2: 270 },
      },
    ],
    coverage: {
      scanned: [
        { key: 'full_black', name: 'Full Black', category: 'primary' },
        { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
      ],
      not_scanned: [],
    },
    limitations: [],
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '/raw_beans_detected.png',
    notes: 'Specialty grade sample with zero primary defects.',
    is_live_backend: false,
  },
]

/**
 * Checks if demo data is currently stored in localStorage
 */
export function hasDemoData(): boolean {
  return localStorage.getItem(DEMO_STORAGE_KEY) !== null
}

/**
 * Retrieves all stored demo assessments (or initializes if empty)
 */
export function getDemoAssessments(): UnifiedAssessment[] {
  const raw = localStorage.getItem(DEMO_STORAGE_KEY)
  if (!raw) return []
  try {
    return JSON.parse(raw) as UnifiedAssessment[]
  } catch {
    return []
  }
}

/**
 * Retrieves a single demo assessment by ID
 */
export function getDemoAssessmentById(id: string): UnifiedAssessment | null {
  const items = getDemoAssessments()
  return items.find((item) => item.assessment_id === id) || null
}

/**
 * Seeds demo assessment data into localStorage
 */
export function loadDemoData(): void {
  localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(INITIAL_DEMO_ASSESSMENTS))
  window.dispatchEvent(new CustomEvent('bv_demo_data_changed', { detail: { count: INITIAL_DEMO_ASSESSMENTS.length } }))
}

/**
 * Completely purges all demo data from localStorage (easily deletable)
 */
export function deleteDemoData(): void {
  localStorage.removeItem(DEMO_STORAGE_KEY)
  window.dispatchEvent(new CustomEvent('bv_demo_data_changed', { detail: { count: 0 } }))
}
