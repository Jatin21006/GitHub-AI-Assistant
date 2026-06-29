import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface CheckboxProps {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  className?: string;
  disabled?: boolean;
}

export const Checkbox: React.FC<CheckboxProps> = ({ id, checked, onChange, label, className, disabled = false }) => {
  return (
    <label
      htmlFor={id}
      className={cn(
        "flex items-center gap-3 cursor-pointer select-none group",
        disabled && "opacity-40 cursor-not-allowed",
        className
      )}
    >
      <button
        id={id}
        type="button"
        role="checkbox"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={cn(
          "flex items-center justify-center w-[18px] h-[18px] rounded-md border transition-all duration-200 flex-shrink-0",
          checked
            ? "bg-[var(--rm-accent)] border-[var(--rm-accent)] shadow-[0_0_12px_var(--rm-accent-glow)]"
            : "border-[var(--rm-border)] bg-transparent hover:border-[var(--rm-text-muted)]"
        )}
      >
        {checked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
      </button>
      {label && (
        <span className="text-sm text-[var(--rm-text-secondary)] group-hover:text-[var(--rm-text)] transition-colors">
          {label}
        </span>
      )}
    </label>
  );
};
