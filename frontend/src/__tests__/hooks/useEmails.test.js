import { renderHook, act, waitFor } from '@testing-library/react';
import { useEmails } from '../../hooks/useEmails.js';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const makeResponse = (results = []) => ({ count: results.length, results, next: null, previous: null });

beforeEach(() => {
  vi.clearAllMocks();
  api.getEmails.mockResolvedValue(makeResponse());
});

describe('useEmails', () => {
  it('fetches emails on mount with page=1', async () => {
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(api.getEmails).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));
  });

  it('exposes emails and count from response', async () => {
    const emails = [{ gmail_id: '1', is_scam: true }];
    api.getEmails.mockResolvedValueOnce(makeResponse(emails));
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.emails).toEqual(emails);
    expect(result.current.count).toBe(1);
  });

  it('includes risk_level param when filter is set', async () => {
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));

    api.getEmails.mockClear();
    act(() => result.current.changeFilter('possible_scam'));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(expect.objectContaining({ risk_level: 'possible_scam' }));
  });

  it('omits risk_level param when filter is empty string', async () => {
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));
    const lastParams = api.getEmails.mock.calls.at(-1)[0];
    expect(lastParams.risk_level).toBeUndefined();
  });

  it('resets to page 1 when changeFilter is called', async () => {
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));
    act(() => result.current.setPage(3));
    act(() => result.current.changeFilter('legit'));
    expect(result.current.page).toBe(1);
  });

  it('sets error state on API failure', async () => {
    api.getEmails.mockRejectedValueOnce(new Error('HTTP_500'));
    const { result } = renderHook(() => useEmails());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('HTTP_500');
  });
});
