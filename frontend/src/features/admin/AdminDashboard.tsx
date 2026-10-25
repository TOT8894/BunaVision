import { useState } from 'react'
import { Link } from 'react-router'
import {
  Upload,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Server,
  Cpu,
  Database,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

interface OverrideItem {
  id: string
  assessmentId: string
  defectType: string
  graderId: string
  timeAgo: string
  decision: 'verified' | 'overrode'
  notes?: string
}

const INITIAL_OVERRIDES: OverrideItem[] = [
  {
    id: 'ov-1',
    assessmentId: 'BV-2026-8942',
    defectType: 'Faded / Immature',
    graderId: 'Q-Grader #884',
    timeAgo: '2 mins ago',
    decision: 'verified',
    notes: 'Confirmed pale bleached coloration under daylight illumination.',
  },
  {
    id: 'ov-2',
    assessmentId: 'BV-2026-8802',
    defectType: 'Sour / Black Discolored',
    graderId: 'Q-Grader #102',
    timeAgo: '1 hour ago',
    decision: 'overrode',
    notes: 'False positive caused by shadow at tray periphery; bean is sound.',
  },
  {
    id: 'ov-3',
    assessmentId: 'BV-2026-8791',
    defectType: 'Insect-Damaged',
    graderId: 'Q-Grader #312',
    timeAgo: '4 hours ago',
    decision: 'verified',
    notes: 'Small borer bore hole confirmed on ventral crease.',
  },
  {
    id: 'ov-4',
    assessmentId: 'BV-2026-8650',
    defectType: 'Coffee Husk / Parchment',
    graderId: 'Q-Grader #419',
    timeAgo: '7 hours ago',
    decision: 'verified',
    notes: 'Partial dried parchment flap adhering to dorsal side.',
  },
]

export function AdminDashboard() {
  const { theme } = useTheme()
  const [filter, setFilter] = useState<'all' | 'verified' | 'overrode'>('all')
  const [isRefreshing, setIsRefreshing] = useState(false)

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-md shadow-black/20'
      : 'bg-white border-[#E8E0D5] shadow-xs'
  }`

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 600)
  }

  const filteredOverrides = INITIAL_OVERRIDES.filter((item) => {
    if (filter === 'all') return true
    return item.decision === filter
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
            Admin Telemetry Dashboard
          </h1>
          <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB] mt-1.5">
            System health, inference latency, and Q-grader override feedback logs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleRefresh}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold border flex items-center gap-1.5 transition-colors cursor-pointer ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26] text-[#C8C2BB] hover:bg-[#2C2723]'
                : 'bg-white border-[#DDD5C8] text-[#5A544C] hover:bg-[#FAF8F5]'
            }`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Stats</span>
          </button>

          <Link
            to="/assess"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-all no-underline"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Assess a Sample</span>
          </Link>
        </div>
      </div>

      {/* ── 4 Top Stat Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Analyzed Batches */}
        <div className={`p-6 ${card}`}>
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Total Analyzed Batches
          </div>
          <div className="text-4xl font-bold font-serif text-[#24211D] dark:text-[#F9F7F2] mt-3">
            1,428
          </div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#4F7335] dark:text-[#8BA470] mt-2">
            <span>+14% this month</span>
          </div>
        </div>

        {/* Avg Inference Time */}
        <div className={`p-6 ${card}`}>
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Avg Inference Time
          </div>
          <div className="text-4xl font-bold font-serif text-[#24211D] dark:text-[#F9F7F2] mt-3">
            1.42s
          </div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#4F7335] dark:text-[#8BA470] mt-2">
            <span>GPU Accelerated (YOLOv10)</span>
          </div>
        </div>

        {/* Active Washing Stations */}
        <div className={`p-6 ${card}`}>
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Active Washing Stations
          </div>
          <div className="text-4xl font-bold font-serif text-[#24211D] dark:text-[#F9F7F2] mt-3">
            18
          </div>
          <div className="text-xs font-medium text-[#7B7569] dark:text-[#A8A193] mt-2">
            Field Terminals Connected
          </div>
        </div>

        {/* Model Version */}
        <div className={`p-6 ${card}`}>
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
            Model Version
          </div>
          <div className="text-3xl font-bold font-serif text-[#593D2B] dark:text-[#C4A882] mt-3">
            CoffeeNet v2.4
          </div>
          <div className="text-xs font-medium text-[#7B7569] dark:text-[#A8A193] mt-2">
            Retrained 4 days ago
          </div>
        </div>
      </div>

      {/* ── Q-Grader Override Feedback Loop ── */}
      <div className={`p-6 sm:p-8 ${card} space-y-6`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E8E0D5] dark:border-[#382E26]">
          <div>
            <h2 className="text-xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Q-Grader Override Feedback Loop
            </h2>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
              Recent manual verification decisions submitted by Q-graders on low-confidence predictions.
            </p>
          </div>

          <div className="flex items-center gap-1.5 bg-[#FAF8F5] dark:bg-[#181513] p-1 rounded-xl border border-[#E8E0D5] dark:border-[#382E26]">
            {(['all', 'verified', 'overrode'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setFilter(mode)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                  filter === mode
                    ? 'bg-[#593D2B] text-white shadow-xs'
                    : 'text-[#7B7569] dark:text-[#A8A193] hover:text-[#24211D] dark:hover:text-[#F9F7F2]'
                }`}
              >
                {mode === 'all' ? 'All Logs' : mode === 'verified' ? 'Verified' : 'Overridden'}
              </button>
            ))}
          </div>
        </div>

        {/* Override List */}
        <div className="space-y-3.5">
          {filteredOverrides.map((item) => (
            <div
              key={item.id}
              className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors ${
                theme === 'dark'
                  ? 'bg-[#1D1916] border-[#382E26] hover:border-[#8BA470]/40'
                  : 'bg-[#FCFBF9] border-[#E8E0D5] hover:border-[#DDD5C8]'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Link
                    to={`/assessments/${item.assessmentId}`}
                    className="font-bold text-sm text-[#3B2416] dark:text-[#F9F7F2] hover:text-[#593D2B] dark:hover:text-[#C4A882] transition-colors"
                  >
                    {item.assessmentId}
                  </Link>
                  <span className="text-[#8BA470]">•</span>
                  <span className="text-sm font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                    {item.defectType}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-[#7B7569] dark:text-[#A8A193]">
                  <span>By {item.graderId}</span>
                  <span>•</span>
                  <span>{item.timeAgo}</span>
                  {item.notes && (
                    <>
                      <span className="hidden md:inline">•</span>
                      <span className="hidden md:inline italic text-[#5A544C] dark:text-[#A8A193]/80">
                        "{item.notes}"
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-2">
                {item.decision === 'verified' ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-[#8BA470]/15 text-[#3A5228] dark:text-[#B5CF97] border border-[#8BA470]/30">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Verified Defect
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Overrode to Normal
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── System Subsystems Status ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className={`p-5 ${card} flex items-center gap-4`}>
          <div className="w-11 h-11 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97] shrink-0">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
              FastAPI Gateway
            </div>
            <div className="text-sm font-bold text-[#24211D] dark:text-[#F9F7F2] mt-0.5">
              Healthy · 99.98% Uptime
            </div>
            <div className="text-[11px] text-[#4F7335] dark:text-[#8BA470] mt-0.5">
              Running on AWS ECS Fargate
            </div>
          </div>
        </div>

        <div className={`p-5 ${card} flex items-center gap-4`}>
          <div className="w-11 h-11 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97] shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
              Vision Inference Pod
            </div>
            <div className="text-sm font-bold text-[#24211D] dark:text-[#F9F7F2] mt-0.5">
              Active · 3 Classes Supported
            </div>
            <div className="text-[11px] text-[#4F7335] dark:text-[#8BA470] mt-0.5">
              Full Black, Partial, Husk
            </div>
          </div>
        </div>

        <div className={`p-5 ${card} flex items-center gap-4`}>
          <div className="w-11 h-11 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97] shrink-0">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#7B7569] dark:text-[#A8A193]">
              S3 Storage & PostgreSQL
            </div>
            <div className="text-sm font-bold text-[#24211D] dark:text-[#F9F7F2] mt-0.5">
              Connected & Encrypted
            </div>
            <div className="text-[11px] text-[#4F7335] dark:text-[#8BA470] mt-0.5">
              Audit log integrity verified
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
