import { cn } from '@/lib/utils';
import { type LucideIcon } from 'lucide-react';

type StatCardProps = {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: { value: string; positive?: boolean };
  className?: string;
};

export function StatCard({ title, value, description, icon: Icon, trend, className }: StatCardProps) {
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
          <div className="rounded-lg bg-[var(--muted)] p-2.5">
            <Icon className="h-5 w-5 text-[var(--accent)]" />
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
