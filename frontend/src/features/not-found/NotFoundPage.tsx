import { Link } from 'react-router'
import { AlertCircle, ArrowLeft } from 'lucide-react'

export function NotFoundPage() {

  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center space-y-6">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
        <AlertCircle className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold font-serif text-[#382416] dark:text-[#F9F7F2]">
          Page Not Found (404)
        </h1>
        <p className="text-sm font-medium text-[#44403C] dark:text-[#D6D3D1] max-w-md mx-auto">
          The requested route does not exist or has been moved.
        </p>
      </div>

      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-all no-underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to BunaVision Home</span>
        </Link>
      </div>
    </div>
  )
}
