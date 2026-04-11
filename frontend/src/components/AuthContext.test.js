import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';

// Minimal consumer that exposes auth state and actions for testing
const AuthConsumer = () => {
  const { isAuthenticated, loading, user, error, login, logout, register } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="user">{user?.email ?? 'none'}</span>
      {error && <span data-testid="error">{error}</span>}
      <button onClick={() => login('test@example.com', 'pass123')}>Login</button>
      <button onClick={logout}>Logout</button>
      <button onClick={() => register('new@example.com', 'Pass123!', 'Pass123!')}>Register</button>
    </div>
  );
};

const renderProvider = () => render(<AuthProvider><AuthConsumer /></AuthProvider>);

beforeEach(() => {
  localStorage.clear();
  global.fetch = jest.fn();
});

// ── Initialization ────────────────────────────────────────────────────────────

describe('initialization', () => {
  test('sets loading=false and stays unauthenticated when no token is stored', async () => {
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(fetch).not.toHaveBeenCalled();
  });

  test('authenticates from stored token by validating with /api/auth/me/', async () => {
    localStorage.setItem('doritostatsToken', 'stored-token');
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: 1, email: 'stored@example.com' }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    );
    expect(screen.getByTestId('user')).toHaveTextContent('stored@example.com');
    expect(fetch).toHaveBeenCalledWith(
      '/api/auth/me/',
      expect.objectContaining({ headers: { Authorization: 'Token stored-token' } })
    );
  });

  test('clears an expired stored token and stays unauthenticated', async () => {
    localStorage.setItem('doritostatsToken', 'expired-token');
    fetch.mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({}) });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(localStorage.getItem('doritostatsToken')).toBeNull();
  });
});

// ── login() ───────────────────────────────────────────────────────────────────

describe('login()', () => {
  test('on success: sets isAuthenticated=true and stores token in localStorage', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ token: 'new-token', user: { id: 2, email: 'test@example.com' } }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    userEvent.click(screen.getByText('Login'));
    await waitFor(() =>
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    );
    expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    expect(localStorage.getItem('doritostatsToken')).toBe('new-token');
  });

  test('on failure: sets error and stays unauthenticated', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ error: 'Invalid credentials.' }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    userEvent.click(screen.getByText('Login'));
    await waitFor(() =>
      expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials.')
    );
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });
});

// ── logout() ──────────────────────────────────────────────────────────────────

describe('logout()', () => {
  test('clears isAuthenticated and removes token from localStorage', async () => {
    localStorage.setItem('doritostatsToken', 'my-token');
    // /me succeeds → authenticated; /logout is fire-and-forget
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, email: 'test@example.com' }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    );
    userEvent.click(screen.getByText('Logout'));
    await waitFor(() =>
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
    );
    expect(localStorage.getItem('doritostatsToken')).toBeNull();
  });
});

// ── register() ────────────────────────────────────────────────────────────────

describe('register()', () => {
  test('on success: sets isAuthenticated=true and stores token', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ token: 'reg-token', user: { id: 3, email: 'new@example.com' } }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    userEvent.click(screen.getByText('Register'));
    await waitFor(() =>
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    );
    expect(localStorage.getItem('doritostatsToken')).toBe('reg-token');
  });

  test('on failure: sets error and stays unauthenticated', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ email: ['A user with that email already exists.'] }),
    });
    renderProvider();
    await waitFor(() =>
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    );
    userEvent.click(screen.getByText('Register'));
    await waitFor(() =>
      expect(screen.getByTestId('error')).toHaveTextContent(
        'A user with that email already exists.'
      )
    );
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
  });
});
