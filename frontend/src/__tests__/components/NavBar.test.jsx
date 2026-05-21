import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { NavBar } from '../../components/NavBar.jsx';
import { DEMO_KEY } from '../../hooks/useAuth.js';
import { api } from '../../api/client.js';

vi.mock('../../api/client.js');

describe('NavBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    api.getHealth.mockResolvedValue({ status: 'ok' });
    global.fetch = vi.fn(() => Promise.resolve({ ok: true }));
    delete window.location;
    window.location = { href: '' };
  });

  it('clears demo mode when signing out', async () => {
    localStorage.setItem(DEMO_KEY, 'true');

    render(<MemoryRouter><NavBar /></MemoryRouter>);
    fireEvent.click(screen.getByLabelText('Sign out'));

    expect(localStorage.getItem(DEMO_KEY)).toBeNull();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      '/admin/logout/',
      expect.objectContaining({ method: 'POST' })
    ));
  });
});
