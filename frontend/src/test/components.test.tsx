import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  StatusPill,
  ConfidenceBadge,
  Disclaimer,
  ErrorState,
  ProcessingState,
} from '../components/common'

describe('Shared Components', () => {
  describe('Disclaimer', () => {
    it('renders disclaimer copy with preliminary assessment warning', () => {
      render(<Disclaimer />)
      expect(screen.getByText(/Preliminary AI Screening/i)).toBeInTheDocument()
      expect(screen.getByText(/provide official coffee grading/i)).toBeInTheDocument()
    })

    it('renders compact disclaimer variant', () => {
      render(<Disclaimer variant="compact" />)
      expect(screen.getByText(/Preliminary AI assessment only/i)).toBeInTheDocument()
    })
  })

  describe('StatusPill', () => {
    it('renders completed status with text and icon', () => {
      render(<StatusPill status="completed" />)
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Status: Completed')
    })

    it('renders processing status with text and animated spinner', () => {
      render(<StatusPill status="processing" />)
      expect(screen.getByText('Processing')).toBeInTheDocument()
    })

    it('renders failed status with text', () => {
      render(<StatusPill status="failed" />)
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })
  })

  describe('ConfidenceBadge', () => {
    it('renders high confidence percentage without manual review flag', () => {
      render(<ConfidenceBadge confidence={0.92} threshold={0.5} />)
      expect(screen.getByText('92%')).toBeInTheDocument()
      expect(screen.queryByText(/Review manually/i)).not.toBeInTheDocument()
    })

    it('renders low confidence percentage with "Review manually" badge', () => {
      render(<ConfidenceBadge confidence={0.42} threshold={0.5} />)
      expect(screen.getByText('42%')).toBeInTheDocument()
      expect(screen.getByText(/Review manually/i)).toBeInTheDocument()
    })
  })

  describe('ErrorState', () => {
    it('renders mapped error code message and next step', () => {
      render(<ErrorState errorCode="INFERENCE_FAILED" />)
      expect(
        screen.getByText("The analysis didn't complete. Your image was not assessed."),
      ).toBeInTheDocument()
      expect(screen.getByText(/Retry or try another photo/i)).toBeInTheDocument()
    })
  })

  describe('ProcessingState', () => {
    it('renders loading status text and elapsed time', () => {
      render(<ProcessingState statusText="Processing image..." />)
      expect(screen.getByText('Processing image...')).toBeInTheDocument()
      expect(screen.getByText(/Elapsed time:/i)).toBeInTheDocument()
    })
  })
})
