import { useState } from 'react'
import {
  PhoneCall,
  Mail,
  MapPin,
  Send,
  Copy,
  Check,
  CheckCircle2,
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

export function ContactsPage() {
  const { theme } = useTheme()
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [station, setStation] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')

  const card = `rounded-2xl border transition-all ${
    theme === 'dark'
      ? 'bg-[#231F1C] border-[#382E26] shadow-md shadow-black/20'
      : 'bg-white border-[#E8E0D5] shadow-xs'
  }`

  const inputCls = `w-full px-3.5 py-2.5 rounded-xl text-xs border focus:outline-none focus:ring-2 focus:ring-[#8BA470] transition-colors ${
    theme === 'dark'
      ? 'bg-[#181513] border-[#382E26] text-[#F9F7F2]'
      : 'bg-[#FAF8F5] border-[#E8E0D5] text-[#24211D]'
  }`

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2500)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitted(true)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* ── Top Header ── */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
          Agronomy Extension & Field Support
        </h1>
        <p className="text-sm text-[#5A544C] dark:text-[#C8C2BB] mt-1.5">
          Direct technical assistance for washing stations, cooperative quality labs, and export terminals.
        </p>
      </div>

      {/* ── 3 Channel Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Phone */}
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="w-12 h-12 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97]">
            <PhoneCall className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Field Helpdesk
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
              Direct assistance for field terminal calibration, camera mounts, and lighting trays.
            </p>
          </div>
          <p className="text-sm font-mono font-bold text-[#593D2B] dark:text-[#C4A882]">
            +251 (0) 11 555 0192
          </p>
          <div className="flex items-center gap-2 pt-2">
            <a
              href="tel:+251115550192"
              className="flex-1 text-center py-2 px-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-colors no-underline"
            >
              Call Helpdesk
            </a>
            <button
              type="button"
              onClick={() => handleCopy('+251115550192', 'phone')}
              className={`p-2 rounded-xl border transition-colors cursor-pointer ${
                theme === 'dark'
                  ? 'border-[#382E26] hover:bg-[#2C2723]'
                  : 'border-[#DDD5C8] hover:bg-[#FAF8F5]'
              }`}
              title="Copy phone"
            >
              {copiedKey === 'phone' ? (
                <Check className="w-4 h-4 text-[#4F7335]" />
              ) : (
                <Copy className="w-4 h-4 text-[#7B7569]" />
              )}
            </button>
          </div>
        </div>

        {/* Email */}
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="w-12 h-12 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97]">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Vision Model Feedback
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
              Submit false-positive images or tricky lighting samples to the ML team.
            </p>
          </div>
          <p className="text-sm font-mono font-bold text-[#593D2B] dark:text-[#C4A882]">
            feedback@bunavision.org
          </p>
          <div className="flex items-center gap-2 pt-2">
            <a
              href="mailto:feedback@bunavision.org"
              className="flex-1 text-center py-2 px-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-colors no-underline"
            >
              Send Email
            </a>
            <button
              type="button"
              onClick={() => handleCopy('feedback@bunavision.org', 'email')}
              className={`p-2 rounded-xl border transition-colors cursor-pointer ${
                theme === 'dark'
                  ? 'border-[#382E26] hover:bg-[#2C2723]'
                  : 'border-[#DDD5C8] hover:bg-[#FAF8F5]'
              }`}
              title="Copy email"
            >
              {copiedKey === 'email' ? (
                <Check className="w-4 h-4 text-[#4F7335]" />
              ) : (
                <Copy className="w-4 h-4 text-[#7B7569]" />
              )}
            </button>
          </div>
        </div>

        {/* Lab Address */}
        <div className={`p-6 sm:p-7 ${card} space-y-4`}>
          <div className="w-12 h-12 rounded-xl bg-[#8BA470]/15 flex items-center justify-center text-[#3A5228] dark:text-[#B5CF97]">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Central Agronomy Lab
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
              Cooperative Extension Center, Mexico Square, Addis Ababa, Ethiopia.
            </p>
          </div>
          <p className="text-xs text-[#7B7569] dark:text-[#A8A193]">
            Mon – Fri · 8:30 AM – 5:30 PM EAT
          </p>
          <div className="pt-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#8BA470]/15 text-[#3A5228] dark:text-[#B5CF97] text-xs font-semibold">
              <span>Walk-ins welcome with dry samples</span>
            </span>
          </div>
        </div>
      </div>

      {/* ── Consultation Form ── */}
      <div className={`p-6 sm:p-8 ${card} max-w-3xl mx-auto space-y-6`}>
        <div className="border-b border-[#E8E0D5] dark:border-[#382E26] pb-4">
          <h2 className="text-xl font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
            Direct Inquiry / Washing Station Consultation
          </h2>
          <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] mt-1">
            Leave a note regarding model deployment, optical tray hardware specs, or ECX alignment.
          </p>
        </div>

        {isSubmitted ? (
          <div className="py-12 text-center space-y-3">
            <div className="w-14 h-14 rounded-full bg-[#8BA470]/20 flex items-center justify-center mx-auto text-[#4F7335]">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold font-serif text-[#3B2416] dark:text-[#F9F7F2]">
              Inquiry Received
            </h3>
            <p className="text-xs text-[#5A544C] dark:text-[#C8C2BB] max-w-md mx-auto">
              Our regional field agronomy team in Addis Ababa will review your query and respond
              within 1 business day.
            </p>
            <button
              type="button"
              onClick={() => setIsSubmitted(false)}
              className="mt-4 px-4 py-2 rounded-xl bg-[#593D2B] text-white text-xs font-semibold cursor-pointer"
            >
              Send Another Inquiry
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Your Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="Abebe Bikila"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputCls}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="station.manager@coop.et"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputCls}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Washing Station / Cooperative
                </label>
                <input
                  type="text"
                  placeholder="e.g. Yirgacheffe Union #04"
                  value={station}
                  onChange={(e) => setStation(e.target.value)}
                  className={inputCls}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                  Inquiry Subject
                </label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className={inputCls}
                >
                  <option value="">Select subject...</option>
                  <option value="hardware">Tray Hardware & Illumination Mounts</option>
                  <option value="model">Computer Vision Defect Accuracy</option>
                  <option value="pilot">Washing Station Pilot Deployment</option>
                  <option value="other">General Question</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#5A544C] dark:text-[#C8C2BB]">
                Message
              </label>
              <textarea
                rows={4}
                required
                placeholder="Describe your equipment setup, lot volume, or technical inquiry..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className={inputCls}
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-[#593D2B] hover:bg-[#483020] text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center space-x-2 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit Inquiry to Agronomy Team</span>
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
