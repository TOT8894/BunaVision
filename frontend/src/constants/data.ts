import type { PresetSample } from '../types/app'
import { Camera, Scan, FileText } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

// ─── Preset Samples ──────────────────────────────────────────────────────────

export const PRESET_SAMPLES: PresetSample[] = [
  {
    id: 'preset-1',
    name: 'Raw Green Beans Inspection (Yirgacheffe)',
    station: 'Yirgacheffe Station #04',
    lot: 'YIR-2026-088',
    moisture: '11.2%',
    url: '/raw_beans_detected.png',
  },
  {
    id: 'preset-2',
    name: 'Sun-Drying Canvas Bed (Sidama Bensa)',
    station: 'Sidama Bensa Hub A',
    lot: 'SID-2026-104',
    moisture: '10.8%',
    url: '/coffee_drying_bed_overhead.jpg',
  },
  {
    id: 'preset-3',
    name: 'Direct Sun-Drying Bed (Guji Hambela)',
    station: 'Guji Field Terminal 02',
    lot: 'GUJ-2026-012',
    moisture: '11.5%',
    url: '/coffee_drying_closeup.jpg',
  },
  {
    id: 'preset-4',
    name: 'Highland Station Drying Lot (Jimma)',
    station: 'Jimma Agaro Washing Station',
    lot: 'JIM-2026-045',
    moisture: '11.1%',
    url: '/coffee_station_landscape.jpg',
  },
]

// ─── Ethiopian Origins ───────────────────────────────────────────────────────

export interface EthiopianOrigin {
  name: string
  defaultVarietal: string
  alt: string
  soil: string
}

export const ETHIOPIAN_ORIGINS: EthiopianOrigin[] = [
  {
    name: 'Yirgacheffe (Gedeo)',
    defaultVarietal: 'Kurume & Dega',
    alt: '1,950 - 2,200m',
    soil: 'Red-brown fertile loam',
  },
  {
    name: 'Sidama (Bensa)',
    defaultVarietal: '74110 / 74112',
    alt: '2,000 - 2,250m',
    soil: 'Volcanic rich humus',
  },
  {
    name: 'Guji (Hambela)',
    defaultVarietal: 'Indigenous Forest',
    alt: '1,900 - 2,150m',
    soil: 'Iron-rich clay loam',
  },
  {
    name: 'Jimma (Agaro)',
    defaultVarietal: '74110 Selected',
    alt: '1,800 - 2,050m',
    soil: 'Forest canopy loam',
  },
  {
    name: 'Harar (Highlands)',
    defaultVarietal: 'Longberry & Mocha',
    alt: '1,750 - 1,950m',
    soil: 'Sun-drenched limestone',
  },
]

// ─── Defect Info Cards ───────────────────────────────────────────────────────

export interface DefectInfoCard {
  key: string
  title: string
  category: string
  color: string
  description: string
  tasteImpact: string
  prevention: string
}

export const DEFECT_INFO_CARDS: DefectInfoCard[] = [
  {
    key: 'full_black',
    title: 'Full Black (ጥቁር ፍሬ)',
    category: 'ECX Primary Defect',
    color: 'bg-red-500',
    description:
      'Immature or insect-punctured raw green cherries fermented excessively before or during harvesting.',
    tasteImpact: 'Harsh, pungent, astringent, medicinal or vinegary cup defect.',
    prevention:
      'Select only ripe cherries; prevent floor harvesting and rain delay on drying beds.',
  },
  {
    key: 'partial_black',
    title: 'Partial Black (ከፊል ጥቁር)',
    category: 'ECX Secondary Defect',
    color: 'bg-amber-500',
    description:
      'Uneven moisture loss or localized fermentation during channel washing or early drying of raw green beans.',
    tasteImpact: 'Dull body, cardboard or woody aftertaste.',
    prevention: 'Turn beans 4-5 times daily on African beds to ensure uniform drying.',
  },
  {
    key: 'parchment_husk',
    title: 'Husk / Parchment (የቆዳ ቅሪት)',
    category: 'ECX Secondary Defect',
    color: 'bg-amber-400',
    description:
      'Dry cherry pulp or endocarp shell retained due to tight huller clearance on unroasted raw beans.',
    tasteImpact: 'Astringency and uneven roaster heat transfer.',
    prevention: 'Adjust huller knife gap to match calibrated bean size sieve screens.',
  },
]

// ─── How It Works Steps ──────────────────────────────────────────────────────

export interface HowItWorksStep {
  step: string
  icon: LucideIcon
  title: string
  amharic: string
  description: string
  detail: string
}

export const HOW_IT_WORKS: HowItWorksStep[] = [
  {
    step: '01',
    icon: Camera,
    title: 'Capture & Upload',
    amharic: 'ፎቶ አንሱ',
    description:
      'Spread green beans in a flat single layer on a plain contrasting surface. Capture a sharp photograph using a smartphone or desk camera.',
    detail: 'Supports JPEG & PNG up to 15MB',
  },
  {
    step: '02',
    icon: Scan,
    title: 'AI Vision Analysis',
    amharic: 'ሰው ሰራሽ ምርምር',
    description:
      'Our YOLOv10 computer vision model segments raw bean boundaries and isolates visible surface defects including broken, sour, and insect damage.',
    detail: '3 of 13 ECX defect classes covered · ~2 second inference',
  },
  {
    step: '03',
    icon: FileText,
    title: 'Review & Verify',
    amharic: 'ሁለት ቋንቋ ሪፖርት',
    description:
      'Examine bean counts, defect ratios, and model confidence scores. Low-confidence predictions (<80%) are automatically flagged for Q-grader review.',
    detail: 'Decision-support only — not an official grade',
  },
]
