'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UserMenu } from '@/components/auth/user-menu';
import { ThemeToggle } from '@/components/layout/theme-toggle';

type TopbarProps = {
  title: string;
  description?: string;
  onMenuClick: () => void;
  actions?: React.ReactNode;
};

export function Topbar({ title, description, onMenuClick, actions }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--background)]/80 px-4 backdrop-blur-md lg:px-8">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenuClick}>
          <Menu className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-lg font-semibold leading-tight">{title}</h1>
          {description && (
            <p className="hidden text-xs text-[var(--muted-foreground)] sm:block">{description}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {actions}
        <UserMenu />
        <ThemeToggle />
      </div>
    </header>
  );
}
