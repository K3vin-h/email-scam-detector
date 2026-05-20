import { renderHook, waitFor } from '@testing-library/react';
import { useAuth } from '../../hooks/useAuth.js';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const mockSettings = { scan_window_days: 7, scan_frequency_hours: 6, notify_frequency: 'daily', notify_via_email: false, notify_email_address: '' };

describe('useAuth', () => {
  it('starts in loading state', () => {
    api.getSettings.mockResolvedValueOnce(mockSettings);
    const { result } = renderHook(() => useAuth());
    expect(result.current.loading).toBe(true);
  });

  it('sets authenticated=true when getSettings resolves', async () => {
    api.getSettings.mockResolvedValueOnce(mockSettings);
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.authenticated).toBe(true);
  });

  it('sets authenticated=false when getSettings throws NOT_AUTHENTICATED', async () => {
    api.getSettings.mockRejectedValueOnce(
      Object.assign(new Error('NOT_AUTHENTICATED'), { status: 403 })
    );
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.authenticated).toBe(false);
  });

  it('sets authenticated=false on any API error', async () => {
    api.getSettings.mockRejectedValueOnce(new Error('HTTP_500'));
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.authenticated).toBe(false);
  });
});
