import React, { useState } from 'react';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import LoginForm from '../../components/PlayoffPool/LoginForm';
import RegisterForm from '../../components/PlayoffPool/RegisterForm';
import Dashboard from '../../components/PlayoffPool/Dashboard';

const PlayoffPoolHome = () => {
  const { isAuthenticated, loading } = usePlayoffPoolAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center">
          <div className="text-lg">Loading...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="container mx-auto px-4">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              NFL Playoff Pool
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Draft players from playoff teams and compete with your friends!
            </p>
          </div>
          
          <div className="max-w-md mx-auto">
            {showRegister ? (
              <div>
                <RegisterForm />
                <div className="text-center mt-4">
                  <button
                    onClick={() => setShowRegister(false)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Already have an account? Sign in
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <LoginForm />
                <div className="text-center mt-4">
                  <button
                    onClick={() => setShowRegister(true)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Need an account? Register
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Dashboard />
    </div>
  );
};

export default PlayoffPoolHome;