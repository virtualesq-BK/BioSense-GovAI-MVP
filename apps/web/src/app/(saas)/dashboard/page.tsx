'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
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

export default function DashboardPage() {
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
        setError(reason instanceof Error ? reason.message : '데이터 로드 실패');
      } else if (failures.length > 0) {
        setError(
          '일부 데이터를 불러오지 못했습니다. Supabase(Postgres)가 연결되어 있는지 확인하세요.'
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '데이터 로드 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const jobTrend = useMemo(() => {
    if (!monitoring?.recent_jobs.length) {
      return [
        { label: '월', value: 0 },
        { label: '화', value: 0 },
        { label: '수', value: 0 },
        { label: '목', value: 0 },
        { label: '금', value: 0 }
      ];
    }
    const byDay = monitoring.recent_jobs.slice(0, 7).reverse();
    return byDay.map((job, i) => ({
      label: `J${i + 1}`,
      value: job.records_stored
    }));
  }, [monitoring]);

  const literatureDonut = useMemo(
    () =>
      litStatus
        ? [
            { name: '인덱싱 완료', value: litStatus.indexed_papers },
            { name: '대기', value: litStatus.pending_papers },
            { name: '실패', value: litStatus.failed_papers }
          ].filter((d) => d.value > 0)
        : [],
    [litStatus]
  );

  const metricsBar = useMemo(
    () =>
      litStatus
        ? [
            { label: '논문', value: litStatus.total_papers },
            { label: '청크', value: litStatus.total_chunks },
            { label: '완료', value: litStatus.indexed_papers },
            { label: '대기', value: litStatus.pending_papers }
          ]
        : [],
    [litStatus]
  );

  return (
    <PageLayout
      title="대시보드"
      description="플랫폼 상태, 데이터 파이프라인, 문헌 인덱스 개요"
      actions={
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          새로고침
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
          {health ? error : `API 연결 실패: ${error}. 백엔드가 실행 중인지 확인하세요.`}
        </div>
      )}

      {loading && !health ? (
        <PageLoading />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title="API 상태"
              value={health?.status === 'ok' ? '정상' : '점검 필요'}
              description={`v${health?.version ?? '—'}`}
              icon={health?.status === 'ok' ? CheckCircle2 : XCircle}
            />
            <StatCard
              title="수집 작업"
              value={monitoring?.total_jobs ?? 0}
              description={`완료 ${monitoring?.completed_jobs ?? 0} · 실패 ${monitoring?.failed_jobs ?? 0}`}
              icon={Database}
            />
            <StatCard
              title="인덱싱 논문"
              value={litStatus?.indexed_papers ?? 0}
              description={`전체 ${litStatus?.total_papers ?? 0}편`}
              icon={BookOpen}
            />
            <StatCard
              title="벡터 청크"
              value={litStatus?.total_chunks ?? 0}
              description="RAG 검색 인덱스"
              icon={Sparkles}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>수집 파이프라인 추이</CardTitle>
                <CardDescription>최근 작업별 저장 레코드 수</CardDescription>
              </CardHeader>
              <CardContent>
                <TrendAreaChart data={jobTrend} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>문헌 인덱스 현황</CardTitle>
                <CardDescription>논문 처리 상태 분포</CardDescription>
              </CardHeader>
              <CardContent>
                {literatureDonut.length > 0 ? (
                  <StatusDonutChart data={literatureDonut} />
                ) : (
                  <p className="py-16 text-center text-sm text-[var(--muted-foreground)]">
                    문헌 데이터 없음
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>문헌·데이터 메트릭</CardTitle>
              </CardHeader>
              <CardContent>
                <MetricsBarChart data={metricsBar} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>최근 수집 작업</CardTitle>
                <CardDescription>공공 데이터 ETL 작업 이력</CardDescription>
              </div>
              <Link href="/admin">
                <Button variant="outline" size="sm">
                  관리 콘솔
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
}

function JobsTable({ jobs }: { jobs: IngestionJob[] }) {
  if (!jobs.length) {
    return (
      <p className="px-6 py-8 text-center text-sm text-[var(--muted-foreground)]">
        수집 작업 이력이 없습니다.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>소스</TableHead>
          <TableHead>상태</TableHead>
          <TableHead>추출</TableHead>
          <TableHead>저장</TableHead>
          <TableHead>생성일</TableHead>
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
              {new Date(job.created_at).toLocaleDateString('ko-KR')}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function JobStatusBadge({ status }: { status: string }) {
  const variant =
    status === 'completed' ? 'success' : status === 'failed' ? 'destructive' : 'warning';
  return <Badge variant={variant}>{status}</Badge>;
}

function DependencyCard({ name, status }: { name: string; status: string }) {
  const ok = status === 'ok';
  return (
    <div className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <span className="font-medium">{name}</span>
      <Badge variant={ok ? 'success' : 'destructive'}>{ok ? '연결됨' : '오프라인'}</Badge>
    </div>
  );
}
