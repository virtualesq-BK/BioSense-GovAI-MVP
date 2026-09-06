'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, BookOpen, FlaskConical } from 'lucide-react';
import { PageLayout } from '@/components/layout/page-layout';
import { LoadingOverlay } from '@/components/common/loading';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  publicDataApi,
  rndApi,
  type Region,
  type RndDesignReport,
  type RndDesignRequest,
  type SensorCandidate
} from '@/lib/api-client';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { useLanguage } from '@/lib/i18n/language-provider';
import type { Locale } from '@/lib/i18n/dictionary';

const CANCERS: Record<Locale, { value: string; label: string }[]> = {
  ko: [
    { value: 'lung', label: '폐암' },
    { value: 'colorectal', label: '대장암' },
    { value: 'breast', label: '유방암' },
    { value: 'liver', label: '간암' },
    { value: 'stomach', label: '위암' },
    { value: 'pancreatic', label: '췌장암' },
    { value: 'ovarian', label: '난소암' },
    { value: 'prostate', label: '전립선암' }
  ],
  en: [
    { value: 'lung', label: 'Lung Cancer' },
    { value: 'colorectal', label: 'Colorectal Cancer' },
    { value: 'breast', label: 'Breast Cancer' },
    { value: 'liver', label: 'Liver Cancer' },
    { value: 'stomach', label: 'Stomach Cancer' },
    { value: 'pancreatic', label: 'Pancreatic Cancer' },
    { value: 'ovarian', label: 'Ovarian Cancer' },
    { value: 'prostate', label: 'Prostate Cancer' }
  ]
};

const CTDNA_CLASSES = [
  'mutation',
  'methylation',
  'fragmentomics',
  'cnv',
  'exosomal_mirna',
  'ctc',
  'multi_omics'
];

const DEFAULT_FORM: RndDesignRequest = {
  country: 'Korea',
  cancer: 'lung',
  biomarker_type: 'mutation',
  target_gene: '',
  goal: '',
  region_code: 'KR-11',
  patient_age: 55
};

