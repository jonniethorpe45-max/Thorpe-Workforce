import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}

export function Button({ className, style, children, type = 'button', ...rest }: ButtonProps) {
  return (
    <button type={type} className={className} style={style} {...rest}>
      {children}
    </button>
  );
}
