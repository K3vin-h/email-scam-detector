import { api } from '../../api/client.js';

const mockJson = (data, status = 200) => ({
  ok: status < 400,
  status,
  json: async () => data,
});

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
  Object.defineProperty(document, 'cookie', {
    writable: true,
    value: 'csrftoken=test-csrf-token',
  });
});

afterEach(() => vi.unstubAllGlobals());

describe('api.getStats (GET)', () => {
  it('calls /api/stats/ with credentials: include', async () => {
    fetch.mockResolvedValueOnce(mockJson({ total_scanned: 5 }));
    await api.getStats();
    expect(fetch).toHaveBeenCalledWith(
      '/api/stats/',
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('does not include X-CSRFToken header on GET', async () => {
    fetch.mockResolvedValueOnce(mockJson({}));
    await api.getStats();
    const [, opts] = fetch.mock.calls[0];
    expect(opts.headers['X-CSRFToken']).toBeUndefined();
  });

  it('returns parsed JSON body', async () => {
    fetch.mockResolvedValueOnce(mockJson({ total_scanned: 42 }));
    const result = await api.getStats();
    expect(result.total_scanned).toBe(42);
  });
});

describe('api.triggerScan (POST)', () => {
  it('includes X-CSRFToken header from cookie', async () => {
    fetch.mockResolvedValueOnce(mockJson({ scanned: 10, new: 2, scams_found: 1 }));
    await api.triggerScan();
    const [, opts] = fetch.mock.calls[0];
    expect(opts.headers['X-CSRFToken']).toBe('test-csrf-token');
  });

  it('sends method: POST', async () => {
    fetch.mockResolvedValueOnce(mockJson({ scanned: 0, new: 0, scams_found: 0 }));
    await api.triggerScan();
    const [, opts] = fetch.mock.calls[0];
    expect(opts.method).toBe('POST');
  });
});

describe('api.patchSettings (PATCH)', () => {
  it('serialises body as JSON', async () => {
    fetch.mockResolvedValueOnce(mockJson({ scan_window_days: 14 }));
    await api.patchSettings({ scan_window_days: 14 });
    const [, opts] = fetch.mock.calls[0];
    expect(JSON.parse(opts.body)).toEqual({ scan_window_days: 14 });
  });

  it('includes X-CSRFToken on PATCH', async () => {
    fetch.mockResolvedValueOnce(mockJson({}));
    await api.patchSettings({});
    const [, opts] = fetch.mock.calls[0];
    expect(opts.headers['X-CSRFToken']).toBe('test-csrf-token');
  });
});

describe('error handling', () => {
  it('throws NOT_AUTHENTICATED on 403', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 403 });
    await expect(api.getStats()).rejects.toMatchObject({
      message: 'NOT_AUTHENTICATED',
      status: 403,
    });
  });

  it('throws NOT_AUTHENTICATED on 401', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 401 });
    await expect(api.getSettings()).rejects.toMatchObject({ message: 'NOT_AUTHENTICATED' });
  });

  it('throws HTTP error for other 4xx/5xx responses', async () => {
    fetch.mockResolvedValueOnce({ ok: false, status: 500 });
    await expect(api.getStats()).rejects.toMatchObject({ message: 'HTTP_500' });
  });

  it('returns null for 204 No Content', async () => {
    fetch.mockResolvedValueOnce({ ok: true, status: 204 });
    const result = await api.getSettings();
    expect(result).toBeNull();
  });
});
