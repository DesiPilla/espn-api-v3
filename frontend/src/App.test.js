import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

jest.mock('./utils/google_analytics', () => ({
  initGoogleAnalytics: jest.fn(),
}));

beforeEach(() => {
  localStorage.clear();
  // AuthProvider calls /api/auth/me/ on mount when a token is stored.
  // With no token stored, fetch is never called, but we set a default mock
  // so any unexpected call fails loudly.
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    json: () => Promise.resolve({}),
  });
});

test('redirects to /login when unauthenticated', async () => {
  render(
    <MemoryRouter initialEntries={['/']}>
      <App />
    </MemoryRouter>
  );
  // ProtectedRoute at "/" redirects to "/login" once loading=false
  expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument();
});
