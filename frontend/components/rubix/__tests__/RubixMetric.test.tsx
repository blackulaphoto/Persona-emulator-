import { render, screen } from '@testing-library/react'
import { RubixMetric } from '../RubixMetric'

describe('RubixMetric', () => {
  it('renders the label and the caller-formatted value text', () => {
    render(<RubixMetric label="Openness" valueLabel="60%" percent={60} />)
    expect(screen.getByText('Openness')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('clamps the fill width to [0, 100] so an out-of-range percent never breaks the bar', () => {
    const { container } = render(<RubixMetric label="X" valueLabel="150" percent={150} />)
    const fill = container.querySelector('.rubix-meter-fill') as HTMLElement
    expect(fill.style.width).toBe('100%')
  })

  it('clamps a negative percent to 0 rather than rendering a negative width', () => {
    const { container } = render(<RubixMetric label="X" valueLabel="-10" percent={-10} />)
    const fill = container.querySelector('.rubix-meter-fill') as HTMLElement
    expect(fill.style.width).toBe('0%')
  })
})
