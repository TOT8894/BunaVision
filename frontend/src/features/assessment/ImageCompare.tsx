import { useState } from 'react'
import type { CompletedAssessment } from '../../types/assessment'

export function ImageCompare({ images, onRefresh }: { images: CompletedAssessment['result']['images']; onRefresh: () => void }) {
  const [refreshed, setRefreshed] = useState(false)
  const handleError = () => {
    if (!refreshed) { setRefreshed(true); onRefresh() }
  }
  const image = (url: string | null, label: string) => url ? <img src={url} alt={label} onError={handleError} className="h-72 w-full rounded-lg object-contain bg-slate-100" /> : <div className="flex h-72 items-center justify-center rounded-lg bg-slate-100 p-6 text-center text-sm text-slate-600">{label} is not available for this assessment.</div>
  return <section aria-labelledby="images-heading" className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <h2 id="images-heading" className="text-lg font-semibold">Image review</h2>
    <p className="mt-1 text-sm text-slate-600">Compare the submitted image with the model annotation. Image links refresh automatically if they expire.</p>
    <div className="mt-4 grid gap-5 lg:grid-cols-2"><div><h3 className="mb-2 text-sm font-medium">Original image</h3>{image(images.original_url, 'Original uploaded coffee sample image')}</div><div><h3 className="mb-2 text-sm font-medium">Annotated image</h3>{image(images.annotated_url, 'Annotated coffee sample image')}</div></div>
  </section>
}
