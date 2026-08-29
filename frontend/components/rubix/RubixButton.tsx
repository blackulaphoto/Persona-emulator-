'use client';

import { ButtonHTMLAttributes, ReactNode } from 'react';

export type RubixButtonVariant = 'primary' | 'ghost' | 'danger';

interface RubixButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'> {
  variant?: RubixButtonVariant;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantClass: Record<RubixButtonVariant, string> = {
  primary: 'rubix-btn-primary',
  ghost: 'rubix-btn-ghost',
  danger: 'rubix-btn-danger',
};

/** Real Rubix button — pill primary CTA / ghost / danger. No decorative variants. */
export function RubixButton({
  variant = 'primary',
  loading = false,
  icon,
  disabled,
  children,
  type = 'button',
  ...rest
}: RubixButtonProps) {
  return (
    <button
      type={type}
      className={variantClass[variant]}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? (
        <span
          aria-hidden="true"
          style={{
            width: 14,
            height: 14,
            borderRadius: '999px',
            border: '2px solid rgba(3,32,77,0.35)',
            borderTopColor: variant === 'primary' ? '#03204d' : 'currentColor',
            display: 'inline-block',
            animation: 'rubixSpin 0.7s linear infinite',
          }}
        />
      ) : (
        icon
      )}
      <span>{children}</span>
      <style jsx>{`
        @keyframes rubixSpin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
}
