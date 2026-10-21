'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Database,
  RefreshCw,
  Sparkles,
  XCircle
} from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
import { StatCard } from '@/components/common/stat-card';
import { PageLoading } from '@/components/common/loading';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { MetricsBarChart, StatusDonutChart, TrendAreaChart } from '@/components/charts/charts';
import {
  healthApi,
  ingestionApi,
  literatureApi,
  type HealthResponse,
  type IngestionJob,
  type IngestionStatus,
  type MonitoringStatus
} from '@/lib/api-client';
import { useLanguage } from '@/lib/i18n/language-provider';

export default function DashboardPage() {
  const { t, locale } = useLanguage();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringStatus | null>(null);
  const [litStatus, setLitStatus] = useState<IngestionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthResult, monitoringResult, litResult] = await Promise.allSettled([
        healthApi.check(),
        ingestionApi.getMonitoringStatus(),
        literatureApi.getIngestionStatus()
      ]);

      if (healthResult.status === 'fulfilled') {
        setHealth(healthResult.value);
      }
      if (monitoringResult.status === 'fulfilled') {
        setMonitoring(monitoringResult.value);
      } else {
        setMonitoring(null);
      }
      if (litResult.status === 'fulfilled') {
        setLitStatus(litResult.value);
      } else {
        setLitStatus(null);
      }

      const failures = [healthResult, monitoringResult, litResult].filter(
        (r) => r.status === 'rejected'
      ) as PromiseRejectedResult[];

      if (healthResult.status === 'rejected') {
        const reason = healthResult.reason;
        setError(reason instanceof Error ? reason.message : t('common.error.loadFailed'));
      } else if (failures.length > 0) {
        setError(t('common.error.partial'));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t('common.error.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  const jobTrend = useMemo(() => {
    if (!monitoring?.recent_jobs.length) {
      return [
        { label: t('dashboard.day.mon'), value: 0 },
        { label: t('dashboard.day.tue'), value: 0 },
        { label: t('dashboard.day.wed'), value: 0 },
        { label: t('dashboard.day.thu'), value: 0 },
        { label: t('dashboard.day.fri'), value: 0 }
      ];
    }
    const byDay = monitoring.recent_jobs.slice(0, 7).reverse();
    return byDay.map((job, i) => ({
      label: `J${i + 1}`,
      value: job.records_stored
    }));
  }, [monitoring, t]);

  const literatureDonut = useMemo(
    () =>
      litStatus
        ? [
            { name: t('dashboard.donut.indexed'), value: litStatus.indexed_papers },
            { name: t('dashboard.donut.pending'), value: litStatus.pending_papers },
            { name: t('dashboard.donut.failed'), value: litStatus.failed_papers }
          ].filter((d) => d.value > 0)
        : [],
    [litStatus, t]
  );

  const metricsBar = useMemo(
    () =>
      litStatus
        ? [
            { label: t('dashboard.metric.papers'), value: litStatus.total_papers },
            { label: t('dashboard.metric.chunks'), value: litStatus.total_chunks },
            { label: t('dashboard.stat.completed'), value: litStatus.indexed_papers },
            { label: t('dashboard.metric.pending'), value: litStatus.pending_papers }
          ]
        : [],
    [litStatus, t]
  );

  return (
    <PageLayout
      title={t('dashboard.title')}
      description={t('dashboard.description')}
      actions={
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {t('common.refresh')}
        </Button>
      }
    >
      {error && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            health
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-200'
              : 'border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-300'
          }`}
        >
          {health ? error : `${t('common.error.apiDown')}: ${error}. ${t('common.error.checkBackend')}`}
        </div>
      )}

      {loading && !health ? (
        <PageLoading />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title={t('dashboard.stat.apiStatus')}
              value={
                health?.status === 'ok'
                  ? t('dashboard.stat.ok')
                  : health?.status === 'degraded'
                    ? t('dashboard.stat.degraded')
                    : health?.status === 'down'
                      ? t('dashboard.stat.down')
                      : t('dashboard.stat.needsAttention')
              }
              description={`v${health?.version ?? '—'}`}
              icon={
                health?.status === 'ok'
                  ? CheckCircle2
                  : health?.status === 'degraded'
                    ? AlertTriangle
                    : XCircle
              }
              variant={
                health?.status === 'ok'
                  ? 'success'
                  : health?.status === 'degraded'
                    ? 'warning'
                    : 'danger'
              }
            />
            <StatCard
              title={t('dashboard.stat.ingestionJobs')}
              value={monitoring?.total_jobs ?? 0}
              description={`${t('dashboard.stat.completed')} ${monitoring?.completed_jobs ?? 0} · ${t('dashboard.stat.failed')} ${monitoring?.failed_jobs ?? 0}`}
              icon={Database}
            />
            <StatCard
              title={t('dashboard.stat.indexedPapers')}
              value={litStatus?.indexed_papers ?? 0}
              description={`${t('dashboard.stat.totalPapers')} ${litStatus?.total_papers ?? 0}${t('dashboard.stat.papersUnit')}`}
              icon={BookOpen}
            />
            <StatCard
              title={t('dashboard.stat.vectorChunks')}
              value={litStatus?.total_chunks ?? 0}
              description={t('dashboard.stat.ragIndex')}
              icon={Sparkles}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t('dashboard.chart.ingestionTrend')}</CardTitle>
                <CardDescription>{t('dashboard.chart.recentRecords')}</CardDescription>
              </CardHeader>
              <CardContent>
                <TrendAreaChart data={jobTrend} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('dashboard.chart.literatureStatus')}</CardTitle>
                <CardDescription>{t('dashboard.chart.statusDistribution')}</CardDescription>
              </CardHeader>
              <CardContent>
                {literatureDonut.length > 0 ? (
                  <StatusDonutChart data={literatureDonut} totalLabel={t('dashboard.donut.total')} />
                ) : (
                  <p className="py-16 text-center text-sm text-[var(--muted-foreground)]">
                    {t('dashboard.chart.noLiteratureData')}
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>{t('dashboard.chart.metrics')}</CardTitle>
              </CardHeader>
              <CardContent>
                <MetricsBarChart data={metricsBar} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>{t('dashboard.recentJobs.title')}</CardTitle>
                <CardDescription>{t('dashboard.recentJobs.description')}</CardDescription>
              </div>
              <Link href="/admin">
                <Button variant="outline" size="sm">
                  {t('common.adminConsole')}
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0 pb-2">
              <JobsTable jobs={monitoring?.recent_jobs ?? []} />
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            <DependencyCard
              name="Supabase (Postgres)"
              status={health?.dependencies.postgres ?? 'down'}
            />
            <DependencyCard name="Neo4j" status={health?.dependencies.neo4j ?? 'down'} />
          </div>
        </>
      )}
    </PageLayout>
  );

  function DependencyCard({ name, status }: { name: string; status: string }) {
    const ok = status === 'ok';
    return (
      <div className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        <span className="font-medium">{name}</span>
        <Badge variant={ok ? 'success' : 'destructive'}>
          {ok ? t('dashboard.dependency.connected') : t('dashboard.dependency.offline')}
        </Badge>
      </div>
    );
  }

  function JobsTable({ jobs }: { jobs: IngestionJob[] }) {
    if (!jobs.length) {
      return (
        <p className="px-6 py-8 text-center text-sm text-[var(--muted-foreground)]">
          {t('dashboard.recentJobs.empty')}
        </p>
      );
    }

    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('dashboard.table.source')}</TableHead>
            <TableHead>{t('dashboard.table.status')}</TableHead>
            <TableHead>{t('dashboard.table.extracted')}</TableHead>
            <TableHead>{t('dashboard.table.stored')}</TableHead>
            <TableHead>{t('dashboard.table.createdAt')}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id}>
              <TableCell className="font-medium">{job.source}</TableCell>
              <TableCell>
                <JobStatusBadge status={job.status} />
              </TableCell>
              <TableCell>{job.records_extracted}</TableCell>
              <TableCell>{job.records_stored}</TableCell>
              <TableCell className="text-[var(--muted-foreground)]">
                {new Date(job.created_at).toLocaleDateString(locale === 'ko' ? 'ko-KR' : 'en-US')}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }
}

function JobStatusBadge({ status }: { status: string }) {
  const variant =
    status === 'completed' ? 'success' : status === 'failed' ? 'destructive' : 'warning';
  return <Badge variant={variant}>{status}</Badge>;
}
