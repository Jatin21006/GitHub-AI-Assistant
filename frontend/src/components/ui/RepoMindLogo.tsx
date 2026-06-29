import { cn } from '../../utils/cn';

interface RepoMindLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

export const RepoMindLogo = ({ size = 'md', showText = true, className }: RepoMindLogoProps) => {
  const sizes = {
    sm: { icon: 28, text: 'text-base' },
    md: { icon: 36, text: 'text-xl' },
    lg: { icon: 48, text: 'text-3xl' },
  };

  const { icon, text } = sizes[size];

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div 
        className="flex items-center justify-center rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] shadow-[0_0_24px_var(--rm-accent-glow)]"
        style={{ width: icon, height: icon }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          style={{ width: icon * 0.55, height: icon * 0.55 }}
          className="text-white"
        >
          {/* Brain/neural network inspired icon */}
          <path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M12 6v12M8 8l4 4-4 4M16 8l-4 4 4 4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      {showText && (
        <span className={cn("font-bold tracking-tight text-[var(--rm-text)]", text)}>
          Repo<span className="text-[var(--rm-accent)]">Mind</span>
        </span>
      )}
    </div>
  );
};
