import type { UnifiedAssessment } from '../../types/assessment'

export const INITIAL_ASSESSMENTS: UnifiedAssessment[] = [
  {
    assessment_id: 'BV-2026-8942',
    station_id: 'Yirgacheffe Station #04 (Gedeo)',
    lot_number: 'YIR-2026-088',
    moisture_level: '11.2%',
    varietal: 'Kurume & Dega (Washed)',
    status: 'completed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1',
    created_at: '2026-10-23T08:15:00Z',
    processing_time_ms: 1840,
    summary: {
      total_beans_estimated: 124,
      normal_beans_count: 102,
      defect_regions_count: 22,
      defect_percentage: 17.7,
    },
    predictions: [
      { class_name: 'Normal Green Bean', category_type: 'Healthy', confidence: 0.968, count: 102 },
      { class_name: 'Partial Black', category_type: 'Secondary Defect', confidence: 0.884, count: 12 },
      { class_name: 'Full Black', category_type: 'Primary Defect', confidence: 0.922, count: 5 },
      { class_name: 'Coffee Husk / Parchment', category_type: 'Secondary Defect', confidence: 0.748, count: 5 },
    ],
    detections: [
      {
        defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
        confidence: 0.922,
        box: { x1: 220, y1: 140, x2: 295, y2: 215 },
      },
      {
        defect: { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        confidence: 0.884,
        box: { x1: 440, y1: 260, x2: 510, y2: 320 },
      },
      {
        defect: { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
        confidence: 0.748,
        box: { x1: 680, y1: 180, x2: 750, y2: 245 },
      },
    ],
    coverage: {
      scanned: [
        { key: 'full_black', name: 'Full Black', category: 'primary' },
        { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
      ],
      not_scanned: [
        { key: 'full_sour', name: 'Full Sour / Stinker', category: 'primary' },
        { key: 'fungus_damaged', name: 'Fungus Damaged', category: 'primary' },
        { key: 'insect_damaged', name: 'Severe Insect Damaged', category: 'primary' },
      ],
    },
    limitations: [
      {
        code: 'PRELIMINARY_AI_ASSESSMENT',
        message: 'Preliminary AI screening of a photograph. This is not an official ECX or SCA grade.',
      },
      {
        code: 'PARTIAL_CLASS_COVERAGE',
        message: 'Only 3 of 13 ECX defect classes are scanned (Full Black, Partial Black, Coffee Husk / Parchment). Defects in other classes are not detected.',
      },
    ],
    advisory: {
      generator_model: 'gemini-2.0-flash',
      summary: {
        en: 'The green lot exhibits clean density and characteristic Yirgacheffe floral aroma potential. Secondary partial black bean tallies indicate uneven fermentation timing on washing channels.',
        am: 'ይህ የይርጋጨፌ አረንጓዴ ቡና ጥሩ ጥግግት እና የአበባ ሽታ አቅም ያሳያል። የተገኙት ከፊል ጥቁር ጉድለቶች በማጠቢያ ቦይ ላይ የመፍላት ጊዜ አለመመጣጠን እንደነበር ይጠቁማሉ።',
      },
      recommendations: [
        {
          en: 'Adjust channel washing wash-off duration by 4 hours during peak ambient temperatures.',
          am: 'ከፍተኛ ሙቀት በሚኖርበት ጊዜ የማጠቢያ ቦይ ቆይታን በ4 ሰዓታት ያስተካክሉ።',
        },
        {
          en: 'Perform manual sorting on African raised beds before moisture equilibrium bag seal.',
          am: 'ወደ ከረጢት ከመታሸጉ በፊት በአየር ማድረቂያ አልጋዎች ላይ በእጅ መምረጥ ያከናውኑ።',
        },
      ],
    },
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '/raw_beans_detected.png',
    notes: 'Grade 2 washed preparation. Raised African drying beds with shading canopy during midday sun.',
    is_live_backend: false,
  },
  {
    assessment_id: 'BV-2026-8810',
    station_id: 'Sidama Bensa Hub A (Daye Bensa)',
    lot_number: 'SID-2026-104',
    moisture_level: '10.8%',
    varietal: '74110 & 74112 Selected',
    status: 'completed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1',
    created_at: '2026-10-22T14:30:00Z',
    processing_time_ms: 1620,
    summary: {
      total_beans_estimated: 148,
      normal_beans_count: 135,
      defect_regions_count: 13,
      defect_percentage: 8.8,
    },
    predictions: [
      { class_name: 'Normal Green Bean', category_type: 'Healthy', confidence: 0.984, count: 135 },
      { class_name: 'Partial Black', category_type: 'Secondary Defect', confidence: 0.895, count: 9 },
      { class_name: 'Full Black', category_type: 'Primary Defect', confidence: 0.932, count: 4 },
    ],
    detections: [
      {
        defect: { key: 'full_black', name: 'Full Black', category: 'primary' },
        confidence: 0.932,
        box: { x1: 280, y1: 180, x2: 345, y2: 245 },
      },
    ],
    coverage: {
      scanned: [
        { key: 'full_black', name: 'Full Black', category: 'primary' },
        { key: 'partial_black', name: 'Partial Black', category: 'secondary' },
        { key: 'parchment_husk', name: 'Coffee Husk / Parchment', category: 'secondary' },
      ],
      not_scanned: [
        { key: 'full_sour', name: 'Full Sour / Stinker', category: 'primary' },
      ],
    },
    limitations: [
      {
        code: 'PRELIMINARY_AI_ASSESSMENT',
        message: 'Preliminary AI screening of a photograph. This is not an official ECX or SCA grade.',
      },
    ],
    advisory: {
      generator_model: 'gemini-2.0-flash',
      summary: {
        en: 'Outstanding visual uniformity from high-altitude Sidama Bensa micro-lot. Near-zero insect pinhole signs, with tight moisture range ideal for GrainPro export shipping.',
        am: 'በጣም ጥሩ ጥራት ያለው የሲዳማ ቤንሳ ማይክሮ-ሎት ናሙና። ወጥ የሆነ ገጽታ እና ለኤክስፖርት ምቹ የሆነ የእርጥበት መጠን አለው።',
      },
      recommendations: [
        {
          en: 'Preserve batch integrity under hermetic seal at 18-20°C ambient warehouse temperature.',
          am: 'በ18-20 ዲግሪ ሴልሺየስ የሙቀት መጠን ውስጥ በGrainPro ከረጢት ጥራቱን ጠብቀው ያከማቹ።',
        },
      ],
    },
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '/raw_beans_detected.png',
    notes: 'Natural process lot from 2,150 MASL. Exceptional fruit pulp cleanliness and drying uniformity.',
    is_live_backend: false,
  },
  {
    assessment_id: 'BV-2026-8701',
    station_id: 'Guji Hambela Field Terminal B',
    lot_number: 'GUJ-2026-004',
    moisture_level: '12.4%',
    varietal: 'Indigenous Guji Wild Forest',
    status: 'failed',
    model_version: 'YOLOv8n-Coffee-ONNX-v1',
    created_at: '2026-10-21T11:05:00Z',
    processing_time_ms: 810,
    summary: {
      total_beans_estimated: 0,
      normal_beans_count: 0,
      defect_regions_count: 0,
      defect_percentage: 0,
    },
    predictions: [],
    original_image_url: '/raw_beans_detected.png',
    annotated_image_url: '',
    notes: 'Image focus failed due to direct midday sunlight and severe lens glare. Sample needs retake.',
    error_code: 'INVALID_IMAGE',
    is_live_backend: false,
  },
]
