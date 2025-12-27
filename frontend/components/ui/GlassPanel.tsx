import React from 'react'

interface GlassPanelProps {
  className?: string
  children: React.ReactNode
}

export function GlassPanel({
  className = '',
  children,
}: GlassPanelProps) {
  return (
    <div className={`glass-panel ${className}`}>
      {children}
    </div>
  )
}
