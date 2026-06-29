import { cn } from '../../utils/cn';

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'text' | 'card' | 'circle' | 'rectangle';
}

export const LoadingSkeleton = ({ className, variant = 'text' }: LoadingSkeletonProps) => {
  return (
    <div
      className={cn(
        "animate-shimmer bg-[var(--rm-surface)] rounded-xl",
        {
          "h-4 w-full": variant === 'text',
          "h-32 w-full": variant === 'card',
          "h-10 w-10 rounded-full": variant === 'circle',
          "h-20 w-full": variant === 'rectangle',
        },
        className
      )}
    />
  );
};

export const CardSkeleton = () => (
  <div className="p-5 rounded-2xl bg-[var(--rm-surface)] border border-[var(--rm-border)] space-y-4">
    <LoadingSkeleton variant="text" className="w-2/3" />
    <LoadingSkeleton variant="text" className="w-1/2" />
    <LoadingSkeleton variant="rectangle" className="h-12" />
  </div>
);
