import { cn } from '@/lib/utils';
import { forwardRef, type ButtonHTMLAttributes } from 'react';

type Variant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg' | 'icon';

const variants: Record<Variant, string> = {
  default: 'bg-[var(--accent)] text-[var(--accent-foreground)] hover:opacity-90 shadow-sm',
  secondary: 'bg-[var(--muted)] text-[var(--foreground)] hover:opacity-80',
  outline:
    'border border-[var(--border)] bg-transparent hover:bg-[var(--muted)] text-[var(--foreground)]',
  ghost: 'hover:bg-[var(--muted)] text-[var(--foreground)]',
  destructive: 'bg-red-600 text-white hover:bg-red-500'
};

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs rounded-md',
  md: 'h-10 px-4 text-sm rounded-lg',
  lg: 'h-11 px-6 text-sm rounded-lg',
  icon: 'h-9 w-9 rounded-lg p-0 inline-flex items-center justify-center'
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = 'Button';
