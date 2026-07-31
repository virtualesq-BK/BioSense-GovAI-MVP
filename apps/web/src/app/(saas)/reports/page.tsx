'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { FileDown, Trash2 } from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
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
import { exportReportToPdf, exportTableToPdf } from '@/lib/pdf-export';
import { deleteReport, getReport, listReports, type SavedReport } from '@/lib/reports-store';
import { formatPercent } from '@/lib/utils';
import Link from 'next/link';

function ReportsContent() {
  const searchParams = useSearchParams();
  const selectedId = searchParams.get('id');
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [selected, setSelected] = useState<SavedReport | null>(null);

  const refresh = useCallback(() => {
    const all = listReports();
    setReports(all);
    if (selectedId) {
      setSelected(getReport(selectedId) ?? all[0] ?? null);
    } else {
      setSelected(all[0] ?? null);
    }
  }, [selectedId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function handleDelete(id: string) {
    deleteReport(id);
    refresh();
  }

  function handleExportSelected() {
    if (!selected) return;
    exportReportToPdf(selected);
  }

  function handleExportTable() {
    exportTableToPdf(
      'BioSense 리포트 목록',
      ['생성일', '암종', '지역', '추천 수', 'Top 센서'],
      reports.map((r) => [
        new Date(r.createdAt).toLocaleDateString('ko-KR'),
        r.input.cancer_type,
        r.input.region_code,
        String(r.recommendations.length),
        r.recommendations[0]?.sensor_name ?? '—'
      ])
    );
  }

  return (
    <PageLayout
      title="리포트"
      description="저장된 추천 결과 조회 및 PDF보내기"
      actions={
        <>
          {reports.length > 0 && (
            <>
              <Button variant="outline" size="sm" onClick={handleExportTable}>
                <FileDown className="h-4 w-4" />
                목록 PDF
              </Button>
              {selected && (
                <Button size="sm" onClick={handleExportSelected}>
                  <FileDown className="h-4 w-4" />
                  선택 PDF
                </Button>
              )}
            </>
          )}
          <Link href="/recommendations">
            <Button variant="outline" size="sm">
              새 추천
            </Button>
          </Link>
        </>
      }
    >
      {reports.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[320px] flex-col items-center justify-center text-center">
            <p className="font-medium">저장된 리포트가 없습니다</p>
            <p className="mt-2 text-sm text-[var(--muted-foreground)]">
              추천 페이지에서 결과를 생성한 뒤 &quot;리포트 저장&quot;을 클릭하세요.
            </p>
            <Link href="/recommendations" className="mt-6">
              <Button>추천 생성하기</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-5">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>저장된 리포트</CardTitle>
              <CardDescription>{reports.length}건</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>날짜</TableHead>
                    <TableHead>암종</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reports.map((r) => (
                    <TableRow
                      key={r.id}
                      className={selected?.id === r.id ? 'bg-[var(--muted)]/60' : 'cursor-pointer'}
                      onClick={() => setSelected(r)}
                    >
                      <TableCell>
                        {new Date(r.createdAt).toLocaleDateString('ko-KR')}
                      </TableCell>
                      <TableCell>{r.input.cancer_type}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(r.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="space-y-4 lg:col-span-3">
            {selected ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>입력 조건</CardTitle>
                    <CardDescription>
                      {new Date(selected.createdAt).toLocaleString('ko-KR')}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <dl className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <dt className="text-[var(--muted-foreground)]">암종</dt>
                        <dd className="font-medium">{selected.input.cancer_type}</dd>
                      </div>
                      <div>
                        <dt className="text-[var(--muted-foreground)]">ctDNA</dt>
                        <dd className="font-medium">{selected.input.ctdna_class}</dd>
                      </div>
                      <div>
                        <dt className="text-[var(--muted-foreground)]">지역</dt>
                        <dd className="font-medium">{selected.input.region_code}</dd>
                      </div>
                      <div>
                        <dt className="text-[var(--muted-foreground)]">연령</dt>
                        <dd className="font-medium">{selected.input.patient_age}세</dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>

                {selected.recommendations.map((rec) => (
                  <Card key={rec.rank}>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="text-base">
                        #{rec.rank} {rec.sensor_name}
                      </CardTitle>
                      <Badge variant="success">{formatPercent(rec.confidence_score)}</Badge>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-[var(--muted-foreground)]">{rec.rationale}</p>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs">
                        <Badge variant="secondary">
                          민감도 {formatPercent(rec.expected_metrics.sensitivity)}
                        </Badge>
                        <Badge variant="secondary">
                          LOD {rec.expected_metrics.lod_value} {rec.expected_metrics.lod_unit}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </>
            ) : (
              <PageLoading label="리포트를 선택하세요" />
            )}
          </div>
        </div>
      )}
    </PageLayout>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<PageLoading />}>
      <ReportsContent />
    </Suspense>
  );
}
