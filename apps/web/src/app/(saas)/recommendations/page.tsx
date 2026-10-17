'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BookOpen, FileDown, Sparkles } from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
import { LoadingOverlay } from '@/components/common/loading';
import { CitationDrawer } from '@/components/features/literature/citation-drawer';
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
import { useLanguage } from '@/lib/i18n/language-provider';
import type { Locale } from '@/lib/i18n/dictionary';

const CANCER_TYPES: Record<Locale, { value: string; label: string }[]> = {
  ko: [
    { value: 'CRC', label: '대장암 (CRC)' },
    { value: 'LUNG', label: '폐암 (LUNG)' },
    { value: 'BREAST', label: '유방암 (BREAST)' },
    { value: 'LIVER', label: '간암 (LIVER)' }
  ],
  en: [
    { value: 'CRC', label: 'Colorectal Cancer (CRC)' },
    { value: 'LUNG', label: 'Lung Cancer (LUNG)' },
    { value: 'BREAST', label: 'Breast Cancer (BREAST)' },
    { value: 'LIVER', label: 'Liver Cancer (LIVER)' }
  ]
};

const CTDNA_CLASSES: Record<Locale, { value: string; label: string }[]> = {
  ko: [
    { value: 'mutation', label: '돌연변이 (Mutation)' },
    { value: 'methylation', label: '메틸화 (Methylation)' },
    { value: 'fragmentomics', label: '프래그먼토믹스' },
    { value: 'cnv', label: 'CNV' },
    { value: 'exosomal_mirna', label: '엑소좀 miRNA' },
    { value: 'ctc', label: 'CTC' },
    { value: 'multi_omics', label: '다중오믹스 패널' }
  ],
  en: [
    { value: 'mutation', label: 'Mutation' },
    { value: 'methylation', label: 'Methylation' },
    { value: 'fragmentomics', label: 'Fragmentomics' },
    { value: 'cnv', label: 'CNV' },
    { value: 'exosomal_mirna', label: 'Exosomal miRNA' },
    { value: 'ctc', label: 'CTC' },
    { value: 'multi_omics', label: 'Multi-omics Panel' }
  ]
};

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
  const { t, locale } = useLanguage();
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
      setError(e instanceof Error ? e.message : t('recommendations.error.generateFailed'));
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [form, t]);

  async function handleSaveReport() {
    if (!results.length) return;
    try {
      const report = await saveReport(form, results);
      router.push(`/reports?id=${report.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save report');
    }
  }

  function handleExportPdf() {
    if (!results.length) return;
    exportReportToPdf(
      {
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        input: form,
        recommendations: results
      },
      locale
    );
  }

  const chartData = results.map((r) => ({
    label: `#${r.rank}`,
    value: Math.round(r.confidence_score * 100)
  }));

  return (
    <PageLayout
      title={t('recommendations.title')}
      description={t('recommendations.description')}
      actions={
        results.length > 0 && (
          <>
            <Button variant="outline" size="sm" onClick={handleExportPdf}>
              <FileDown className="h-4 w-4" />
              {t('recommendations.pdf')}
            </Button>
            <Button size="sm" onClick={handleSaveReport}>
              {t('recommendations.saveReport')}
            </Button>
          </>
        )
      }
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t('recommendations.caseInput')}</CardTitle>
            <CardDescription>{t('recommendations.caseInput.description')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label={t('recommendations.field.cancerType')}>
              <Select
                value={form.cancer_type}
                onChange={(e) => setForm((f) => ({ ...f, cancer_type: e.target.value }))}
              >
                {CANCER_TYPES[locale].map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t('recommendations.field.ctdnaClass')}>
              <Select
                value={form.ctdna_class}
                onChange={(e) => setForm((f) => ({ ...f, ctdna_class: e.target.value }))}
              >
                {CTDNA_CLASSES[locale].map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t('recommendations.field.region')}>
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
                  <option value="11">{t('recommendations.seoul')}</option>
                )}
              </Select>
            </Field>
            <Field label={t('recommendations.field.patientAge')}>
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
            <Field label={t('recommendations.field.biomarker')}>
              <Input
                value={form.biomarker_name ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, biomarker_name: e.target.value }))}
                placeholder="e.g. KRAS G12D"
              />
            </Field>
            <Field label={t('recommendations.field.topK')}>
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
              {t('recommendations.generate')}
            </Button>
          </CardContent>
        </Card>

        <div className="relative space-y-6 lg:col-span-3">
          {loading && <LoadingOverlay label={t('recommendations.loading')} />}
          {results.length === 0 && !loading ? (
            <Card>
              <CardContent className="flex min-h-[400px] flex-col items-center justify-center text-center">
                <Sparkles className="mb-4 h-10 w-10 text-[var(--muted-foreground)]" />
                <p className="font-medium">{t('recommendations.empty.title')}</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  {t('recommendations.empty.description')}
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {chartData.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>{t('recommendations.confidenceComparison')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MetricsBarChart data={chartData} dataKey="value" xKey="label" />
                  </CardContent>
                </Card>
              )}
              {results.map((rec) => (
                <RecommendationCard key={rec.rank} rec={rec} t={t} />
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

function RecommendationCard({
  rec,
  t
}: {
  rec: SensorRecommendation;
  t: ReturnType<typeof useLanguage>['t'];
}) {
  const m = rec.expected_metrics;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const literatureCount = rec.evidence?.literature_ids?.length ?? 0;

  return (
    <>
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
          <Badge variant="success">
            {t('recommendations.confidence')} {formatPercent(rec.confidence_score)}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-[var(--muted-foreground)]">{rec.rationale}</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricPill label={t('recommendations.metric.sensitivity')} value={formatPercent(m.sensitivity)} />
            <MetricPill label={t('recommendations.metric.specificity')} value={formatPercent(m.specificity)} />
            <MetricPill label={t('recommendations.metric.lod')} value={`${m.lod_value} ${m.lod_unit}`} />
            <MetricPill
              label={t('recommendations.metric.estimatedCost')}
              value={formatCurrency(m.estimated_cost_usd)}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => setDrawerOpen(true)}
          >
            <BookOpen className="h-4 w-4" />
            {t('recommendations.viewEvidence')}
            {literatureCount > 0 ? ` (${literatureCount})` : ''}
          </Button>
        </CardContent>
      </Card>
      <CitationDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        evidence={rec.evidence}
        sensorName={rec.sensor_name}
      />
    </>
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
