import { AppShell } from '@/components/layout/app-shell';

export default function SaasLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
