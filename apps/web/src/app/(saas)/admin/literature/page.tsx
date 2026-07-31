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

type Tab = 'papers' | 'query' | 'evaluation';

const SAMPLE_TEXT = `Abstract: Electrochemical detection of KRAS G12D mutations in circulating tumor DNA 
using aptamer-based biosensors. We demonstrate a gold electrode sensor with 0.1 ng/mL limit of detection 
for ctDNA biomarker KRAS G12D in colorectal cancer patients. The aptamer recognition strategy achieved 
92% sensitivity and 94% specificity. Methylation markers including SEPT9 were also evaluated for 
early cancer screening applications.`;

export default function LiteratureAdminPage() {
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
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

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
      setError(e instanceof Error ? e.message : 'Ingest failed');
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
      setError(err instanceof Error ? err.message : 'Upload failed');
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
      setError(e instanceof Error ? e.message : 'Query failed');
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
      setError(e instanceof Error ? e.message : 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'papers', label: '논문 수집' },
    { id: 'query', label: 'RAG 쿼리' },
    { id: 'evaluation', label: '평가' }
  ];

  return (
    <PageLayout
      title="과학 문헌 RAG"
      description="PDF 수집 → 청킹 → pgvector 임베딩 → 바이오마커 추천 + 인용"
    >
      {status && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard title="전체" value={status.total_papers} />
          <StatCard title="인덱싱됨" value={status.indexed_papers} />
          <StatCard title="대기" value={status.pending_papers} />
          <StatCard title="실패" value={status.failed_papers} />
          <StatCard title="청크" value={status.total_chunks} />
        </div>
      )}

      <div className="flex gap-1 border-b border-[var(--border)]">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium transition-colors',
              tab === t.id
                ? 'border-b-2 border-[var(--accent)] text-[var(--accent)]'
                : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
            )}
          >
            {t.label}
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
                샘플 논문 텍스트 수집
              </Button>
              <label className="cursor-pointer">
                <span className="inline-flex h-10 items-center rounded-lg border border-[var(--border)] px-4 text-sm font-medium hover:bg-[var(--muted)]">
                  PDF 업로드
                </span>
                <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
              </label>
              <Button variant="outline" onClick={refresh} disabled={loading}>
                새로고침
              </Button>
            </div>
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>제목</TableHead>
                      <TableHead>ID</TableHead>
                      <TableHead>상태</TableHead>
                      <TableHead>청크</TableHead>
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
                          수집된 논문이 없습니다.
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
                <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="RAG 쿼리" />
                <Input
                  value={biomarker}
                  onChange={(e) => setBiomarker(e.target.value)}
                  placeholder="바이오마커 (선택)"
                />
                <Button onClick={handleQuery} disabled={loading}>
                  바이오마커 추천 생성
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
                        {rec.sensor_strategy} · {rec.recognition_approach} · confidence{' '}
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
                  placeholder="평가 쿼리"
                />
                <Input
                  value={evalTerms}
                  onChange={(e) => setEvalTerms(e.target.value)}
                  placeholder="기대 키워드 (쉼표 구분)"
                />
                <Button onClick={handleEvaluate} disabled={loading}>
                  검색 품질 평가 실행
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
                  <CardTitle className="text-sm">평가 이력</CardTitle>
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
