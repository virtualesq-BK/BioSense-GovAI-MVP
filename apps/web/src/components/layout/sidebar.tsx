'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Settings,
  Sparkles,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/lib/i18n/language-provider';
import type { TranslationKey } from '@/lib/i18n/dictionary';

const navItems: { href: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { href: '/dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/recommendations', labelKey: 'nav.recommendations', icon: Sparkles },
  { href: '/rnd-design', labelKey: 'nav.rndDesign', icon: FlaskConical },
  { href: '/reports', labelKey: 'nav.reports', icon: FileText },
  { href: '/admin', labelKey: 'nav.admin', icon: Settings }
];

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { t } = useLanguage();

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label={t('nav.closeMenu')}
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[var(--border)] bg-[var(--sidebar)] transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-[var(--border)] px-5">
          <Link href="/" className="flex items-center gap-2 font-semibold text-[var(--foreground)]">
            <Activity className="h-5 w-5 text-[var(--accent)]" />
            <span>BioSense</span>
          </Link>
          <button
            type="button"
            className="rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] lg:hidden"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map(({ href, labelKey, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  active
                    ? 'bg-[var(--sidebar-active)] text-[var(--accent)]'
                    : 'text-[var(--sidebar-foreground)] hover:bg-[var(--muted)]'
                )}
              >
                <Icon className="h-4 w-4" />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-[var(--border)] p-4 text-xs text-[var(--muted-foreground)]">
          {t('nav.footer')}
        </div>
      </aside>
    </>
  );
}
