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
      gmail_id: 'msg1',
      sender: 'scammer@evil.com',
      subject: 'You won a prize!',
      snippet: 'Claim your reward now.',
      received_at: '2024-01-15T10:00:00Z',
      confidence: 0.97,
      is_scam: true,
      labeled_in_gmail: true,
    },
    {
      gmail_id: 'msg2',
      sender: 'friend@gmail.com',
      subject: 'Dinner tonight?',
      snippet: 'Are you free?',
      received_at: '2024-01-16T12:00:00Z',
      confidence: 0.08,
      is_scam: false,
      labeled_in_gmail: false,
    },
  ],
};

const renderPage = () =>
  render(<MemoryRouter><DashboardPage /></MemoryRouter>);

beforeEach(() => {
  api.getStats.mockResolvedValue(mockStats);
  api.getEmails.mockResolvedValue(mockEmailsPage);
});

describe('DashboardPage', () => {
  it('renders stat cards after loading', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('100')).toBeInTheDocument());
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
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

  it('shows Scam badge for scam emails and Legit for safe ones', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Scam')).toBeInTheDocument();
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

  it('filter "Scam only" refetches emails with is_scam=true', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Scam only')).toBeInTheDocument());

    api.getEmails.mockClear();
    fireEvent.click(screen.getByText('Scam only'));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(
      expect.objectContaining({ is_scam: 'true' })
    );
  });

  it('filter "Legit only" refetches with is_scam=false', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Legit only')).toBeInTheDocument());

    api.getEmails.mockClear();
    fireEvent.click(screen.getByText('Legit only'));
    await waitFor(() => expect(api.getEmails).toHaveBeenCalled());
    expect(api.getEmails).toHaveBeenLastCalledWith(
      expect.objectContaining({ is_scam: 'false' })
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
