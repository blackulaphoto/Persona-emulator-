import React from 'react'

export type BadgeColor = 'blue' | 'green' | 'orange' | 'red' | 'purple'

interface BadgeProps {
  color?: BadgeColor
  className?: string
  children: React.ReactNode
}

const colorClasses = {
  blue: 'badge-apple-blue',
  green: 'badge-apple-green',
  orange: 'badge-apple-orange',
  red: 'badge-apple-red',
  purple: 'badge-apple-purple',
}

export function Badge({
  color = 'blue',
  className = '',
  children,
}: BadgeProps) {
  return (
    <span className={`${colorClasses[color]} ${className}`}>
      {children}
    </span>
  )
}
