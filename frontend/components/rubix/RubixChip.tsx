'use client';

import { ButtonHTMLAttributes, ReactNode } from 'react';

interface RubixChipProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'> {
  active?: boolean;
  children: ReactNode;
}

/** Toggle-style pill — filters, tags, single-select choices (e.g. attachment style, event kind). */
export function RubixChip({ active = false, children, type = 'button', ...rest }: RubixChipProps) {
  return (
    <button type={type} className="rubix-chip" data-active={active ? 'true' : 'false'} aria-pressed={active} {...rest}>
      {children}
    </button>
  );
}