export default function RndDesignPage() {
  const { t, locale } = useLanguage();
  const [form, setForm] = useState<RndDesignRequest>(DEFAULT_FORM);
  const [regions, setRegions] = useState<Region[]>([]);
  const [report, setReport] = useState<RndDesignReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    publicDataApi.listRegions().then(setRegions).catch(() => setRegions([]));
  }, []);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await rndApi.design({
        ...form,
        biomarker_type: form.biomarker_type || undefined,
        target_gene: form.target_gene || undefined,
        goal: form.goal || t('rndDesign.field.goal.placeholder')
      });
      setReport(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('rndDesign.error.generateFailed'));
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [form, t]);

  return (
    <PageLayout title={t('rndDesign.title')} description={t('rndDesign.description')}>
      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t('rndDesign.caseInput')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label={t('rndDesign.field.cancer')}>
              <Select
                value={form.cancer}
                onChange={(e) => setForm((f) => ({ ...f, cancer: e.target.value }))}
              >
                {CANCERS[locale].map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t('rndDesign.field.biomarkerType')}>
              <Select
                value={form.biomarker_type ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, biomarker_type: e.target.value }))}
              >
                <option value="">{t('rndDesign.field.biomarkerType.any')}</option>
                {CTDNA_CLASSES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t('rndDesign.field.targetGene')}>
              <Input
                value={form.target_gene ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, target_gene: e.target.value }))}
                placeholder="e.g. EGFR"
              />
            </Field>
            <Field label={t('rndDesign.field.goal')}>
              <Input
                value={form.goal}
                onChange={(e) => setForm((f) => ({ ...f, goal: e.target.value }))}
                placeholder={t('rndDesign.field.goal.placeholder')}
              />
            </Field>
            <Field label={t('rndDesign.field.region')}>
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
                  <option value="KR-11">{t('recommendations.seoul')}</option>
                )}
              </Select>
            </Field>
            <Field label={t('rndDesign.field.patientAge')}>
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
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <Button className="w-full gap-2" onClick={handleGenerate} disabled={loading}>
              <FlaskConical className="h-4 w-4" />
              {t('rndDesign.generate')}
            </Button>
          </CardContent>
        </Card>

        <div className="relative space-y-6 lg:col-span-3">
          {loading && <LoadingOverlay label={t('rndDesign.loading')} />}
          {!report && !loading ? (
            <Card>
              <CardContent className="flex min-h-[400px] flex-col items-center justify-center text-center">
                <FlaskConical className="mb-4 h-10 w-10 text-[var(--muted-foreground)]" />
                <p className="font-medium">{t('rndDesign.empty.title')}</p>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  {t('rndDesign.empty.description')}
                </p>
              </CardContent>
            </Card>
          ) : (
            report && <ReportView report={report} t={t} />
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

function ReportView({
  report,
  t
}: {
  report: RndDesignReport;
  t: ReturnType<typeof useLanguage>['t'];
}) {
  const epi = report.epidemiological_evidence;
  const mol = report.molecular_characteristics;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div>
            <CardTitle>{report.target_disease}</CardTitle>
            <CardDescription>{report.goal}</CardDescription>
          </div>
          <Badge variant={report.evidence_confidence >= 50 ? 'success' : 'warning'}>
            {t('rndDesign.section.confidence')}: {report.evidence_confidence.toFixed(1)}
          </Badge>
        </CardHeader>
      </Card>

      <Section title={t('rndDesign.section.epidemiology')}>
        {epi.missing_data ? (
          <MissingBadge t={t} />
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricPill
              label={`${epi.region_name_ko ?? epi.region_code} · Incidence`}
              value={epi.incidence_rate != null ? epi.incidence_rate.toFixed(1) : '—'}
            />
            <MetricPill
              label={`${epi.region_name_ko ?? epi.region_code} · Mortality`}
              value={epi.mortality_rate != null ? epi.mortality_rate.toFixed(1) : '—'}
            />
            <MetricPill
              label={`${t('rndDesign.regionAverage')} · Incidence`}
              value={epi.national_incidence_avg != null ? epi.national_incidence_avg.toFixed(1) : '—'}
            />
            <MetricPill
              label={`${t('rndDesign.regionAverage')} · Mortality`}
              value={epi.national_mortality_avg != null ? epi.national_mortality_avg.toFixed(1) : '—'}
            />
          </div>
        )}
        <p className="mt-2 text-xs text-[var(--muted-foreground)]">{epi.source}</p>
      </Section>

      <Section title={t('rndDesign.section.biomarkerCandidates')}>
        {report.biomarker_candidates.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">{t('rndDesign.noBiomarkerFound')}</p>
        ) : (
          <div className="space-y-2">
            {report.biomarker_candidates.map((c) => (
              <div
                key={c.biomarker_name}
                className={cnRow(c.biomarker_name === report.selected_biomarker_name)}
              >
                <span className="font-medium">{c.biomarker_name}</span>
                <Badge variant={c.biomarker_name === report.selected_biomarker_name ? 'success' : 'secondary'}>
                  {c.total_score.toFixed(1)}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title={t('rndDesign.section.molecular')}>
        {mol.missing_data ? (
          <MissingBadge t={t} />
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <MetricPill label="Gene" value={mol.gene_symbol ?? '—'} />
            <MetricPill label="Biotype" value={mol.biotype ?? '—'} />
            <MetricPill label="Mutations (GDC)" value={mol.mutation_count?.toLocaleString() ?? '—'} />
          </div>
        )}
      </Section>

      {report.recognition_strategy && (
        <Section title={t('rndDesign.section.recognition')}>
          <Badge>{report.recognition_strategy}</Badge>
        </Section>
      )}

      {report.sensor_candidates.length > 0 && (
        <Section title={t('rndDesign.section.sensors')}>
          <div className="space-y-3">
            {report.sensor_candidates.map((sc) => (
              <SensorRow key={`${sc.sensor_name}-${sc.recognition_code}`} sc={sc} t={t} />
            ))}
          </div>
        </Section>
      )}

      {report.existing_evidence.length > 0 && (
        <Section title={t('rndDesign.section.evidence')}>
          <ul className="space-y-2">
            {report.existing_evidence.map((ref) => (
              <li key={ref.external_id} className="flex items-start gap-2 text-sm">
                <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-[var(--muted-foreground)]" />
                <span>
                  {ref.title} <span className="text-[var(--muted-foreground)]">({ref.source})</span>
                </span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {report.experimental_design_hypothesis && (
        <Section title={t('rndDesign.section.protocol')}>
          <Badge variant={report.experimental_design_hypothesis.is_ai_suggested ? 'warning' : 'success'}>
            {report.experimental_design_hypothesis.is_ai_suggested
              ? t('rndDesign.aiSuggested')
              : t('rndDesign.curatedProtocol')}
          </Badge>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-[var(--muted-foreground)]">
            {report.experimental_design_hypothesis.steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </Section>
      )}

      <Section title={t('rndDesign.section.limitations')} tone="warning">
        <ul className="space-y-1.5 text-sm">
          {report.data_limitations.map((l, i) => (
            <li key={i} className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
              <span className="text-[var(--muted-foreground)]">{l}</span>
            </li>
          ))}
        </ul>
      </Section>

      {report.references.length > 0 && (
        <Section title={t('rndDesign.section.references')}>
          <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--muted-foreground)]">
            {report.references.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function SensorRow({
  sc,
  t
}: {
  sc: SensorCandidate;
  t: ReturnType<typeof useLanguage>['t'];
}) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium">{sc.sensor_name}</p>
          <p className="text-xs text-[var(--muted-foreground)]">{sc.recognition_name}</p>
        </div>
        {sc.is_estimated === null ? (
          <Badge variant="secondary">{t('rndDesign.missingData')}</Badge>
        ) : sc.is_estimated ? (
          <Badge variant="warning">{t('rndDesign.estimated')}</Badge>
        ) : (
          <Badge variant="success">{t('rndDesign.measured')}</Badge>
        )}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <MetricPill label="Sensitivity" value={sc.sensitivity != null ? formatPercent(sc.sensitivity) : '—'} />
        <MetricPill label="Specificity" value={sc.specificity != null ? formatPercent(sc.specificity) : '—'} />
        <MetricPill
          label="LOD"
          value={sc.lod_value != null ? `${sc.lod_value} ${sc.lod_unit ?? ''}` : '—'}
        />
        <MetricPill
          label="Est. Cost"
          value={sc.estimated_cost_usd != null ? formatCurrency(sc.estimated_cost_usd) : '—'}
        />
      </div>
    </div>
  );
}

function Section({
  title,
  tone,
  children
}: {
  title: string;
  tone?: 'warning';
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className={tone === 'warning' ? 'pb-2' : undefined}>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
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

function MissingBadge({ t }: { t: ReturnType<typeof useLanguage>['t'] }) {
  return <Badge variant="secondary">{t('rndDesign.missingData')}</Badge>;
}

function cnRow(highlighted: boolean) {
  return `flex items-center justify-between rounded-lg px-3 py-2 ${
    highlighted ? 'bg-[var(--accent)]/10' : 'bg-[var(--muted)]'
  }`;
}
