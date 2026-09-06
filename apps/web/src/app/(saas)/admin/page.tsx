'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Database, Play, RefreshCw } from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
import { PageLoading } from '@/components/common/loading';
import { StatCard } from '@/components/common/stat-card';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import {
  ingestionApi,
  literatureApi,
  type IngestionJob,
  type IngestionStatus,
  type MonitoringStatus
} from '@/lib/api-client';
import { useLanguage } from '@/lib/i18n/language-provider';

export default function AdminPage() {
  const { t } = useLanguage();
  const [monitoring, setMonitoring] = useState<MonitoringStatus | null>(null);
  const [litStatus, setLitStatus] = useState<IngestionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [source, setSource] = useState<'full' | 'kosis' | 'kdca'>('full');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, l] = await Promise.all([
        ingestionApi.getMonitoringStatus(),
        literatureApi.getIngestionStatus()
      ]);
      setMonitoring(m);
      setLitStatus(l);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.console.error.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleTrigger() {
    setTriggering(true);
    setMessage(null);
    setError(null);
    try {
      const res = await ingestionApi.trigger({ source, year: 2023 });
      setMessage(res.message);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.console.error.triggerFailed'));
    } finally {
      setTriggering(false);
    }
  }

  return (
    <PageLayout
      title={t('admin.console.title')}
      description={t('admin.console.description')}
      actions={
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      }
    >
      {loading && !monitoring ? (
        <PageLoading />
      ) : (
        <>
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}
          {message && (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
              {message}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title={t('admin.console.stat.totalJobs')}
              value={monitoring?.total_jobs ?? 0}
              icon={Database}
            />
            <StatCard
              title={t('admin.console.stat.completed')}
              value={monitoring?.completed_jobs ?? 0}
              description={`${t('admin.console.stat.failed')} ${monitoring?.failed_jobs ?? 0}`}
            />
            <StatCard
              title={t('admin.console.stat.indexedPapers')}
              value={litStatus?.indexed_papers ?? 0}
              icon={BookOpen}
            />
            <StatCard title={t('admin.console.stat.chunks')} value={litStatus?.total_chunks ?? 0} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t('admin.console.publicData.title')}</CardTitle>
                <CardDescription>{t('admin.console.publicData.description')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">{t('admin.console.source')}</label>
                  <Select value={source} onChange={(e) => setSource(e.target.value as typeof source)}>
                    <option value="full">{t('admin.console.source.full')}</option>
                    <option value="kosis">KOSIS</option>
                    <option value="kdca">KDCA</option>
                  </Select>
                </div>
                <Button className="gap-2" onClick={handleTrigger} disabled={triggering}>
                  <Play className="h-4 w-4" />
                  {triggering ? t('admin.console.running') : t('admin.console.runIngestion')}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('admin.console.literatureRag.title')}</CardTitle>
                <CardDescription>{t('admin.console.literatureRag.description')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2 text-sm">
                  <Badge variant="success">
                    {t('admin.console.indexed')} {litStatus?.indexed_papers ?? 0}
                  </Badge>
                  <Badge variant="warning">
                    {t('admin.console.pending')} {litStatus?.pending_papers ?? 0}
                  </Badge>
                  <Badge variant="destructive">
                    {t('admin.console.failed')} {litStatus?.failed_papers ?? 0}
                  </Badge>
                </div>
                <Link href="/admin/literature">
                  <Button variant="outline" className="w-full">
                    {t('admin.console.openLiteratureAdmin')}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t('admin.console.jobHistory.title')}</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pb-2">
              <AdminJobsTable jobs={monitoring?.recent_jobs ?? []} t={t} />
            </CardContent>
          </Card>
        </>
      )}
    </PageLayout>
  );
}

function AdminJobsTable({
  jobs,
  t
}: {
  jobs: IngestionJob[];
  t: ReturnType<typeof useLanguage>['t'];
}) {
  if (!jobs.length) {
    return (
      <p className="px-6 py-8 text-center text-sm text-[var(--muted-foreground)]">
        {t('admin.console.jobHistory.empty')}
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t('admin.console.table.id')}</TableHead>
          <TableHead>{t('admin.console.table.source')}</TableHead>
          <TableHead>{t('admin.console.table.status')}</TableHead>
          <TableHead>{t('admin.console.table.extractedToStored')}</TableHead>
          <TableHead>{t('admin.console.table.error')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow key={job.id}>
            <TableCell className="font-mono text-xs">{job.id.slice(0, 8)}…</TableCell>
            <TableCell>{job.source}</TableCell>
            <TableCell>
              <Badge
                variant={
                  job.status === 'completed'
                    ? 'success'
                    : job.status === 'failed'
                      ? 'destructive'
                      : 'warning'
                }
              >
                {job.status}
              </Badge>
            </TableCell>
            <TableCell>
              {job.records_extracted} → {job.records_stored}
            </TableCell>
            <TableCell className="max-w-[200px] truncate text-xs text-red-500">
              {job.error_message ?? '—'}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
