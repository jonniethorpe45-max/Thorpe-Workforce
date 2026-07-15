import type { CSSProperties, HTMLAttributes, ReactNode } from 'react';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}

export function Badge({ className, style, children, ...rest }: BadgeProps) {
  return (
    <span className={className} style={style} {...rest}>
      {children}
    </span>
  );
}
