import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from './RegisterPage';
import { useAuth } from '../components/AuthContext';

jest.mock('../components/AuthContext');

const renderRegisterPage = (authOverrides = {}) => {
  useAuth.mockReturnValue({
    register: jest.fn().mockResolvedValue({ success: true }),
    loading: false,
    error: null,
    clearError: jest.fn(),
    ...authOverrides,
  });
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>
  );
};

describe('RegisterPage', () => {
  test('renders the form with heading and submit button', () => {
    renderRegisterPage();
    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  test('displays error message from auth context', () => {
    renderRegisterPage({ error: 'A user with that email already exists.' });
    expect(screen.getByText('A user with that email already exists.')).toBeInTheDocument();
  });

  test('disables submit button while loading', () => {
    renderRegisterPage({ loading: true });
    expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();
  });

  test('calls register() with email, password, and confirm password on submit', async () => {
    const mockRegister = jest.fn().mockResolvedValue({ success: true });
    const { container } = renderRegisterPage({ register: mockRegister });

    userEvent.type(screen.getByRole('textbox'), 'newuser@example.com');
    const [passwordInput, confirmInput] = container.querySelectorAll('input[type="password"]');
    userEvent.type(passwordInput, 'StrongPass123!');
    userEvent.type(confirmInput, 'StrongPass123!');
    userEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() =>
      expect(mockRegister).toHaveBeenCalledWith(
        'newuser@example.com',
        'StrongPass123!',
        'StrongPass123!'
      )
    );
  });

  test('has a link back to the login page', () => {
    renderRegisterPage();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });
});
