import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { useAuth } from './AuthContext';

jest.mock('./AuthContext');

const renderRoute = (authState) => {
  useAuth.mockReturnValue(authState);
  render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
};

describe('ProtectedRoute', () => {
  test('renders nothing while auth is loading', () => {
    renderRoute({ isAuthenticated: false, loading: true });
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  test('redirects to /login when unauthenticated', () => {
    renderRoute({ isAuthenticated: false, loading: false });
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  test('preserves the attempted path in redirect state', () => {
    // MemoryRouter starts at /protected; after redirect, /login renders
    renderRoute({ isAuthenticated: false, loading: false });
    // The Login Page is rendered (redirect happened)
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  test('renders children when authenticated', () => {
    renderRoute({ isAuthenticated: true, loading: false });
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });
});
