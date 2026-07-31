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

export default function AdminPage() {
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
      setError(e instanceof Error ? e.message : '로드 실패');
    } finally {
      setLoading(false);
    }
  }, []);

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
      setError(e instanceof Error ? e.message : '트리거 실패');
    } finally {
      setTriggering(false);
    }
  }

  return (
    <PageLayout
      title="관리 콘솔"
      description="데이터 수집 파이프라인 및 문헌 RAG 관리"
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
              title="총 수집 작업"
              value={monitoring?.total_jobs ?? 0}
              icon={Database}
            />
            <StatCard
              title="완료"
              value={monitoring?.completed_jobs ?? 0}
              description={`실패 ${monitoring?.failed_jobs ?? 0}`}
            />
            <StatCard title="인덱싱 논문" value={litStatus?.indexed_papers ?? 0} icon={BookOpen} />
            <StatCard title="청크" value={litStatus?.total_chunks ?? 0} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>공공 데이터 수집</CardTitle>
                <CardDescription>KOSIS / KDCA ETL 파이프라인 수동 실행</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">소스</label>
                  <Select value={source} onChange={(e) => setSource(e.target.value as typeof source)}>
                    <option value="full">전체 동기화</option>
                    <option value="kosis">KOSIS</option>
                    <option value="kdca">KDCA</option>
                  </Select>
                </div>
                <Button className="gap-2" onClick={handleTrigger} disabled={triggering}>
                  <Play className="h-4 w-4" />
                  {triggering ? '실행 중…' : '수집 실행'}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>문헌 RAG</CardTitle>
                <CardDescription>PDF 업로드, RAG 쿼리, 평가 도구</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2 text-sm">
                  <Badge variant="success">인덱싱 {litStatus?.indexed_papers ?? 0}</Badge>
                  <Badge variant="warning">대기 {litStatus?.pending_papers ?? 0}</Badge>
                  <Badge variant="destructive">실패 {litStatus?.failed_papers ?? 0}</Badge>
                </div>
                <Link href="/admin/literature">
                  <Button variant="outline" className="w-full">
                    문헌 RAG Admin 열기
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>수집 작업 이력</CardTitle>
            </CardHeader>
            <CardContent className="p-0 pb-2">
              <AdminJobsTable jobs={monitoring?.recent_jobs ?? []} />
            </CardContent>
          </Card>
        </>
      )}
    </PageLayout>
  );
}

function AdminJobsTable({ jobs }: { jobs: IngestionJob[] }) {
  if (!jobs.length) {
    return (
      <p className="px-6 py-8 text-center text-sm text-[var(--muted-foreground)]">
        작업 이력 없음
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>소스</TableHead>
          <TableHead>상태</TableHead>
          <TableHead>추출→저장</TableHead>
          <TableHead>오류</TableHead>
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
