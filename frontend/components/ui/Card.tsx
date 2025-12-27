import React from 'react'

export type CardVariant = 'default' | 'glass' | 'elevated' | 'dark'

interface CardProps {
  variant?: CardVariant
  hover?: boolean
  className?: string
  children: React.ReactNode
  onClick?: () => void
}

const variantClasses = {
  default: 'card-apple',
  glass: 'glass-card',
  elevated: 'card-apple-elevated',
  dark: 'card-apple-dark',
}

export function Card({
  variant = 'default',
  hover = false,
  className = '',
  children,
  onClick,
}: CardProps) {
  const baseClass = variantClasses[variant]
  const hoverClass = hover && variant === 'default' ? 'cursor-pointer' : ''

  return (
    <div
      className={`${baseClass} ${hoverClass} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
