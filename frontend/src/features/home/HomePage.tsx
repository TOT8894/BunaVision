import { Link } from 'react-router'
import {
  Upload,
  Sparkles,
  Scan,
  Globe2,
  Zap,
  ShieldCheck,
  ArrowRight,
  Camera,
  Info,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { HOW_IT_WORKS } from '../../constants/data'

export function HomePage() {
  const { theme } = useTheme()
  const { authToken } = useAuth()

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-sm'
      : 'bg-white border-[#E2D9CF] shadow-xs'
  }`

  return (
    <div>
      {/* ═══════════════════ HERO ═══════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: copy */}
          <div className="space-y-7 animate-fade-in-up">
            {/* Eyebrow tag */}
            <div
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border
              border-[#8BA470]/60 bg-[#8BA470]/15
              text-[#2B3F1D] dark:text-[#A7BF8C]
              text-xs font-bold uppercase tracking-wider shadow-2xs"
            >
              <Zap className="w-3.5 h-3.5 shrink-0 text-[#3A5228] dark:text-[#8BA470]" />
              <span>AI-Assisted Green Coffee Bean Screening</span>
            </div>

            {/* Headline */}
            <div className="space-y-3.5 animate-fade-in-up-delay-1">
              <h1
                className="text-4xl sm:text-5xl font-bold font-serif leading-tight
                text-[#1C1917] dark:text-[#F9F7F2]"
              >
                See coffee quality{' '}
                <span className="text-[#593D2B] dark:text-[#C4A882]">more clearly.</span>
              </h1>
              <p className="text-base leading-relaxed text-[#292524] dark:text-[#D6D3D1] max-w-xl font-medium">
                BunaVision brings computer vision intelligence to pre-roast green coffee bean
                inspection. Rapidly detect and segment visible surface defect regions
                (Full Black, Partial Black, and Coffee Husk) before roasting.
              </p>
            </div>

            {/* Disclaimer pill */}
            <div
              className="flex items-start gap-2.5 px-4 py-3 rounded-xl
              bg-amber-100/70 dark:bg-amber-950/30
              border border-amber-300 dark:border-amber-800/50"
            >
              <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-amber-900 dark:text-amber-400" />
              <p className="text-xs font-bold text-amber-950 dark:text-amber-200 leading-relaxed">
                Decision-support screening only. Does not issue official ECX grade certificates or cup scores.
              </p>
            </div>

            {/* CTA buttons */}
            <div className="flex flex-wrap items-center gap-3.5 pt-1 animate-fade-in-up-delay-2">
              <Link
                to={authToken ? '/assess' : '/login'}
                state={!authToken ? { from: '/assess' } : undefined}
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl
                  bg-[#593D2B] hover:bg-[#483020] active:bg-[#382416]
                  text-white font-bold text-sm shadow-md hover:shadow-lg hover:-translate-y-0.5
                  transition-all duration-200 no-underline cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>Assess a Sample →</span>
              </Link>

              <a
                href="#how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl
                  border-2 border-[#593D2B] dark:border-[#8BA470]
                  text-[#593D2B] dark:text-[#A7BF8C]
                  font-bold text-sm
                  hover:bg-[#593D2B]/10 dark:hover:bg-[#8BA470]/15 hover:-translate-y-0.5
                  transition-all duration-200 no-underline cursor-pointer"
              >
                <span>How It Works</span>
              </a>
            </div>

            {/* Capability highlights */}
            <div className="flex flex-wrap gap-2 pt-2 animate-fade-in-up-delay-3">
              {[
                { label: '3 ECX Defect Classes', icon: Scan },
                { label: 'Bilingual EN / አማርኛ', icon: Globe2 },
                { label: 'Instance Segmentation', icon: Sparkles },
                { label: 'Sub-second Latency', icon: Zap },
              ].map(({ label, icon: Icon }) => (
                <span
                  key={label}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border transition-transform hover:scale-105 ${
                    theme === 'dark'
                      ? 'border-[#382E26] text-[#D6D3D1] bg-[#231F1C]'
                      : 'border-[#D6CEBF] text-[#1C1917] bg-white shadow-2xs'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 text-[#593D2B] dark:text-[#8BA470]" />
                  <span>{label}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Right: annotated image with soft float and laser scan effect */}
          <div className="relative animate-soft-float">
            <div
              className={`rounded-3xl overflow-hidden border shadow-xl transition-all duration-500 hover:shadow-2xl ${
                theme === 'dark' ? 'border-[#382E26]' : 'border-[#D6CEBF]'
              }`}
            >
              <div className="relative aspect-4/3 bg-stone-950 overflow-hidden">
                <img
                  src="/raw_beans_detected.png"
                  alt="Raw green coffee beans inspection sample"
                  className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
                />

                {/* Animated scanline */}
                <div className="absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-[#8BA470] to-transparent animate-scan-line pointer-events-none shadow-[0_0_12px_#8BA470]" />

                {/* Subtle overlay info bar */}
                <div className="absolute bottom-3 left-3 right-3 bg-[#1C1917]/90 backdrop-blur-md text-white text-xs px-3.5 py-2.5 rounded-xl flex items-center justify-between border border-white/10 shadow-lg">
                  <div className="space-y-0.5">
                    <div className="font-bold text-[#A7BF8C]">
                      Optical Defect Localization
                    </div>
                    <div className="text-stone-300">
                      Instance segmentation on flat spread tray
                    </div>
                  </div>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                    YOLO Active
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════ HOW IT WORKS ═══════════════════ */}
      <section
        id="how-it-works"
        className={`py-20 border-t ${
          theme === 'dark' ? 'border-[#382E26] bg-[#1d1a17]' : 'border-[#E2D9CF] bg-white'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Section header */}
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
              Three-Step Inspection Workflow
            </h2>
            <p className="text-sm font-medium leading-relaxed text-[#44403C] dark:text-[#D6D3D1]">
              Simple, repeatable protocol designed for washing stations, cooperative quality labs, and export terminals.
            </p>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {HOW_IT_WORKS.map((step, idx) => {
              const Icon = step.icon
              return (
                <div key={step.step} className="relative">
                  {idx < HOW_IT_WORKS.length - 1 && (
                    <ArrowRight
                      className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 w-6 h-6
                      text-[#8BA470]/60 dark:text-[#8BA470]/40 z-10"
                    />
                  )}

                  <div
                    className={`h-full p-6 sm:p-7 rounded-2xl border space-y-4 ${card}`}
                  >
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
                      <span className="font-serif font-black text-4xl text-[#8BA470]/30 select-none">
                        {step.step}
                      </span>
                    </div>

                    <div className="space-y-1.5">
                      <h3 className="font-bold text-base font-serif text-[#382416] dark:text-[#F9F7F2]">
                        {step.title}
                      </h3>
                      <p className="text-xs font-semibold text-[#8BA470] dark:text-[#A7BF8C]">
                        {step.amharic}
                      </p>
                    </div>

                    <p className="text-xs font-medium leading-relaxed text-[#44403C] dark:text-[#D6D3D1]">
                      {step.description}
                    </p>

                    <div className="pt-2 text-xs font-bold text-[#593D2B] dark:text-[#A7BF8C] border-t border-[#E2D9CF] dark:border-[#382E26]">
                      {step.detail}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Bottom CTA */}
          <div className="text-center pt-4">
            <Link
              to={authToken ? '/assess' : '/login'}
              state={!authToken ? { from: '/assess' } : undefined}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl
                bg-[#593D2B] hover:bg-[#483020] text-white font-bold text-sm
                shadow-xs transition-all no-underline"
            >
              <Upload className="w-4 h-4" />
              <span>{authToken ? 'Start New Assessment' : 'Sign In to Assess'}</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ═══════════════════ GUIDANCE & NOTICE ═══════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Photography Guidance */}
          <div className={`p-6 sm:p-7 ${card}`}>
            <div className="flex items-center space-x-2 mb-4">
              <Camera className="w-5 h-5 text-[#593D2B] dark:text-[#8BA470]" />
              <h3 className="font-bold text-base font-serif text-[#382416] dark:text-[#F9F7F2]">
                Photography Guidance Summary
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-medium">
              {[
                'Single-layer bean layout (no stacking or overlapping)',
                'Matte contrasting neutral background tray',
                'Bright, indirect, shadow-free lighting',
                'Sharp focus across the entire sample frame',
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-2 text-[#44403C] dark:text-[#D6D3D1]"
                >
                  <span className="text-[#3A5228] dark:text-[#8BA470] font-bold mt-0.5">☑</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Preliminary AI Notice */}
          <div className="p-6 sm:p-7 rounded-2xl border border-amber-300 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20">
            <div className="flex items-center space-x-2 mb-3">
              <Info className="w-5 h-5 text-amber-800 dark:text-amber-400" />
              <h3 className="font-bold text-base font-serif text-amber-950 dark:text-amber-200">
                Preliminary Screening Notice
              </h3>
            </div>
            <p className="text-xs font-medium leading-relaxed text-amber-900 dark:text-amber-300">
              BunaVision provides automated optical surface defect region counting for green coffee
              bean samples prior to roasting. It does not issue official specialty coffee cup scores,
              sensory certificates, or internal density evaluations. Human verification by a certified
              Q-grader is required for official batch export documentation.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
