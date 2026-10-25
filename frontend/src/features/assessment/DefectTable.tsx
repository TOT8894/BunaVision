import { ConfidenceBadge } from '../../components/common/ConfidenceBadge'
import type { CompletedAssessment } from '../../types/assessment'

export function DefectTable({ rows }: { rows: CompletedAssessment['result']['summary']['by_class'] }) {
  return <section aria-labelledby="defects-heading" className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><h2 id="defects-heading" className="text-lg font-semibold">Detected defect regions</h2><p className="mt-1 text-sm text-slate-600">Counts refer to model-detected regions, not verified beans.</p>
    {rows.length === 0 ? <p className="mt-4 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-900">No supported defect regions were detected. This does not confirm the absence of defects.</p> : <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b text-slate-600"><tr><th className="p-2">Defect</th><th className="p-2">Category</th><th className="p-2">Regions</th><th className="p-2">Mean model confidence</th></tr></thead><tbody>{rows.map((row) => <tr key={row.defect.key} className="border-b border-slate-100"><td className="p-2 font-medium">{row.defect.name}</td><td className="p-2 capitalize">{row.defect.category}</td><td className="p-2">{row.count}</td><td className="p-2"><ConfidenceBadge confidence={row.mean_confidence} /></td></tr>)}</tbody></table></div>}
  </section>
}
