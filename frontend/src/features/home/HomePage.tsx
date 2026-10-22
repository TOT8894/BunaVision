import { Link } from 'react-router'

export function HomePage() {
  return (
    <section className="mx-auto max-w-3xl py-8 sm:py-16">
      <p className="text-sm font-semibold tracking-wide text-leaf-700">GREEN COFFEE SCREENING</p>
      <h1 className="mt-3 text-4xl font-bold tracking-tight text-coffee-700 sm:text-5xl">
        Understand visible defects in your coffee sample.
      </h1>
      <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-700">
        Upload a clear photo and receive a preliminary AI prediction of the supported visible defect
        regions.
      </p>
      <Link
        className="mt-8 inline-flex rounded-md bg-leaf-700 px-5 py-3 font-semibold text-white no-underline hover:bg-leaf-700/90 focus:outline-2 focus:outline-offset-2 focus:outline-leaf-700"
        to="/upload"
      >
        Start an assessment
      </Link>
      <div className="mt-10 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-slate-800">
        <strong>Important:</strong> BunaVision is a decision-support tool. Results are preliminary
        AI predictions, not verified findings or an official grade. Review the sample manually
        before making quality decisions.
      </div>
    </section>
  )
}
