import { Link } from 'react-router'
import {
  Upload,
  Sparkles,
  UserPlus,
  Scan,
  Globe2,
  Zap,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { HOW_IT_WORKS } from '../../constants/data'

export function HomePage() {
  const { theme } = useTheme()
  const { authToken } = useAuth()

  return (
    <div>
      {/* ═══════════════════ HERO ═══════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-14 items-center">
          {/* Left: copy */}
          <div className="space-y-8">
            {/* Eyebrow tag */}
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border
              border-[#8BA470]/40 bg-[#8BA470]/10
              text-[#3A5228] dark:text-[#B5CF97]
              text-xs font-bold uppercase tracking-wider"
            >
              <Zap className="w-3.5 h-3.5 shrink-0" />
              <span>AI-Assisted Green Bean Analysis</span>
            </div>

            {/* Headline */}
            <div className="space-y-4">
              <h1
                className="text-4xl sm:text-5xl font-bold font-serif leading-tight
                text-[#3B2416] dark:text-[#F9F7F2]"
              >
                See coffee quality{' '}
                <span className="text-[#593D2B] dark:text-[#C4A882]">more clearly.</span>
              </h1>
              <p className="text-base leading-relaxed text-[#4A4540] dark:text-[#C8C2BB] max-w-lg">
                BunaVision brings computer vision intelligence to raw green coffee bean sorting.
                Rapidly detect and count visible surface defects before roasting—improving
                transparency across washing stations and grading labs.
              </p>
            </div>

            {/* Disclaimer strip */}
            <div
              className="flex items-start gap-2 px-4 py-3 rounded-xl
              bg-amber-50 dark:bg-amber-950/30
              border border-amber-300 dark:border-amber-800/50"
            >
              <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-amber-700 dark:text-amber-400" />
              <p className="text-xs font-medium text-amber-900 dark:text-amber-300 leading-relaxed">
                Decision-support tool only. Not an official ECX grade or certified evaluation.
              </p>
            </div>

            {/* CTA buttons */}
            <div className="flex flex-wrap gap-3">
              {authToken ? (
                <Link
                  to="/assess"
                  className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl
                    bg-[#593D2B] hover:bg-[#483020] active:bg-[#3A2519]
                    text-white font-semibold text-sm shadow-md
                    hover:scale-[1.02] transition-all no-underline"
                >
                  <Upload className="w-4 h-4" />
                  Assess a Sample →
                </Link>
              ) : (
                <>
                  <Link
                    to="/assess"
                    className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl
                      bg-[#593D2B] hover:bg-[#483020] active:bg-[#3A2519]
                      text-white font-semibold text-sm shadow-md
                      hover:scale-[1.02] transition-all no-underline"
                  >
                    <Sparkles className="w-4 h-4 text-[#A7BF8C]" />
                    Assess a Sample →
                  </Link>
                  <a
                    href="#how-it-works"
                    className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl
                      border-2 border-[#593D2B] dark:border-[#8BA470]
                      text-[#593D2B] dark:text-[#A7BF8C]
                      font-semibold text-sm
                      hover:bg-[#593D2B]/5 dark:hover:bg-[#8BA470]/10
                      transition-all no-underline"
                  >
                    View How It Works
                  </a>
                </>
              )}
            </div>

            {/* Feature pills */}
            <div className="flex flex-wrap gap-2">
              {[
                { label: '3 ECX Defect Classes', icon: Scan },
                { label: 'Bilingual EN / አማርኛ', icon: Globe2 },
                { label: 'Gemini AI Advisory', icon: Sparkles },
                { label: '~2s Inference', icon: Zap },
              ].map(({ label, icon: Icon }) => (
                <span
                  key={label}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${
                    theme === 'dark'
                      ? 'border-[#382E26] text-[#C8C2BB] bg-[#231F1C]'
                      : 'border-[#D5CCB8] text-[#4A4540] bg-white'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Right: annotated image */}
          <div className="relative pb-6">
            <div
              className={`rounded-3xl overflow-hidden border shadow-2xl ${
                theme === 'dark' ? 'border-[#382E26]' : 'border-[#D5CCB8]'
              }`}
            >
              <div className="relative aspect-square bg-stone-950">
                <img
                  src="/raw_beans_detected.png"
                  alt="Raw green coffee beans with AI defect detection overlays"
                  className="w-full h-full object-cover"
                />
                {/* Detection overlays */}
                <div className="absolute top-[20%] left-[22%] flex flex-col items-center pointer-events-none">
                  <div className="w-14 h-14 rounded-full bg-red-500/30 border-2 border-red-400" />
                  <span className="-mt-3 bg-red-600 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow-lg">
                    Full Black 93%
                  </span>
                </div>
                <div className="absolute top-[50%] right-[24%] flex flex-col items-center pointer-events-none">
                  <div className="w-12 h-12 rounded-full bg-amber-500/30 border-2 border-amber-400" />
                  <span className="-mt-3 bg-amber-600 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow-lg">
                    Partial Black 91%
                  </span>
                </div>
                <div className="absolute bottom-[30%] left-[28%] flex flex-col items-center pointer-events-none">
                  <div className="w-11 h-11 rounded-full bg-amber-400/30 border-2 border-amber-300" />
                  <span className="-mt-3 bg-amber-500 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow-lg">
                    Husk 88%
                  </span>
                </div>
                <div className="absolute bottom-3 left-3 right-3 bg-[#593D2B]/90 backdrop-blur text-white text-[11px] px-3 py-2 rounded-lg font-mono">
                  <div className="font-bold text-[#A7BF8C]">Sample #BV-2026-8942</div>
                  <div className="text-stone-300">
                    Total Beans: 120 | Defect Ratio: 18.3%
                  </div>
                </div>
                <div className="absolute bottom-3 right-3 bg-[#593D2B] text-white text-[10px] px-2.5 py-1 rounded-md font-bold">
                  YOLOv10 Active
                </div>
              </div>
            </div>

            {/* Floating model chip */}
            <div
              className={`absolute -bottom-2 -left-2 flex items-center gap-2
              px-4 py-2.5 rounded-2xl border shadow-lg text-xs ${
                theme === 'dark'
                  ? 'bg-[#231F1C] border-[#382E26]'
                  : 'bg-white border-[#D5CCB8]'
              }`}
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-[#4A4540] dark:text-[#C8C2BB]">Model:</span>
              <span className="font-mono font-bold text-[#593D2B] dark:text-[#A7BF8C]">
                YOLOv8n-Coffee-ONNX-v1
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ HOW IT WORKS ═══════════════════ */}
      <section
        id="how-it-works"
        className={`py-20 border-t ${
          theme === 'dark'
            ? 'bg-[#1A1714] border-[#2E2822]'
            : 'bg-[#F0EBE3] border-[#DDD5C8]'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Section header */}
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Three-Step Inspection Workflow
            </h2>
            <p className="text-sm leading-relaxed text-[#4A4540] dark:text-[#C8C2BB]">
              Simple, repeatable process designed for field terminals and washing station
              laboratories.
            </p>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {HOW_IT_WORKS.map((step, idx) => {
              const Icon = step.icon
              return (
                <div key={step.step} className="relative">
                  {/* Connector arrow */}
                  {idx < HOW_IT_WORKS.length - 1 && (
                    <ArrowRight
                      className="hidden md:block absolute -right-3 top-8 w-6 h-6
                      text-[#8BA470]/50 dark:text-[#8BA470]/30 z-10"
                    />
                  )}

                  <div
                    className={`h-full p-6 rounded-2xl border space-y-4 ${
                      theme === 'dark'
                        ? 'bg-[#231F1C] border-[#382E26]'
                        : 'bg-white border-[#DDD5C8] shadow-sm'
                    }`}
                  >
                    {/* Step number + icon row */}
                    <div className="flex items-center justify-between">
                      <div
                        className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          theme === 'dark'
                            ? 'bg-[#593D2B]/30 text-[#C4A882]'
                            : 'bg-[#593D2B]/10 text-[#593D2B]'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <span
                        className="font-serif font-black text-4xl
                        text-[#8BA470]/25 dark:text-[#8BA470]/20 select-none"
                      >
                        {step.step}
                      </span>
                    </div>

                    {/* Title */}
                    <div className="space-y-1">
                      <h3 className="font-bold text-base font-serif text-[#3B2416] dark:text-[#F9F7F2]">
                        {step.title}
                      </h3>
                    </div>

                    {/* Description */}
                    <p className="text-sm leading-relaxed text-[#4A4540] dark:text-[#C8C2BB]">
                      {step.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Bottom CTA */}
          <div className="text-center pt-4">
            {authToken ? (
              <Link
                to="/assess"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl
                  bg-[#593D2B] hover:bg-[#483020] text-white font-semibold
                  shadow-md hover:scale-[1.02] transition-all no-underline"
              >
                <Upload className="w-4 h-4" />
                Go to Assessment
              </Link>
            ) : (
              <div className="space-y-3">
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 px-8 py-4 rounded-xl
                    bg-[#593D2B] hover:bg-[#483020] text-white font-semibold
                    shadow-md hover:scale-[1.02] transition-all no-underline"
                >
                  <UserPlus className="w-4 h-4" />
                  Create Free Account to Start
                </Link>
                <p className="text-sm text-[#5A544C] dark:text-[#A8A193]">
                  Already have an account?{' '}
                  <Link
                    to="/login"
                    className="font-semibold text-[#593D2B] dark:text-[#A7BF8C] hover:underline"
                  >
                    Sign in
                  </Link>
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ═══════════════════ PHOTOGRAPHY GUIDANCE + AI NOTICE ═══════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Photography Guidance */}
          <div
            className={`p-6 rounded-2xl border ${
              theme === 'dark'
                ? 'bg-[#231F1C] border-[#382E26]'
                : 'bg-white border-[#DDD5C8] shadow-sm'
            }`}
          >
            <h3 className="font-bold text-lg font-serif text-[#3B2416] dark:text-[#F9F7F2] mb-4">
              📷 Photography Guidance Summary
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {[
                'Single-layer bean layout (no bean stacking)',
                'Matte contrasting neutral background',
                'Bright, indirect, shadow-free lighting',
                'Sharp focus across the complete sample frame',
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-2 text-[#4A4540] dark:text-[#C8C2BB]"
                >
                  <span className="text-[#8BA470] font-bold mt-0.5">☑</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Preliminary AI Notice */}
          <div className="p-6 rounded-2xl border border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/20">
            <h3 className="font-bold text-lg font-serif text-red-800 dark:text-red-300 mb-3">
              ⚠ Preliminary AI Notice
            </h3>
            <p className="text-xs leading-relaxed text-red-900 dark:text-red-300">
              BunaVision provides preliminary visual surface defect region estimations only. It
              does not issue official specialty coffee cup scores, sensory grading certifications,
              or internal bean density checks. Human verification by a certified Q-grader is
              required for official batch export documentation.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
