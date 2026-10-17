import { beforeEach, describe, expect, it, vi } from 'vitest';

const list = vi.fn();
const create = vi.fn();
const remove = vi.fn();

vi.mock('@/lib/api-client', () => ({ reportsApi: { list, create, remove } }));

const LEGACY_KEY = 'biosense-reports';

function stubLocalStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial));
  vi.stubGlobal('window', {});
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    removeItem: (k: string) => void store.delete(k),
    setItem: (k: string, v: string) => void store.set(k, v)
  });
  return store;
}

const serverRow = {
  id: 's1',
  created_at: '2026-01-01T00:00:00Z',
  input: { cancer_type: 'lung' },
  recommendations: []
};

describe('reports-store', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    list.mockResolvedValue([serverRow]);
    create.mockResolvedValue(serverRow);
  });

  it('maps server rows to SavedReport', async () => {
    stubLocalStorage();
    const { listReports } = await import('../reports-store');

    expect(await listReports()).toEqual([
      { id: 's1', createdAt: '2026-01-01T00:00:00Z', input: { cancer_type: 'lung' }, recommendations: [] }
    ]);
  });

  it('uploads legacy local reports oldest-first, then clears local storage', async () => {
    const legacy = [
      { id: 'new', createdAt: 'b', input: { n: 2 }, recommendations: [] },
      { id: 'old', createdAt: 'a', input: { n: 1 }, recommendations: [] }
    ];
    const store = stubLocalStorage({ [LEGACY_KEY]: JSON.stringify(legacy) });
    const { listReports } = await import('../reports-store');

    await listReports();

    expect(create.mock.calls.map((c) => c[0])).toEqual([{ n: 1 }, { n: 2 }]);
    expect(store.has(LEGACY_KEY)).toBe(false);
  });

  it('keeps local reports when the upload fails so nothing is lost', async () => {
    const legacy = [{ id: 'x', createdAt: 'a', input: {}, recommendations: [] }];
    const store = stubLocalStorage({ [LEGACY_KEY]: JSON.stringify(legacy) });
    create.mockRejectedValue(new Error('offline'));
    const { listReports } = await import('../reports-store');

    await listReports();

    expect(store.has(LEGACY_KEY)).toBe(true);
  });
});
