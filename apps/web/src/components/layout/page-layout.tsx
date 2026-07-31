'use client';

import { Topbar } from '@/components/layout/topbar';
import { useSidebar } from '@/components/layout/app-shell';

type PageLayoutProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
};

export function PageLayout({ title, description, actions, children }: PageLayoutProps) {
  const { openSidebar } = useSidebar();

  return (
    <>
      <Topbar
        title={title}
        description={description}
        onMenuClick={openSidebar}
        actions={actions}
      />
      <main className="flex-1 space-y-6 p-4 lg:p-8">{children}</main>
    </>
  );
}
