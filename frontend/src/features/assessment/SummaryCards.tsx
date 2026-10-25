import type { CompletedAssessment } from '../../types/assessment'

export function SummaryCards({ summary }: { summary: CompletedAssessment['result']['summary'] }) {
  const cards = [['Defect regions', summary.detection_count, 'Regions detected by the model; not a bean count.'], ['Primary regions', summary.primary_detection_count, 'Detected primary-category defect regions.'], ['Secondary regions', summary.secondary_detection_count, 'Detected secondary-category defect regions.']]
  return <section aria-label="Assessment summary" className="grid gap-3 sm:grid-cols-3">{cards.map(([label, value, help]) => <div key={String(label)} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-sm text-slate-600">{label}</p><p className="mt-1 text-3xl font-semibold text-coffee-700">{value}</p><p className="mt-1 text-xs text-slate-500">{help}</p></div>)}</section>
}
