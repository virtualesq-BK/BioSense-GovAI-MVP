'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDown, Sparkles } from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
import { LoadingOverlay } from '@/components/common/loading';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { MetricsBarChart } from '@/components/charts/charts';
import {
  publicDataApi,
  recommendationsApi,
  type GenerateRecommendationRequest,
  type Region,
  type SensorRecommendation
} from '@/lib/api-client';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { saveReport } from '@/lib/reports-store';
import { exportReportToPdf } from '@/lib/pdf-export';

const CANCER_TYPES = [
  { value: 'CRC', label: '대장암 (CRC)' },
  { value: 'LUNG', label: '폐암 (LUNG)' },
  { value: 'BREAST', label: '유방암 (BREAST)' },
  { value: 'LIVER', label: '간암 (LIVER)' }
];

const CTDNA_CLASSES = [
  { value: 'mutation', label: '돌연변이 (Mutation)' },
  { value: 'methylation', label: '메틸화 (Methylation)' },
  { value: 'fragmentomics', label: '프래그먼토믹스' }
];

const DEFAULT_FORM: GenerateRecommendationRequest = {
  cancer_type: 'CRC',
  ctdna_class: 'mutation',
  region_code: '11',
  patient_age: 55,
  biomarker_name: 'KRAS G12D',
  top_k: 3
};

export default function RecommendationsPage() {
  const router = useRouter();
  const [form, setForm] = useState<GenerateRecommendationRequest>(DEFAULT_FORM);
  const [regions, setRegions] = useState<Region[]>([]);
  const [results, setResults] = useState<SensorRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    publicDataApi.listRegions().then(setRegions).catch(() => setRegions([]));
  }, []);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await recommendationsApi.generate(form);
      setResults(res.recommendations);
    } catch (e) {
      setError(e instanceof Error ? e.message : '추천 생성 실패');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [form]);

  function handleSaveReport() {
    if (!results.length) return;
    const report = saveReport(form, results);
    router.push(`/reports?id=${report.id}`);
  }

  function handleExportPdf() {
    if (!results.length) return;
    exportReportToPdf({
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      input: form,
      recommendations: results
    });
  }

  const chartData = results.map((r) => ({
    label: `#${r.rank}`,
    value: Math.round(r.confidence_score * 100)
  }));

  return (
    <PageLayout
      title="센서 추천"
      description="바이오마커·ctDNA 조건에 맞는 바이오센서 전략 생성"
      actions={
        results.length > 0 && (
          <>
            <Button variant="outline" size="sm" onClick={handleExportPdf}>
              <FileDown className="h-4 w-4" />
              PDF
            </Button>
            <Button size="sm" onClick={handleSaveReport}>
              리포트 저장
            </Button>
          </>
        )
      }
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>케이스 입력</CardTitle>
            <CardDescription>암종, ctDNA 분류, 지역, 바이오마커를 설정하세요.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="암종">
              <Select
                value={form.cancer_type}
                onChange={(e) => setForm((f) => ({ ...f, cancer_type: e.target.value }))}
              >
                {CANCER_TYPES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="ctDNA 분류">
              <Select
                value={form.ctdna_class}
                onChange={(e) => setForm((f) => ({ ...f, ctdna_class: e.target.value }))}
              >
                {CTDNA_CLASSES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="지역">
              <Select
                value={form.region_code}
                onChange={(e) => setForm((f) => ({ ...f, region_code: e.target.value }))}
              >
                {regions.length > 0 ? (
                  regions.map((r) => (
                    <option key={r.code} value={r.code}>
                      {r.name_ko}
                    </option>
                  ))
                ) : (
                  <option value="11">서울 (11)</option>
                )}
              </Select>
            </Field>
            <Field label="환자 연령">
              <Input
                type="number"
                min={0}
                max={120}
                value={form.patient_age}
                onChange={(e) =>
                  setForm((f) => ({ ...f, patient_age: Number(e.target.value) }))
                }
              />
            </Field>
            <Field label="바이오마커 (선택)">
              <Input
                value={form.biomarker_name ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, biomarker_name: e.target.value }))}
                placeholder="예: KRAS G12D"
              />
            </Field>
            <Field label="Top-K">
              <Input
                type="number"
                min={1}
                max={10}
                value={form.top_k ?? 3}
                onChange={(e) => setForm((f) => ({ ...f, top_k: Number(e.target.value) }))}
              />
            </Field>
            {error && (
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            )}
            <Button className="w-full gap-2" onClick={handleGenerate} disabled={loading}>
              <Sparkles className="h-4 w-4" />
              추천 생성
            </Button>
          </CardContent>
        </Card>

        <div className="relative space-y-6 lg:col-span-3">
          {loading && <LoadingOverlay label="하이브리드 검색 중…" />}
          {results.length === 0 && !loading ? (
            <Card>
              <CardContent className="flex min-h-[400px] flex-col items-center justify-center text-center">
                <Sparkles className="mb-4 h-10 w-10 text-[var(--muted-foreground)]" />
                <p className="font-medium">추천 결과가 여기에 표시됩니다</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  케이스를 입력하고 추천 생성을 클릭하세요.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {chartData.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>신뢰도 비교</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MetricsBarChart data={chartData} dataKey="value" xKey="label" />
                  </CardContent>
                </Card>
              )}
              {results.map((rec) => (
                <RecommendationCard key={rec.rank} rec={rec} />
              ))}
            </>
          )}
        </div>
      </div>
    </PageLayout>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}

function RecommendationCard({ rec }: { rec: SensorRecommendation }) {
  const m = rec.expected_metrics;
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge>#{rec.rank}</Badge>
            <CardTitle className="text-base">{rec.sensor_name}</CardTitle>
          </div>
          <CardDescription className="mt-1">
            {rec.recognition_name} · {rec.biomarker_name}
          </CardDescription>
        </div>
        <Badge variant="success">신뢰도 {formatPercent(rec.confidence_score)}</Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed text-[var(--muted-foreground)]">{rec.rationale}</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricPill label="민감도" value={formatPercent(m.sensitivity)} />
          <MetricPill label="특이도" value={formatPercent(m.specificity)} />
          <MetricPill label="LOD" value={`${m.lod_value} ${m.lod_unit}`} />
          <MetricPill label="예상 비용" value={formatCurrency(m.estimated_cost_usd)} />
        </div>
      </CardContent>
    </Card>
  );
}

function MetricPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-[var(--muted)] px-3 py-2">
      <p className="text-xs text-[var(--muted-foreground)]">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}
