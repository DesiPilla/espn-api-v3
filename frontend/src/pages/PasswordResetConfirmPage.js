import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

const PasswordResetConfirmPage = () => {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid') || '';
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!uid || !token) {
    return (
      <div style={{ maxWidth: 400, margin: '60px auto', padding: '0 16px' }}>
        <h1>Invalid link</h1>
        <p>This password reset link is invalid or has expired.</p>
        <Link to="/password-reset">Request a new link</Link>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch('/api/auth/password-reset/confirm/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid, token, new_password: newPassword }),
      });
      const data = await response.json();
      if (response.ok) {
        setSuccess(true);
      } else {
        const msg = Array.isArray(data.error)
          ? data.error.join(' ')
          : data.error || 'Failed to reset password.';
        setError(msg);
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div style={{ maxWidth: 400, margin: '60px auto', padding: '0 16px' }}>
        <h1>Password reset</h1>
        <p>Your password has been reset. You can now sign in with your new password.</p>
        <Link to="/login">Sign in</Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 400, margin: '60px auto', padding: '0 16px' }}>
      <h1>Set new password</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <label>New password</label>
          <br />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoFocus
            style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>Confirm new password</label>
          <br />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ width: '100%', padding: '10px' }}>
          {loading ? 'Resetting…' : 'Reset password'}
        </button>
      </form>
    </div>
  );
};

export default PasswordResetConfirmPage;
