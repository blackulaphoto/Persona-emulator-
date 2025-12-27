import React from 'react'

export type CardVariant = 'default' | 'glass' | 'elevated' | 'dark'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant
  hover?: boolean
  children: React.ReactNode
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
  ...props
}: CardProps) {
  const baseClass = variantClasses[variant]
  const hoverClass = hover && variant === 'default' ? 'cursor-pointer' : ''

  return (
    <div
      className={`${baseClass} ${hoverClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
