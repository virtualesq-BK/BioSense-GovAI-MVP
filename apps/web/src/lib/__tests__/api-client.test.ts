import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const getSession = vi.fn();

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({ auth: { getSession } })
}));

async function loadClient() {
  vi.resetModules();
  return import('../api-client');
}

function stubFetch(response: Partial<Response> & { jsonBody?: unknown }) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    text: async () => '',
    json: async () => response.jsonBody,
    ...response
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('api-client', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {});
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://api.test/');
    getSession.mockResolvedValue({ data: { session: null } });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it('sends the Supabase access token as a bearer header', async () => {
    getSession.mockResolvedValue({ data: { session: { access_token: 'tok123' } } });
    const fetchMock = stubFetch({ jsonBody: { status: 'ok' } });
    const { healthApi } = await loadClient();

    await healthApi.check();

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://api.test/v1/health');
    expect(init.headers.Authorization).toBe('Bearer tok123');
  });

  it('omits the Authorization header when signed out', async () => {
    const fetchMock = stubFetch({ jsonBody: [] });
    const { catalogApi } = await loadClient();

    await catalogApi.listCancers();

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it('throws the response body text on non-2xx responses', async () => {
    stubFetch({ ok: false, status: 403, text: async () => '{"detail":"Admin privileges required"}' });
    const { healthApi } = await loadClient();

    await expect(healthApi.check()).rejects.toThrow('Admin privileges required');
  });

  it('falls back to a status message when the error body is empty', async () => {
    stubFetch({ ok: false, status: 500, text: async () => '' });
    const { healthApi } = await loadClient();

    await expect(healthApi.check()).rejects.toThrow('API error 500');
  });
});
