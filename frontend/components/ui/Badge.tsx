import React from 'react'

export type BadgeColor = 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'gray'

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
  gray: 'badge-apple bg-primary-200 text-primary-700',
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
