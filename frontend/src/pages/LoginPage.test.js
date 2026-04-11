import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from './LoginPage';
import { useAuth } from '../components/AuthContext';

jest.mock('../components/AuthContext');

const renderLoginPage = (authOverrides = {}) => {
  useAuth.mockReturnValue({
    login: jest.fn().mockResolvedValue({ success: true }),
    loading: false,
    error: null,
    clearError: jest.fn(),
    ...authOverrides,
  });
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
};

describe('LoginPage', () => {
  test('renders the form with heading and submit button', () => {
    renderLoginPage();
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('displays error message from auth context', () => {
    renderLoginPage({ error: 'Invalid credentials.' });
    expect(screen.getByText('Invalid credentials.')).toBeInTheDocument();
  });

  test('disables submit button while loading', () => {
    renderLoginPage({ loading: true });
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
  });

  test('calls login() with the entered email and password on submit', async () => {
    const mockLogin = jest.fn().mockResolvedValue({ success: true });
    const { container } = renderLoginPage({ login: mockLogin });

    userEvent.type(screen.getByRole('textbox'), 'user@example.com');
    userEvent.type(container.querySelector('input[type="password"]'), 'mypassword');
    userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith('user@example.com', 'mypassword')
    );
  });

  test('has a link to the forgot password page', () => {
    renderLoginPage();
    expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument();
  });

  test('has a link to the register page', () => {
    renderLoginPage();
    expect(screen.getByRole('link', { name: /register/i })).toBeInTheDocument();
  });
});
