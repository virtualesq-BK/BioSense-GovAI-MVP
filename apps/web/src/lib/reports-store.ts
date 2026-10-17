import {
  reportsApi,
  type GenerateRecommendationRequest,
  type SensorRecommendation,
  type ServerReport
} from '@/lib/api-client';

export type SavedReport = {
  id: string;
  createdAt: string;
  input: GenerateRecommendationRequest;
  recommendations: SensorRecommendation[];
};

const LEGACY_STORAGE_KEY = 'biosense-reports';

function fromServer(r: ServerReport): SavedReport {
  return {
    id: r.id,
    createdAt: r.created_at,
    input: r.input,
    recommendations: r.recommendations
  };
}

function readLegacyReports(): SavedReport[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(LEGACY_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedReport[]) : [];
  } catch {
    return [];
  }
}

/** One-time upload of reports saved in this browser before server storage existed. */
async function migrateLegacyReports(): Promise<void> {
  const legacy = readLegacyReports();
  if (!legacy.length) return;
  try {
    // Oldest first so the server's created_at ordering keeps their relative order.
    for (const r of [...legacy].reverse()) {
      await reportsApi.create(r.input, r.recommendations);
    }
    localStorage.removeItem(LEGACY_STORAGE_KEY);
  } catch {
    // Keep local copies; migration is retried on the next visit.
  }
}

export async function listReports(): Promise<SavedReport[]> {
  await migrateLegacyReports();
  return (await reportsApi.list()).map(fromServer);
}

export async function saveReport(
  input: GenerateRecommendationRequest,
  recommendations: SensorRecommendation[]
): Promise<SavedReport> {
  return fromServer(await reportsApi.create(input, recommendations));
}

export async function deleteReport(id: string): Promise<void> {
  await reportsApi.remove(id);
}
