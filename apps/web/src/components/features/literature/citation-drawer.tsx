'use client';

import { useEffect, useMemo, useState } from 'react';
import { BookOpen, ExternalLink, X } from 'lucide-react';
import { PageLoading } from '@/components/common/loading';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  literatureApi,
  type LiteratureCitation,
  type PaperSummary,
  type RecommendationEvidence
} from '@/lib/api-client';
import { cn, formatPercent } from '@/lib/utils';
import { useLanguage } from '@/lib/i18n/language-provider';

export type CitationDrawerProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  evidence: RecommendationEvidence | null | undefined;
  sensorName?: string;
};

type CitationItem = {
  key: string;
  paperId: string;
  paper: PaperSummary | null;
  citation: LiteratureCitation | null;
  error?: string;
};

function extractLiteratureIds(evidence: RecommendationEvidence | null | undefined): string[] {
  const ids = evidence?.literature_ids ?? [];
  return [...new Set(ids.map(String).filter(Boolean))];
}

function citationIndex(
  evidence: RecommendationEvidence | null | undefined
): Map<string, LiteratureCitation> {
  const map = new Map<string, LiteratureCitation>();
  for (const cit of evidence?.citations ?? []) {
    if (cit.paper_id) map.set(cit.paper_id, cit);
    if (cit.paper_external_id) map.set(cit.paper_external_id, cit);
  }
  return map;
}

function resolveDoi(metadata: Record<string, unknown> | undefined): string | null {
  if (!metadata) return null;
  const raw = metadata.doi ?? metadata.DOI;
  if (typeof raw !== 'string' || !raw.trim()) return null;
  const doi = raw.replace(/^https?:\/\/(dx\.)?doi\.org\//i, '').trim();
  return doi || null;
}

function resolveJournal(metadata: Record<string, unknown> | undefined): string | null {
  if (!metadata) return null;
  const raw = metadata.journal ?? metadata.Journal ?? metadata.journal_name;
  return typeof raw === 'string' && raw.trim() ? raw.trim() : null;
}

function doiHref(doi: string): string {
  return doi.startsWith('http') ? doi : `https://doi.org/${doi}`;
}

export function CitationDrawer({
  open,
  onOpenChange,
  evidence,
  sensorName
}: CitationDrawerProps) {
  const { t } = useLanguage();
  const literatureIds = useMemo(() => extractLiteratureIds(evidence), [evidence]);
  const cites = useMemo(() => citationIndex(evidence), [evidence]);
  const [items, setItems] = useState<CitationItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    if (literatureIds.length === 0) {
      setItems([]);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    (async () => {
      const results = await Promise.all(
        literatureIds.map(async (paperId) => {
          const citation = cites.get(paperId) ?? null;
          try {
            const paper = await literatureApi.getPaper(paperId);
            return {
              key: paperId,
              paperId,
              paper,
              citation: citation ?? cites.get(paper.external_id) ?? null
            } satisfies CitationItem;
          } catch (e) {
            return {
              key: paperId,
              paperId,
              paper: null,
              citation,
              error: e instanceof Error ? e.message : t('citation.loadFailed')
            } satisfies CitationItem;
          }
        })
      );
      if (!cancelled) {
        setItems(results);
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [open, literatureIds, cites, t]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onOpenChange(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
        aria-label={t('citation.close')}
        onClick={() => onOpenChange(false)}
      />
      <aside
        className={cn(
          'relative flex h-full w-full max-w-md flex-col border-l border-[var(--border)]',
          'bg-[var(--card)] text-[var(--card-foreground)] shadow-xl'
        )}
      >
        <div className="flex items-start justify-between gap-3 border-b border-[var(--border)] px-5 py-4">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-[var(--accent)]" />
              <h2 className="text-base font-semibold">{t('citation.title')}</h2>
            </div>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              {sensorName ? `${sensorName} ${t('citation.subtitleFor')}` : t('citation.subtitleDefault')}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={t('citation.close')}
            onClick={() => onOpenChange(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading ? (
            <PageLoading label={t('citation.loading')} />
          ) : literatureIds.length === 0 ? (
            <EmptyCitations />
          ) : (
            <ul className="space-y-4">
              {items.map((item) => (
                <li key={item.key}>
                  <CitationCard item={item} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </div>
  );
}

function EmptyCitations() {
  const { t } = useLanguage();
  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center gap-2 text-center text-[var(--muted-foreground)]">
      <BookOpen className="h-8 w-8 opacity-50" />
      <p className="text-sm font-medium text-[var(--foreground)]">{t('citation.empty.title')}</p>
      <p className="text-xs">{t('citation.empty.description')}</p>
    </div>
  );
}

function CitationCard({ item }: { item: CitationItem }) {
  const { t } = useLanguage();
  const title =
    item.paper?.title ?? item.citation?.paper_title ?? item.paperId;
  const excerpt = item.citation?.excerpt?.trim();
  const relevance = item.citation?.relevance_score;
  const metadata = item.paper?.metadata;
  const doi = resolveDoi(metadata);
  const journal = resolveJournal(metadata);
  const externalId = item.paper?.external_id ?? item.citation?.paper_external_id;

  return (
    <Card>
      <CardHeader className="gap-2 p-4 pb-0">
        <div className="flex flex-wrap items-center gap-2">
          {relevance != null && (
            <Badge variant="success">
              {t('citation.relevance')} {formatPercent(relevance)}
            </Badge>
          )}
          {externalId && <Badge variant="secondary">{externalId}</Badge>}
        </div>
        <CardTitle className="text-sm leading-snug">{title}</CardTitle>
        {item.paper?.authors?.length ? (
          <CardDescription className="line-clamp-2">
            {item.paper.authors.join(', ')}
          </CardDescription>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-3 p-4">
        {item.error && !item.paper ? (
          <p className="text-sm text-red-600 dark:text-red-400">{item.error}</p>
        ) : null}

        {excerpt ? (
          <blockquote className="border-l-2 border-[var(--accent)] pl-3 text-sm leading-relaxed text-[var(--muted-foreground)]">
            {excerpt}
          </blockquote>
        ) : item.paper?.abstract ? (
          <p className="line-clamp-4 text-sm leading-relaxed text-[var(--muted-foreground)]">
            {item.paper.abstract}
          </p>
        ) : (
          <p className="text-xs text-[var(--muted-foreground)]">{t('citation.noExcerpt')}</p>
        )}

        <div className="flex flex-wrap items-center gap-2">
          {doi ? (
            <a
              href={doiHref(doi)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm font-medium text-[var(--accent)] hover:underline"
            >
              DOI: {doi}
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : journal ? (
            <span className="text-sm text-[var(--muted-foreground)]">{journal}</span>
          ) : (
            <span className="text-xs text-[var(--muted-foreground)]">
              {t('citation.noDoiJournal')}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
