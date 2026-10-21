import { cn } from '@/lib/utils';
import { type LucideIcon } from 'lucide-react';

type StatCardVariant = 'default' | 'success' | 'warning' | 'danger';

type StatCardProps = {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: { value: string; positive?: boolean };
  variant?: StatCardVariant;
  className?: string;
};

const iconVariantBg: Record<StatCardVariant, string> = {
  default: 'bg-(--muted)',
  success: 'bg-emerald-100 dark:bg-emerald-900/30',
  warning: 'bg-amber-100 dark:bg-amber-900/30',
  danger: 'bg-red-100 dark:bg-red-900/30'
};

const iconVariantColor: Record<StatCardVariant, string> = {
  default: 'text-(--accent)',
  success: 'text-emerald-600 dark:text-emerald-400',
  warning: 'text-amber-600 dark:text-amber-400',
  danger: 'text-red-600 dark:text-red-400'
};

export function StatCard({ title, value, description, icon: Icon, trend, variant = 'default', className }: StatCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 shadow-sm',
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm text-[var(--muted-foreground)]">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {description && (
            <p className="text-xs text-[var(--muted-foreground)]">{description}</p>
          )}
        </div>
        {Icon && (
          <div className={cn('rounded-lg p-2.5', iconVariantBg[variant])}>
            <Icon className={cn('h-5 w-5', iconVariantColor[variant])} />
          </div>
        )}
      </div>
      {trend && (
        <p
          className={cn(
            'mt-3 text-xs font-medium',
            trend.positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'
          )}
        >
          {trend.value}
        </p>
      )}
    </div>
  );
}
