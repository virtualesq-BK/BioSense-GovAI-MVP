'use client';

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/lib/i18n/language-provider';

export function LoadingSpinner({ className }: { className?: string }) {
  return <Loader2 className={cn('h-5 w-5 animate-spin text-[var(--accent)]', className)} />;
}

export function PageLoading({ label }: { label?: string }) {
  const { t } = useLanguage();
  const resolvedLabel = label ?? t('common.loadingData');
  return (
    <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 text-[var(--muted-foreground)]">
      <LoadingSpinner className="h-8 w-8" />
      <p className="text-sm">{resolvedLabel}</p>
    </div>
  );
}

export function LoadingOverlay({ label }: { label?: string }) {
  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-[var(--card)]/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-2">
        <LoadingSpinner className="h-7 w-7" />
        {label && <p className="text-xs text-[var(--muted-foreground)]">{label}</p>}
      </div>
    </div>
  );
}
