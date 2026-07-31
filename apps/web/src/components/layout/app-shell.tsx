'use client';

import { createContext, useContext, useState } from 'react';
import { Sidebar } from '@/components/layout/sidebar';

type SidebarContextValue = {
  openSidebar: () => void;
  closeSidebar: () => void;
};

const SidebarContext = createContext<SidebarContextValue | null>(null);

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error('useSidebar must be used within AppShell');
  return ctx;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <SidebarContext.Provider
      value={{
        openSidebar: () => setSidebarOpen(true),
        closeSidebar: () => setSidebarOpen(false)
      }}
    >
      <div className="flex min-h-screen bg-[var(--background)]">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="flex min-w-0 flex-1 flex-col">{children}</div>
      </div>
    </SidebarContext.Provider>
  );
}
