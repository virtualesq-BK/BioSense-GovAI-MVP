'use client';

import { useCallback, useEffect, useState } from 'react';
import { PageLayout } from '@/components/layout/page-layout';
import { LoadingOverlay } from '@/components/common/loading';
import { StatCard } from '@/components/common/stat-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import {
  literatureApi,
  type IngestionStatus,
  type PaperSummary,
  type RagEvalResult,
  type RagQueryResult
} from '@/lib/api-client';
import { useLanguage } from '@/lib/i18n/language-provider';
import type { TranslationKey } from '@/lib/i18n/dictionary';

type Tab = 'papers' | 'query' | 'evaluation';

const SAMPLE_TEXT = `Abstract: Electrochemical detection of KRAS G12D mutations in circulating tumor DNA 
using aptamer-based biosensors. We demonstrate a gold electrode sensor with 0.1 ng/mL limit of detection 
for ctDNA biomarker KRAS G12D in colorectal cancer patients. The aptamer recognition strategy achieved 
92% sensitivity and 94% specificity. Methylation markers including SEPT9 were also evaluated for 
early cancer screening applications.`;

export default function LiteratureAdminPage() {
  const { t } = useLanguage();
  const [tab, setTab] = useState<Tab>('papers');
  const [papers, setPapers] = useState<PaperSummary[]>([]);
  const [status, setStatus] = useState<IngestionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState('KRAS ctDNA electrochemical biosensor');
  const [biomarker, setBiomarker] = useState('KRAS G12D mutation');
  const [queryResult, setQueryResult] = useState<RagQueryResult | null>(null);

  const [evalQuery, setEvalQuery] = useState('KRAS ctDNA aptamer biosensor');
  const [evalTerms, setEvalTerms] = useState('KRAS,aptamer,ctDNA');
  const [evalResult, setEvalResult] = useState<RagEvalResult | null>(null);
  const [evalHistory, setEvalHistory] = useState<
    Array<RagEvalResult & { expected_terms: string[] }>
  >([]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, s] = await Promise.all([
        literatureApi.listPapers(),
        literatureApi.getIngestionStatus()
      ]);
      setPapers(p);
      setStatus(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.error.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleIngestSample() {
    setLoading(true);
    setError(null);
    try {
      await literatureApi.ingestText({
        external_id: `pmid:sample-${Date.now()}`,
        title: 'Sample KRAS ctDNA Biosensor Paper',
        text: SAMPLE_TEXT
      });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.error.ingestFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      await literatureApi.uploadPdf(file, `upload:${file.name}`, file.name.replace('.pdf', ''));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.error.uploadFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function handleQuery() {
    setLoading(true);
    setError(null);
    try {
      const result = await literatureApi.ragQuery({
        query,
        biomarker_name: biomarker,
        cancer_type: 'colorectal',
        top_k: 5
      });
      setQueryResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.error.queryFailed'));
    } finally {
      setLoading(false);
    }
  }

  async function handleEvaluate() {
    setLoading(true);
    setError(null);
    try {
      const result = await literatureApi.ragEvaluate({
        query: evalQuery,
        expected_terms: evalTerms.split(',').map((t) => t.trim()),
        top_k: 5
      });
      setEvalResult(result);
      const history = await literatureApi.listEvaluations();
      setEvalHistory(history);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('admin.error.evalFailed'));
    } finally {
      setLoading(false);
    }
  }

  const tabs: { id: Tab; labelKey: TranslationKey }[] = [
    { id: 'papers', labelKey: 'admin.tab.papers' },
    { id: 'query', labelKey: 'admin.tab.query' },
    { id: 'evaluation', labelKey: 'admin.tab.evaluation' }
  ];

  return (
    <PageLayout title={t('admin.title')} description={t('admin.description')}>
      {status && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard title={t('admin.stat.total')} value={status.total_papers} />
          <StatCard title={t('admin.stat.indexed')} value={status.indexed_papers} />
          <StatCard title={t('admin.stat.pending')} value={status.pending_papers} />
          <StatCard title={t('admin.stat.failed')} value={status.failed_papers} />
          <StatCard title={t('admin.stat.chunks')} value={status.total_chunks} />
        </div>
      )}

      <div className="flex gap-1 border-b border-[var(--border)]">
        {tabs.map((tabItem) => (
          <button
            key={tabItem.id}
            type="button"
            onClick={() => setTab(tabItem.id)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium transition-colors',
              tab === tabItem.id
                ? 'border-b-2 border-[var(--accent)] text-[var(--accent)]'
                : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
            )}
          >
            {t(tabItem.labelKey)}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="relative">
        {loading && <LoadingOverlay />}

        {tab === 'papers' && (
          <section className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <Button onClick={handleIngestSample} disabled={loading}>
                {t('admin.ingestSample')}
              </Button>
              <label className="cursor-pointer">
                <span className="inline-flex h-10 items-center rounded-lg border border-[var(--border)] px-4 text-sm font-medium hover:bg-[var(--muted)]">
                  {t('admin.uploadPdf')}
                </span>
                <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
              </label>
              <Button variant="outline" onClick={refresh} disabled={loading}>
                {t('common.refresh')}
              </Button>
            </div>
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('admin.table.title')}</TableHead>
                      <TableHead>{t('admin.table.id')}</TableHead>
                      <TableHead>{t('admin.table.status')}</TableHead>
                      <TableHead>{t('admin.table.chunks')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {papers.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell>{p.title}</TableCell>
                        <TableCell className="font-mono text-xs text-[var(--muted-foreground)]">
                          {p.external_id}
                        </TableCell>
                        <TableCell>
                          <PaperStatusBadge status={p.ingestion_status} />
                        </TableCell>
                        <TableCell>{p.chunk_count}</TableCell>
                      </TableRow>
                    ))}
                    {papers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="py-8 text-center text-[var(--muted-foreground)]">
                          {t('admin.table.empty')}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>
        )}

        {tab === 'query' && (
          <section className="space-y-4">
            <Card>
              <CardContent className="space-y-3 pt-6">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t('admin.query.placeholder')}
                />
                <Input
                  value={biomarker}
                  onChange={(e) => setBiomarker(e.target.value)}
                  placeholder={t('admin.query.biomarkerPlaceholder')}
                />
                <Button onClick={handleQuery} disabled={loading}>
                  {t('admin.query.generate')}
                </Button>
              </CardContent>
            </Card>
            {queryResult && (
              <div className="space-y-4">
                <p className="text-xs text-[var(--muted-foreground)]">
                  {queryResult.chunks_retrieved} chunks · {queryResult.latency_ms}ms
                </p>
                {queryResult.recommendations.map((rec, i) => (
                  <Card key={i}>
                    <CardHeader>
                      <CardTitle className="text-base text-[var(--accent)]">
                        {rec.biomarker_name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">
                        {rec.sensor_strategy} · {rec.recognition_approach} · {t('admin.query.confidence')}{' '}
                        {rec.confidence}
                      </p>
                      <p className="mt-2 text-sm text-[var(--muted-foreground)]">{rec.rationale}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'evaluation' && (
          <section className="space-y-4">
            <Card>
              <CardContent className="space-y-3 pt-6">
                <Input
                  value={evalQuery}
                  onChange={(e) => setEvalQuery(e.target.value)}
                  placeholder={t('admin.eval.queryPlaceholder')}
                />
                <Input
                  value={evalTerms}
                  onChange={(e) => setEvalTerms(e.target.value)}
                  placeholder={t('admin.eval.termsPlaceholder')}
                />
                <Button onClick={handleEvaluate} disabled={loading}>
                  {t('admin.eval.run')}
                </Button>
              </CardContent>
            </Card>
            {evalResult && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard title="Precision@K" value={evalResult.precision_at_k} />
                <StatCard title="Recall@K" value={evalResult.recall_at_k} />
                <StatCard title="Citation" value={evalResult.citation_coverage} />
                <StatCard title="MRR" value={evalResult.mrr} />
              </div>
            )}
            {evalHistory.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{t('admin.eval.history')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1">
                  {evalHistory.slice(0, 5).map((e) => (
                    <p key={e.evaluation_id} className="text-xs text-[var(--muted-foreground)]">
                      P@{e.precision_at_k} R@{e.recall_at_k} MRR={e.mrr}
                    </p>
                  ))}
                </CardContent>
              </Card>
            )}
          </section>
        )}
      </div>
    </PageLayout>
  );
}

function PaperStatusBadge({ status }: { status: string }) {
  const variant =
    status === 'indexed' ? 'success' : status === 'failed' ? 'destructive' : 'secondary';
  return <Badge variant={variant}>{status}</Badge>;
}
