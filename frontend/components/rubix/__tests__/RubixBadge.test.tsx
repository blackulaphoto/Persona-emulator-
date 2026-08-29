import { render, screen } from '@testing-library/react'
import { RubixBadge } from '../RubixBadge'

describe('RubixBadge', () => {
  it('renders its children as visible text', () => {
    render(<RubixBadge tone="positive">Secure</RubixBadge>)
    expect(screen.getByText('Secure')).toBeInTheDocument()
  })

  it('does not hardcode a specific domain vocabulary - renders whatever status string the caller passes', () => {
    render(<RubixBadge tone="caution">weakened</RubixBadge>)
    expect(screen.getByText('weakened')).toBeInTheDocument()
  })
})
