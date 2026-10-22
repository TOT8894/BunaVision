import type { ReactNode } from 'react'

interface PlaceholderPageProps {
  title: string
  children: ReactNode
}

export function PlaceholderPage({ title, children }: PlaceholderPageProps) {
  return (
    <section className="mx-auto max-w-3xl rounded-xl border border-coffee-100 bg-white p-6 shadow-sm sm:p-8">
      <h1 className="text-2xl font-bold text-coffee-700 sm:text-3xl">{title}</h1>
      <div className="mt-4 space-y-4 text-slate-700">{children}</div>
    </section>
  )
}
