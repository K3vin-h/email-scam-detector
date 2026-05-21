import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../../pages/DashboardPage.jsx';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

const mockStats = {
  total_scanned: 100,
  total_scams: 20,
  scams_last_7_days: 5,
  scams_last_30_days: 15,
  top_scam_senders: [{ sender: 'spammer@evil.com', count: 3 }],
};

const mockEmailsPage = {
  count: 2,
  results: [
    {
      id: 1,
      gmail_id: 'msg1',
      sender: 'scammer@evil.com',
      subject: 'You won a prize!',
      snippet: 'Claim your reward now.',
      received_at: '2024-01-15T10:00:00Z',
      confidence: 0.97,
      is_scam: true,
      risk_level: 'scam',
      risk_label: 'Scam',
      labeled_in_gmail: true,
    },
    {
      id: 3,
      gmail_id: 'msg3',
      sender: 'notice@example.com',
      subject: 'Verify your login',
      snippet: 'Please review this sign-in.',
      received_at: '2024-01-16T10:00:00Z',
      confidence: 0.62,
      is_scam: false,
      risk_level: 'possible_scam',
      risk_label: 'Possible scam',
      labeled_in_gmail: false,
    },
    {
      id: 2,
      gmail_id: 'msg2',
      sender: 'friend@gmail.com',
      subject: 'Dinner tonight?',
      snippet: 'Are you free?',
      received_at: '2024-01-16T12:00:00Z',
      confidence: 0.08,
      is_scam: false,
      risk_level: 'legit',
      risk_label: 'Legit',
      labeled_in_gmail: false,
    },
  ],
};

const renderPage = () =>
  render(<MemoryRouter><DashboardPage /></MemoryRouter>);

beforeEach(() => {
  api.getHealth.mockResolvedValue({ status: 'ok' });
  api.getStats.mockResolvedValue(mockStats);
  api.getEmails.mockResolvedValue(mockEmailsPage);
});

describe('DashboardPage', () => {
  it('renders hero stats after loading', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('100')).toBeInTheDocument());
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('Total Scanned')).toBeInTheDocument();
    expect(screen.getByText('Scams Blocked')).toBeInTheDocument();
    expect(screen.getByText('Threat Ratio')).toBeInTheDocument();
  });

  it('renders email rows with sender names', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('scammer@evil.com')).toBeInTheDocument());
    expect(screen.getByText('friend@gmail.com')).toBeInTheDocument();
  });

  it('renders subjects', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('You won a prize!')).toBeInTheDocument());
  });

  it('shows Scam, Possible scam, and Legit badges', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Scam')).toBeInTheDocument();
      expect(screen.getByText('Possible scam')).toBeInTheDocument();
      expect(screen.getByText('Legit')).toBeInTheDocument();
    });
  });

  it('scan button calls triggerScan and shows result', async () => {
    api.triggerScan.mockResolvedValueOnce({ scanned: 50, new: 3, scams_found: 1 });
    renderPage();
    await waitFor(() => expect(screen.getByText('Scan Now')).toBeInTheDocument());

    fireEvent.click(screen.getByText('Scan Now'));
    await waitFor(() => expect(api.triggerScan).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText(/1 scam/)).toBeInTheDocument());
  });

  it('refreshes stats and emails after a successful scan', async () => {
    api.triggerScan.mockResolvedValueOnce({ scanned: 50, new: 3, scams_found: 1 });
    renderPage();
    await waitFor(() => expect(screen.getByText('Scan Now')).toBeInTheDocument());

    api.getStats.mockClear();
    api.getEmails.mockClear();
    fireEvent.click(screen.getByText('Scan Now'));

    await waitFor(() => expect(api.triggerScan).toHaveBeenCalled());
    expect(api.getStats).toHaveBeenCalledTimes(1);
    expect(api.getEmails).toHaveBeenCalledTimes(1);
  });

  it('manual correction marks an email as legit and refreshes data', async () => {
    api.correctEmailRisk.mockResolvedValueOnce({ risk_level: 'legit', risk_label: 'Legit' });
    renderPage();
    await waitFor(() => expect(screen.getByLabelText('Change risk for You won a prize!: Scam')).toBeInTheDocument());

    api.getStats.mockClear();
    api.getEmails.mockClear();
    fireEvent.click(screen.getByLabelText('Change risk for You won a prize!: Scam'));
    await waitFor(() => expect(screen.getByLabelText('Mark You won a prize! as Legit')).toBeInTheDocument());
    fireEvent.click(screen.getByLabelText('Mark You won a prize! as Legit'));

    await waitFor(() => expect(api.correctEmailRisk).toHaveBeenCalledWith(1, 'legit'));
    expect(api.getStats).toHaveBeenCalledTimes(1);
    expect(api.getEmails).toHaveBeenCalledTimes(1);
  });

  it('filter "Scam" refetches emails with risk_level=scam', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Scam' })).toBeInTheDocument());

    api.getEmails.mockClear();
    fireEvent.click(screen.getByRole('button', { name: 'Scam' }));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(
      expect.objectContaining({ risk_level: 'scam' })
    );
  });

  it('filter "Possible scam" refetches with risk_level=possible_scam', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Possible scam' })).toBeInTheDocument());

    api.getEmails.mockClear();
    fireEvent.click(screen.getByRole('button', { name: 'Possible scam' }));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(
      expect.objectContaining({ risk_level: 'possible_scam' })
    );
  });

  it('filter "Legit" refetches with risk_level=legit', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Legit' })).toBeInTheDocument());

    api.getEmails.mockClear();
    fireEvent.click(screen.getByRole('button', { name: 'Legit' }));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(
      expect.objectContaining({ risk_level: 'legit' })
    );
  });

  it('shows empty state when no emails returned', async () => {
    api.getEmails.mockResolvedValueOnce({ count: 0, results: [] });
    renderPage();
    await waitFor(() =>
      expect(screen.getByText(/No emails found/)).toBeInTheDocument()
    );
  });
});
