import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { SettingsPage } from '../../pages/SettingsPage.jsx';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const baseSettings = {
  scan_window_days: 7,
  scan_frequency_hours: 6,
  notify_frequency: 'daily',
  notify_via_email: false,
  notify_email_address: '',
};

const renderPage = (path = '/settings') =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  api.getSettings.mockResolvedValue(baseSettings);
  api.patchSettings.mockResolvedValue(baseSettings);
});

describe('SettingsPage', () => {
  it('pre-populates scan_window_days from settings', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('7')).toBeInTheDocument());
  });

  it('pre-populates scan_frequency_hours from settings', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('6')).toBeInTheDocument());
  });

  it('shows Gmail connected banner when ?connected=true', async () => {
    renderPage('/settings?connected=true');
    await waitFor(() =>
      expect(screen.getByText(/Gmail connected successfully/i)).toBeInTheDocument()
    );
  });

  it('does not show banner without ?connected=true', async () => {
    renderPage('/settings');
    await waitFor(() => expect(api.getSettings).toHaveBeenCalled());
    expect(screen.queryByText(/Gmail connected successfully/i)).not.toBeInTheDocument();
  });

  it('does not render notify_email_address when notify_via_email is false', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('7')).toBeInTheDocument());
    expect(screen.queryByLabelText(/Notification email/i)).not.toBeInTheDocument();
  });

  it('shows notify_email_address input when notify_via_email is true', async () => {
    api.getSettings.mockResolvedValueOnce({ ...baseSettings, notify_via_email: true });
    renderPage();
    await waitFor(() =>
      expect(screen.getByLabelText(/Notification email/i)).toBeInTheDocument()
    );
  });

  it('submitting calls patchSettings with form values', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('7')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /save settings/i }));
    await waitFor(() => expect(api.patchSettings).toHaveBeenCalled());
  });

  it('shows saved confirmation after successful save', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('7')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /save settings/i }));
    await waitFor(() => expect(screen.getByText(/Settings saved/i)).toBeInTheDocument());
  });

  it('shows error message when save fails', async () => {
    api.patchSettings.mockRejectedValueOnce(new Error('HTTP_400'));
    renderPage();
    await waitFor(() => expect(screen.getByDisplayValue('7')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /save settings/i }));
    await waitFor(() => expect(screen.getByText(/Failed to save settings/i)).toBeInTheDocument());
  });

  it('contains Connect Gmail link', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText(/Connect Gmail/i)).toBeInTheDocument());
  });
});
