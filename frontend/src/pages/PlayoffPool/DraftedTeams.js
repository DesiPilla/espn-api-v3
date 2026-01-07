import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const DraftedTeams = () => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const { user } = usePlayoffPoolAuth();
  
  const [league, setLeague] = useState(null);
  const [teamsData, setTeamsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTab, setSelectedTab] = useState('standings');

  useEffect(() => {
    if (leagueId) {
      loadData();
    }
  }, [leagueId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [leagueData, draftedData] = await Promise.all([
        playoffPoolAPI.getLeague(leagueId),
        playoffPoolAPI.getDraftedTeams(leagueId)
      ]);
      
      setLeague(leagueData);
      setTeamsData(draftedData);
    } catch (err) {
      setError('Failed to load teams data');
      console.error('Error loading teams:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPositionCounts = (players) => {
    const counts = {};
    players.forEach(player => {
      counts[player.position] = (counts[player.position] || 0) + 1;
    });
    return counts;
  };

  const getPositionTotals = (players) => {
    const totals = {};
    players.forEach(player => {
      totals[player.position] = (totals[player.position] || 0) + player.fantasy_points;
    });
    return totals;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center">
          <div className="text-lg">Loading drafted teams...</div>
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
          onClick={() => navigate(`/playoff-pool/league/${leagueId}`)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Back to League
        </button>
      </div>
    );
  }

  const teams = teamsData?.teams || [];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(`/playoff-pool/league/${leagueId}`)}
            className="mb-4 text-blue-600 hover:text-blue-800"
          >
            ← Back to League
          </button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Drafted Teams</h1>
          <p className="text-gray-600">{league?.name}</p>
          <div className="text-sm text-gray-500 mt-2">
            {teamsData?.total_teams} teams • {teamsData?.total_players} total players drafted
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setSelectedTab('standings')}
                className={`mr-8 py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'standings'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Standings
              </button>
              <button
                onClick={() => setSelectedTab('rosters')}
                className={`mr-8 py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'rosters'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Team Rosters
              </button>
              <button
                onClick={() => setSelectedTab('analysis')}
                className={`mr-8 py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'analysis'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Position Analysis
              </button>
            </nav>
          </div>
        </div>

        {/* Standings Tab */}
        {selectedTab === 'standings' && (
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Team Rankings</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Team
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Points
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Players
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {teams.map((team, index) => (
                    <tr key={`${team.user.id}-${team.team_name}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                          index === 0 ? 'bg-yellow-100 text-yellow-800' :
                          index === 1 ? 'bg-gray-100 text-gray-800' :
                          index === 2 ? 'bg-orange-100 text-orange-800' :
                          'bg-gray-50 text-gray-600'
                        }`}>
                          {index + 1}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">{team.team_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{team.user.username}</div>
                        {team.user.id === user?.id && (
                          <div className="text-xs text-green-600">Your team</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {team.total_points.toFixed(1)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm text-gray-900">{team.players.length}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Team Rosters Tab */}
        {selectedTab === 'rosters' && (
          <div className="space-y-6">
            {teams.map((team) => (
              <div key={`${team.user.id}-${team.team_name}`} className="bg-white shadow-md rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{team.team_name}</h3>
                      <p className="text-sm text-gray-600">
                        Owner: {team.user.username}
                        {team.user.id === user?.id && <span className="ml-2 text-green-600">(Your team)</span>}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">{team.total_points.toFixed(1)} pts</div>
                      <div className="text-sm text-gray-600">{team.players.length} players</div>
                    </div>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Pos</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Team</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Points</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {team.players
                        .sort((a, b) => b.fantasy_points - a.fantasy_points)
                        .map((player) => (
                          <tr key={player.id}>
                            <td className="px-4 py-2 text-sm font-medium text-gray-900">{player.player_name}</td>
                            <td className="px-4 py-2 text-sm text-gray-600">{player.position}</td>
                            <td className="px-4 py-2 text-sm text-gray-600">{player.team}</td>
                            <td className="px-4 py-2 text-sm text-gray-900 text-right">{player.fantasy_points.toFixed(1)}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Position Analysis Tab */}
        {selectedTab === 'analysis' && (
          <div className="bg-white shadow-md rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Position Analysis</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Team
                    </th>
                    {league?.positions_included?.map(pos => (
                      <th key={pos} className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {pos}
                      </th>
                    ))}
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {teams.map((team) => {
                    const positionTotals = getPositionTotals(team.players);
                    const positionCounts = getPositionCounts(team.players);
                    
                    return (
                      <tr key={`${team.user.id}-${team.team_name}`} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{team.team_name}</div>
                          <div className="text-sm text-gray-500">{team.user.username}</div>
                        </td>
                        {league?.positions_included?.map(pos => (
                          <td key={pos} className="px-3 py-4 whitespace-nowrap text-center">
                            <div className="text-sm font-medium text-gray-900">
                              {(positionTotals[pos] || 0).toFixed(1)}
                            </div>
                            <div className="text-xs text-gray-500">
                              ({positionCounts[pos] || 0} players)
                            </div>
                          </td>
                        ))}
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="text-sm font-medium text-gray-900">
                            {team.total_points.toFixed(1)}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DraftedTeams;