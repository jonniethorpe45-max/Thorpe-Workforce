import type { CSSProperties, HTMLAttributes, ReactNode } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}

export function Card({ className, style, children, ...rest }: CardProps) {
  return (
    <div className={className} style={style} {...rest}>
      {children}
    </div>
  );
}
