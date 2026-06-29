import React from 'react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'secondary' | 'destructive' | 'accent';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rm-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--rm-bg)] disabled:pointer-events-none disabled:opacity-40 active:scale-[0.97] cursor-pointer",
          {
            // Default/Primary — violet accent with glow
            "bg-[var(--rm-accent)] text-white hover:bg-[var(--rm-accent-hover)] shadow-[0_0_20px_var(--rm-accent-glow)] hover:shadow-[0_0_30px_var(--rm-accent-glow-strong)]": variant === 'default',
            // Outline — bordered
            "border border-[var(--rm-border)] bg-transparent text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)] hover:border-[var(--rm-border-active)]": variant === 'outline',
            // Ghost — minimal
            "bg-transparent text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)]": variant === 'ghost',
            // Secondary — surface styled
            "bg-[var(--rm-surface)] text-[var(--rm-text-secondary)] hover:bg-[var(--rm-surface-hover)] hover:text-[var(--rm-text)] border border-[var(--rm-border)]": variant === 'secondary',
            // Destructive
            "bg-red-600/20 text-red-400 border border-red-500/20 hover:bg-red-600/30 hover:border-red-500/40": variant === 'destructive',
            // Accent — stronger glow
            "bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] text-white shadow-[0_0_30px_var(--rm-accent-glow-strong)] hover:shadow-[0_0_40px_var(--rm-accent-glow-strong)]": variant === 'accent',
            // Sizes
            "h-10 px-5 py-2": size === 'default',
            "h-8 rounded-lg px-3 text-xs": size === 'sm',
            "h-12 rounded-xl px-8 text-base": size === 'lg',
            "h-10 w-10 rounded-xl": size === 'icon',
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
