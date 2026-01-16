import React from 'react'

export type BadgeColor = 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'gray'

interface BadgeProps {
  color?: BadgeColor
  className?: string
  children: React.ReactNode
}

const colorClasses = {
  blue: 'badge-purple',        // Purple is the new primary
  green: 'badge-green',
  orange: 'badge-coral',       // Orange/red mapped to coral
  red: 'badge-coral',
  purple: 'badge-purple',
  gray: 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-soft-gray text-slate',
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
