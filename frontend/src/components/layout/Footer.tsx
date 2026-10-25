import { Info } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

export function Footer() {
  const { theme } = useTheme()

  return (
    <footer
      className={`border-t py-8 transition-colors ${
        theme === 'dark'
          ? 'bg-[#181513] border-[#382E26]'
          : 'bg-[#FAF8F5] border-[#E8E0D5]'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-[#5A544C] space-y-3 sm:space-y-0">
          <div className="flex items-center space-x-2">
            <span className="font-serif font-bold text-[#593D2B] dark:text-[#F9F7F2]">
              BunaVision
            </span>
            <span>— Raw Green Coffee Bean Optical Intelligence</span>
          </div>
          <p>
            © {new Date().getFullYear()} BunaVision Agricultural Systems. All rights reserved.
          </p>
        </div>
        <div className="flex items-start gap-2 border-t border-[#E8E0D5]/50 dark:border-[#382E26]/50 pt-3 text-[11px] text-[#5A544C] leading-relaxed">
          <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
          <p>
            <strong>Mandatory AI Limitation Notice:</strong> BunaVision delivers automated
            optical surface defect region counting for raw green coffee bean samples prior to
            roasting. It does not issue official cup scores, sensory certificates, or internal
            density evaluations. Certified human Q-grader verification is required for all export
            documentation.
          </p>
        </div>
      </div>
    </footer>
  )
}
