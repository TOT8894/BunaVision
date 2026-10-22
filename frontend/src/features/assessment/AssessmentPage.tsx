import { useParams } from 'react-router'
import { PlaceholderPage } from '../../components/common/PlaceholderPage'

export function AssessmentPage() {
  const { assessmentId } = useParams()
  return (
    <PlaceholderPage title="Assessment report">
      <p>Report rendering will be added here.</p>
      {assessmentId ? (
        <p className="text-sm text-slate-500">Assessment ID: {assessmentId}</p>
      ) : null}
    </PlaceholderPage>
  )
}
