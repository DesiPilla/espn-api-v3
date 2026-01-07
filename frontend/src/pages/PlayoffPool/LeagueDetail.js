import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const LeagueDetail = () => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const { user } = usePlayoffPoolAuth();
  
  const [league, setLeague] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (leagueId) {
      loadLeagueData();
    }
  }, [leagueId]);

  const loadLeagueData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [leagueData, membersData] = await Promise.all([
        playoffPoolAPI.getLeague(leagueId),
        playoffPoolAPI.getLeagueMembers(leagueId)
      ]);
      
      setLeague(leagueData);
      setMembers(membersData);
    } catch (err) {
      setError('Failed to load league data');
      console.error('Error loading league:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartDraft = () => {
    navigate(`/playoff-pool/league/${leagueId}/draft`);
  };

  const handleViewDraftedTeams = () => {
    navigate(`/playoff-pool/league/${leagueId}/teams`);
  };

  const handleBackToDashboard = () => {
    navigate('/playoff-pool');
  };

  const isAdmin = league?.user_membership?.is_admin;
  const canStartDraft = isAdmin && !league?.is_draft_complete && !league?.draft_started_at;
  const draftInProgress = league?.draft_started_at && !league?.is_draft_complete;
  const draftComplete = league?.is_draft_complete;

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center">
          <div className="text-lg">Loading league...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button
          onClick={handleBackToDashboard}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={handleBackToDashboard}
            className="mb-4 text-blue-600 hover:text-blue-800"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{league?.name}</h1>
          <p className="text-gray-600">Created by {league?.created_by?.username}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* League Info */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow-md rounded-lg p-6 mb-6">
              <h2 className="text-xl font-bold mb-4">League Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-gray-700">Teams</h3>
                  <p className="text-gray-600">{members.length} / {league?.num_teams}</p>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700">Status</h3>
                  <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    draftComplete
                      ? 'bg-green-100 text-green-800'
                      : draftInProgress
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {draftComplete
                      ? 'Draft Complete'
                      : draftInProgress
                      ? 'Draft In Progress'
                      : 'Draft Not Started'
                    }
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700">Positions</h3>
                  <p className="text-gray-600">
                    {Array.isArray(league?.positions_included) 
                      ? league.positions_included.join(', ')
                      : 'Not configured'
                    }
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700">Created</h3>
                  <p className="text-gray-600">
                    {league?.created_at ? new Date(league.created_at).toLocaleDateString() : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-white shadow-md rounded-lg p-6 mb-6">
              <h2 className="text-xl font-bold mb-4">Actions</h2>
              <div className="flex flex-wrap gap-4">
                {canStartDraft && (
                  <button
                    onClick={handleStartDraft}
                    className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                  >
                    Start Draft
                  </button>
                )}
                
                {(draftInProgress && isAdmin) && (
                  <button
                    onClick={handleStartDraft}
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                  >
                    Manage Draft
                  </button>
                )}
                
                {draftComplete && (
                  <button
                    onClick={handleViewDraftedTeams}
                    className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
                  >
                    View Drafted Teams
                  </button>
                )}
                
                {!draftComplete && !draftInProgress && members.length < league?.num_teams && (
                  <div className="text-gray-600">
                    Waiting for more members to join...
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Members */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">League Members</h2>
              <div className="space-y-3">
                {members.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <div className="font-semibold">{member.user.username}</div>
                      <div className="text-sm text-gray-600">{member.team_name}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {member.is_admin && (
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                          Admin
                        </span>
                      )}
                      {member.user.id === user?.id && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                          You
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Empty slots */}
                {Array.from({ length: (league?.num_teams || 0) - members.length }).map((_, index) => (
                  <div key={`empty-${index}`} className="flex items-center p-3 bg-gray-100 rounded">
                    <div className="text-gray-400">Empty slot</div>
                  </div>
                ))}
              </div>
              
              {members.length < league?.num_teams && (
                <div className="mt-4 text-center">
                  <p className="text-sm text-gray-600 mb-2">
                    {(league?.num_teams || 0) - members.length} slots remaining
                  </p>
                  <button
                    onClick={() => {
                      // TODO: Implement invite/join functionality
                      alert('Invite functionality coming soon!');
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Invite Friends
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeagueDetail;