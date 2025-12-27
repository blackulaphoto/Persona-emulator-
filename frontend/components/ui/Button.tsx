import React from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'danger' | 'success'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  icon?: React.ReactNode
  children: React.ReactNode
}

const sizeClasses = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
}

const variantClasses = {
  primary: 'btn-apple-primary',
  secondary: 'btn-apple-secondary',
  tertiary: 'btn-apple-tertiary',
  danger: 'btn-apple-danger',
  success: 'btn-apple-success',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${variantClasses[variant]} ${sizeClasses[size]} ${className} inline-flex items-center justify-center gap-2`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="spinner-apple" />
      )}
      {!loading && icon && icon}
      {children}
    </button>
  )
}
