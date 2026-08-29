'use client';

import { HTMLAttributes, ReactNode } from 'react';

export type RubixCardVariant = 'default' | 'hero' | 'flat';

interface RubixCardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'className'> {
  variant?: RubixCardVariant;
  interactive?: boolean;
  className?: string;
  children: ReactNode;
}

const variantClass: Record<RubixCardVariant, string> = {
  default: 'rubix-card',
  hero: 'rubix-card rubix-card-hero',
  flat: 'rubix-card-flat',
};

/** Translucent, layered Rubix surface. Never render an opaque rectangle here. */
export function RubixCard({ variant = 'default', interactive = false, className = '', children, ...rest }: RubixCardProps) {
  const classes = [variantClass[variant], interactive ? 'rubix-card-interactive' : '', className]
    .filter(Boolean)
    .join(' ');
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
