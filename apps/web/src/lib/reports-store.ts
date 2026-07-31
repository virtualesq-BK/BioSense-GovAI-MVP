import type { GenerateRecommendationRequest, SensorRecommendation } from '@/lib/api-client';

export type SavedReport = {
  id: string;
  createdAt: string;
  input: GenerateRecommendationRequest;
  recommendations: SensorRecommendation[];
};

const STORAGE_KEY = 'biosense-reports';

export function listReports(): SavedReport[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedReport[]) : [];
  } catch {
    return [];
  }
}

export function saveReport(
  input: GenerateRecommendationRequest,
  recommendations: SensorRecommendation[]
): SavedReport {
  const report: SavedReport = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    input,
    recommendations
  };
  const existing = listReports();
  const next = [report, ...existing].slice(0, 50);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return report;
}

export function deleteReport(id: string) {
  const next = listReports().filter((r) => r.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}

export function getReport(id: string): SavedReport | undefined {
  return listReports().find((r) => r.id === id);
}
