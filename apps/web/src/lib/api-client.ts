function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, '');
  if (typeof window !== 'undefined') return '/api';
  return process.env.API_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000';
}

const API_BASE = resolveApiBase();

async function authHeaders(): Promise<Record<string, string>> {
  if (typeof window === 'undefined') return {};
  const { createClient } = await import('@/lib/supabase/client');
  const supabase = createClient();
  const {
    data: { session }
  } = await supabase.auth.getSession();
  if (!session?.access_token) return {};
  return { Authorization: `Bearer ${session.access_token}` };
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(await authHeaders()),
      ...init?.headers
    }
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// --- Health ---

export type HealthResponse = {
  status: string;
  version: string;
  dependencies: {
    postgres: string;
    neo4j: string;
  };
};

export type UserProfile = {
  id: string;
  auth_user_id: string;
  email: string;
  org_name: string | null;
  role: string;
  created_at: string;
};

// --- Recommendations ---

export type GenerateRecommendationRequest = {
  cancer_type: string;
  ctdna_class: string;
  region_code: string;
  patient_age: number;
  biomarker_name?: string | null;
  notes?: string | null;
  top_k?: number;
};

export type ExpectedMetrics = {
  sensitivity: number;
  specificity: number;
  lod_value: number;
  lod_unit: string;
  estimated_cost_usd: number;
};

export type SensorRecommendation = {
  rank: number;
  sensor_type: string;
  sensor_name: string;
  recognition_strategy: string;
  recognition_name: string;
  biomarker_name: string;
  expected_metrics: ExpectedMetrics;
  experimental_protocol: Record<string, unknown>;
  confidence_score: number;
  composite_score: number;
  rationale: string;
  evidence: Record<string, unknown>;
};

export type GenerateRecommendationResponse = {
  recommendations: SensorRecommendation[];
  count: number;
};

// --- Ingestion / Public Data ---

export type IngestionJob = {
  id: string;
  job_type: string;
  status: string;
  source: string;
  records_extracted: number;
  records_transformed: number;
  records_embedded: number;
  records_stored: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type MonitoringStatus = {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  last_success_at: string | null;
  last_job_status: string | null;
  recent_jobs: IngestionJob[];
};

export type Region = {
  code: string;
  name_ko: string;
  name_en: string;
};

export type CancerStats = {
  region_code: string;
  cancer_type: string;
  incidence_rate: number | null;
  mortality_rate: number | null;
  data_year: number;
  source: string;
};

// --- Literature ---

export type PaperSummary = {
  id: string;
  external_id: string;
  title: string;
  source: string;
  ingestion_status: string;
  chunk_count: number;
  pdf_filename: string | null;
  created_at: string;
};

export type IngestionStatus = {
  total_papers: number;
  indexed_papers: number;
  pending_papers: number;
  failed_papers: number;
  total_chunks: number;
};

export type RagQueryResult = {
  query: string;
  recommendations: Array<{
    biomarker_name: string;
    sensor_strategy: string;
    recognition_approach: string;
    rationale: string;
    confidence: number;
    citations: Array<{ paper_external_id: string; excerpt: string }>;
  }>;
  citations: Array<{ paper_external_id: string; paper_title: string; excerpt: string }>;
  chunks_retrieved: number;
  latency_ms: number;
};

export type RagEvalResult = {
  evaluation_id: string;
  precision_at_k: number;
  recall_at_k: number;
  citation_coverage: number;
  mrr: number;
  chunks_evaluated: number;
};

export const healthApi = {
  check: () => apiFetch<HealthResponse>('/v1/health')
};

export const usersApi = {
  me: () => apiFetch<UserProfile>('/v1/me')
};

export const recommendationsApi = {
  generate: (body: GenerateRecommendationRequest) =>
    apiFetch<GenerateRecommendationResponse>('/v1/recommendations/generate', {
      method: 'POST',
      body: JSON.stringify(body)
    })
};

export const ingestionApi = {
  getMonitoringStatus: () => apiFetch<MonitoringStatus>('/v1/ingestion/monitoring/status'),
  listJobs: () => apiFetch<IngestionJob[]>('/v1/ingestion/jobs'),
  trigger: (body: { source: 'kosis' | 'kdca' | 'full'; year?: number }) =>
    apiFetch<{ job_id: string; message: string }>('/v1/ingestion/jobs/trigger', {
      method: 'POST',
      body: JSON.stringify(body)
    })
};

export const publicDataApi = {
  listRegions: () => apiFetch<Region[]>('/v1/public-data/regions'),
  getCancerStats: (region_code: string, cancer_type: string, year?: number) => {
    const params = new URLSearchParams({ region_code, cancer_type });
    if (year) params.set('year', String(year));
    return apiFetch<CancerStats>(`/v1/public-data/cancer-stats?${params}`);
  }
};

export const literatureApi = {
  listPapers: () => apiFetch<PaperSummary[]>('/v1/literature/papers'),
  getIngestionStatus: () => apiFetch<IngestionStatus>('/v1/literature/ingestion/status'),
  ingestText: (body: { external_id: string; title: string; text: string }) =>
    apiFetch<PaperSummary>('/v1/literature/papers/ingest-text', {
      method: 'POST',
      body: JSON.stringify(body)
    }),
  uploadPdf: async (file: File, external_id: string, title: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('external_id', external_id);
    form.append('title', title);
    const res = await fetch(`${API_BASE}/v1/literature/papers/upload`, {
      method: 'POST',
      body: form
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<PaperSummary>;
  },
  ragQuery: (body: {
    query: string;
    cancer_type?: string;
    biomarker_name?: string;
    top_k?: number;
  }) =>
    apiFetch<RagQueryResult>('/v1/literature/rag/query', {
      method: 'POST',
      body: JSON.stringify(body)
    }),
  ragEvaluate: (body: { query: string; expected_terms: string[]; top_k?: number }) =>
    apiFetch<RagEvalResult>('/v1/literature/rag/evaluate', {
      method: 'POST',
      body: JSON.stringify(body)
    }),
  listEvaluations: () =>
    apiFetch<Array<RagEvalResult & { expected_terms: string[] }>>('/v1/literature/rag/evaluations')
};
