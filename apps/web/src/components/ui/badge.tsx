import { cn } from '@/lib/utils';

type Variant = 'default' | 'secondary' | 'success' | 'warning' | 'destructive';

const variants: Record<Variant, string> = {
  default: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-300',
  secondary: 'bg-[var(--muted)] text-[var(--muted-foreground)]',
  success: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300',
  warning: 'bg-amber-500/15 text-amber-600 dark:text-amber-300',
  destructive: 'bg-red-500/15 text-red-600 dark:text-red-300'
};

export function Badge({
  className,
  variant = 'default',
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
