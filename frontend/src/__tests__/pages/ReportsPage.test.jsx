import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ReportsPage } from '../../pages/ReportsPage.jsx';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const mockReports = {
  count: 2,
  results: [
    {
      period: 'daily',
      generated_at: '2024-01-15T23:59:00Z',
      total_scams: 4,
      top_senders: [{ sender: 'spam@bad.com', count: 2 }],
    },
    {
      period: 'daily',
      generated_at: '2024-01-16T23:59:00Z',
      total_scams: 1,
      top_senders: [],
    },
  ],
};

const renderPage = () =>
  render(<MemoryRouter><ReportsPage /></MemoryRouter>);

beforeEach(() => {
  api.getHealth.mockResolvedValue({ status: 'ok' });
  api.getReports.mockResolvedValue(mockReports);
  api.getStats.mockResolvedValue({ total_scanned: 10, total_scams: 5, scams_last_7_days: 3, scams_last_30_days: 5 });
  api.getDailyStats.mockResolvedValue([]);
  api.getSenderStats.mockResolvedValue({ most_impersonated: 'paypal.com', highest_risk_sender: 'scam@bad.com', scam_trend_pct: 10 });
});

describe('ReportsPage', () => {
  it('renders report cards with scam counts', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('4')).toBeInTheDocument());
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders top sender in report card', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('spam@bad.com')).toBeInTheDocument());
  });

  it('initially fetches all reports (no period filter)', async () => {
    renderPage();
    await waitFor(() => expect(api.getReports).toHaveBeenCalledWith(''));
  });

  it('clicking Weekly calls getReports with period=weekly', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Weekly')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Weekly'));
    await waitFor(() =>
      expect(api.getReports).toHaveBeenCalledWith('weekly')
    );
    expect(screen.getByText('Weekly')).toHaveAttribute('aria-pressed', 'true');
  });

  it('clicking Monthly calls getReports with period=monthly', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Monthly')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Monthly'));
    await waitFor(() => expect(api.getReports).toHaveBeenCalledWith('monthly'));
    expect(screen.getByText('Monthly')).toHaveAttribute('aria-pressed', 'true');
  });

  it('clicking All returns to unfiltered reports', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Weekly')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Weekly'));
    await waitFor(() => expect(api.getReports).toHaveBeenCalledWith('weekly'));

    fireEvent.click(screen.getByText('All'));
    await waitFor(() => expect(api.getReports).toHaveBeenCalledWith(''));
    expect(screen.getByText('All')).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows empty state when no reports', async () => {
    api.getReports.mockResolvedValueOnce({ count: 0, results: [] });
    renderPage();
    await waitFor(() => expect(screen.getByText(/No reports yet/)).toBeInTheDocument());
  });

  it('shows error state on API failure', async () => {
    api.getReports.mockRejectedValueOnce(new Error('HTTP_500'));
    renderPage();
    await waitFor(() => expect(screen.getByText(/Failed to load reports/)).toBeInTheDocument());
  });
});
