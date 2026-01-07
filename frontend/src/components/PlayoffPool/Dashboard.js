import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from './AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const Dashboard = () => {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { user, logout } = usePlayoffPoolAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadLeagues();
  }, []);

  const loadLeagues = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await playoffPoolAPI.getLeagues();
      setLeagues(data.results || data);
    } catch (err) {
      setError('Failed to load leagues');
      console.error('Error loading leagues:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleCreateLeague = () => {
    navigate('/playoff-pool/create-league');
  };

  const handleJoinLeague = () => {
    // TODO: Implement join league modal or navigation
    alert('Join league functionality coming soon!');
  };

  const handleLeagueClick = (leagueId) => {
    navigate(`/playoff-pool/league/${leagueId}`);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center">
          <div className="text-lg">Loading your leagues...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.display_name || user?.username}!
          </h1>
          <p className="text-gray-600 mt-2">Manage your playoff pool leagues</p>
        </div>
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
        >
          Logout
        </button>
      </div>

      {/* Action Buttons */}
      <div className="mb-8 flex flex-wrap gap-4">
        <button
          onClick={handleCreateLeague}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
        >
          Create New League
        </button>
        <button
          onClick={handleJoinLeague}
          className="bg-green-500 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg"
        >
          Join Existing League
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
          <button
            onClick={loadLeagues}
            className="ml-4 text-red-800 underline"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Leagues List */}
      <div className="bg-white shadow-md rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Your Leagues</h2>
        </div>
        
        {leagues.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <p className="text-lg mb-4">No leagues yet!</p>
            <p className="mb-4">Create or join a league to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {leagues.map((league) => (
              <div
                key={league.id}
                className="p-6 hover:bg-gray-50 cursor-pointer"
                onClick={() => handleLeagueClick(league.id)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {league.name}
                    </h3>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p>
                        <span className="font-medium">Teams:</span>{' '}
                        {league.member_count || 0} / {league.num_teams}
                      </p>
                      <p>
                        <span className="font-medium">Positions:</span>{' '}
                        {Array.isArray(league.positions_included) 
                          ? league.positions_included.join(', ') 
                          : 'Not configured'}
                      </p>
                      <p>
                        <span className="font-medium">Created:</span>{' '}
                        {new Date(league.created_at).toLocaleDateString()}
                      </p>
                      {league.user_membership && (
                        <p>
                          <span className="font-medium">Your Team:</span>{' '}
                          {league.user_membership.team_name}
                          {league.user_membership.is_admin && (
                            <span className="ml-2 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                              Admin
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="ml-4 flex flex-col items-end">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      league.is_draft_complete
                        ? 'bg-green-100 text-green-800'
                        : league.draft_started_at
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {league.is_draft_complete
                        ? 'Draft Complete'
                        : league.draft_started_at
                        ? 'Draft In Progress'
                        : 'Draft Not Started'
                      }
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;