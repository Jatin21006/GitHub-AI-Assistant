import React from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-11 w-full rounded-xl border border-[var(--rm-border)] bg-[var(--rm-surface)] px-4 py-2 text-sm text-[var(--rm-text)] placeholder:text-[var(--rm-text-muted)] transition-all duration-200 file:border-0 file:bg-transparent file:text-sm file:font-medium focus:outline-none focus:border-[var(--rm-border-active)] focus:ring-2 focus:ring-[var(--rm-accent-glow)] disabled:cursor-not-allowed disabled:opacity-40",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
