import { renderHook, act, waitFor } from '@testing-library/react';
import { useSettings } from '../../hooks/useSettings.js';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const baseSettings = {
  scan_window_days: 7,
  scan_frequency_hours: 6,
  notify_frequency: 'daily',
  notify_via_email: false,
  notify_email_address: '',
};

describe('useSettings', () => {
  it('loads settings on mount', async () => {
    api.getSettings.mockResolvedValueOnce(baseSettings);
    const { result } = renderHook(() => useSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.settings).toEqual(baseSettings);
  });

  it('update calls patchSettings and updates local state', async () => {
    api.getSettings.mockResolvedValueOnce(baseSettings);
    const updated = { ...baseSettings, scan_window_days: 14 };
    api.patchSettings.mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => { await result.current.update({ scan_window_days: 14 }); });

    expect(api.patchSettings).toHaveBeenCalledWith({ scan_window_days: 14 });
    expect(result.current.settings.scan_window_days).toBe(14);
  });

  it('sets saveError when patchSettings fails', async () => {
    api.getSettings.mockResolvedValueOnce(baseSettings);
    api.patchSettings.mockRejectedValueOnce(new Error('HTTP_400'));

    const { result } = renderHook(() => useSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.update({}).catch(() => {});
    });
    expect(result.current.saveError).toBe('HTTP_400');
  });

  it('clears saveError on successful update', async () => {
    api.getSettings.mockResolvedValue(baseSettings);
    api.patchSettings
      .mockRejectedValueOnce(new Error('HTTP_400'))
      .mockResolvedValueOnce(baseSettings);

    const { result } = renderHook(() => useSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => { await result.current.update({}).catch(() => {}); });
    expect(result.current.saveError).toBe('HTTP_400');

    await act(async () => { await result.current.update({}); });
    expect(result.current.saveError).toBeNull();
  });

  it('sets error when getSettings fails', async () => {
    api.getSettings.mockRejectedValueOnce(new Error('NOT_AUTHENTICATED'));
    const { result } = renderHook(() => useSettings());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('NOT_AUTHENTICATED');
  });
});
