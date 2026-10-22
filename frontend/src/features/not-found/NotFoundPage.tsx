import { Link } from 'react-router'
import { PlaceholderPage } from '../../components/common/PlaceholderPage'

export function NotFoundPage() { return <PlaceholderPage title="Page not found"><p>The page you requested does not exist.</p><Link className="font-semibold text-leaf-700" to="/">Return to BunaVision</Link></PlaceholderPage> }
