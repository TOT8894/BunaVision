import type { CompletedAssessment } from '../../types/assessment'

export function LimitationsPanel({ assessment }: { assessment: CompletedAssessment }) {
  const { limitations, coverage } = assessment.result
  return <aside aria-labelledby="limitations-heading" className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-950"><h2 id="limitations-heading" className="text-lg font-semibold">AI transparency and limitations</h2><p className="mt-2 text-sm">This is a preliminary AI screening of a photograph, not an official coffee grade. Review results manually and use them alongside appropriate quality-control procedures.</p><p className="mt-2 text-sm">Confidence is model confidence, not a guarantee of correctness. Only visible defects in the supported classes can be assessed.</p>{coverage.not_scanned.length > 0 && <p className="mt-2 text-sm">Not scanned: {coverage.not_scanned.map((item) => item.name).join(', ')}.</p>}<ul className="mt-3 list-disc space-y-1 pl-5 text-sm">{limitations.map((item) => <li key={item.code}>{item.message}</li>)}</ul></aside>
}
