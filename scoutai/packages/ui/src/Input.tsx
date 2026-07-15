import type { InputHTMLAttributes, CSSProperties } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  className?: string;
  style?: CSSProperties;
}

export function Input({ className, style, ...rest }: InputProps) {
  return <input className={className} style={style} {...rest} />;
}
