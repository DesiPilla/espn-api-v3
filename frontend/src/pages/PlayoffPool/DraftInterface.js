import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const DraftInterface = () => {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  const [league, setLeague] = useState(null);
  const [members, setMembers] = useState([]);
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [draftedPlayers, setDraftedPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [filterPosition, setFilterPosition] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [playersPerPage] = useState(15);
  const [loading, setLoading] = useState(true);
  const [draftLoading, setDraftLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (leagueId) {
      loadDraftData();
    }
  }, [leagueId]);

  const loadDraftData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [leagueData, membersData, playersData] = await Promise.all([
        playoffPoolAPI.getLeague(leagueId),
        playoffPoolAPI.getLeagueMembers(leagueId),
        playoffPoolAPI.getAvailablePlayers(leagueId)
      ]);
      
      setLeague(leagueData);
      setMembers(membersData);
      setAvailablePlayers(playersData);

      // Load drafted teams data to show current picks
      try {
        const teamsData = await playoffPoolAPI.getDraftedTeams(leagueId);
        const allDrafted = [];
        teamsData.teams.forEach(team => {
          team.players.forEach(player => allDrafted.push(player));
        });
        setDraftedPlayers(allDrafted);
      } catch (err) {
        console.warn('No drafted players yet');
      }
      
    } catch (err) {
      setError('Failed to load draft data');
      console.error('Error loading draft data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDraftPlayer = async () => {
    if (!selectedPlayer || !selectedUser) {
      alert('Please select both a player and a team');
      return;
    }

    try {
      setDraftLoading(true);
      
      await playoffPoolAPI.draftPlayer(leagueId, selectedPlayer.player_id, selectedUser.user.id);
      
      // Reload draft data to update UI
      await loadDraftData();
      
      // Clear selections
      setSelectedPlayer(null);
      setSelectedUser(null);
      
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to draft player');
      console.error('Error drafting player:', err);
    } finally {
      setDraftLoading(false);
    }
  };

  const handleCompleteDraft = async () => {
    if (window.confirm('Are you sure you want to complete the draft? This action cannot be undone.')) {
      try {
        await playoffPoolAPI.completeDraft(leagueId);
        navigate(`/playoff-pool/league/${leagueId}/teams`);
      } catch (err) {
        alert('Failed to complete draft');
        console.error('Error completing draft:', err);
      }
    }
  };

  // Filter players based on position and search term
  const filteredPlayers = availablePlayers.filter(player => {
    const matchesPosition = filterPosition === 'ALL' || player.position === filterPosition;
    const matchesSearch = !searchTerm || 
      player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      player.team.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesPosition && matchesSearch;
  });

  // Pagination logic
  const totalPages = Math.ceil(filteredPlayers.length / playersPerPage);
  const startIndex = (currentPage - 1) * playersPerPage;
  const endIndex = startIndex + playersPerPage;
  const currentPlayers = filteredPlayers.slice(startIndex, endIndex);

  // Reset to page 1 when search or filter changes
  const handleSearchChange = (value) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handleFilterChange = (value) => {
    setFilterPosition(value);
    setCurrentPage(1);
  };

  const positions = ['ALL', ...new Set(availablePlayers.map(p => p.position))];
  const isAdmin = league?.user_membership?.is_admin;

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center">
          <div className="text-lg">Loading draft...</div>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Only league administrators can access the draft interface.
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

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button
          onClick={loadDraftData}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Try Again
        </button>
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Draft Interface</h1>
          <p className="text-gray-600">{league?.name}</p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Available Players */}
          <div className="xl:col-span-2">
            <div className="bg-white shadow-md rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Available Players</h2>
                <div className="text-sm text-gray-600">
                  Showing {startIndex + 1}-{Math.min(endIndex, filteredPlayers.length)} of {filteredPlayers.length} players
                </div>
              </div>

              {/* Filters */}
              <div className="mb-4 flex flex-wrap gap-4">
                <div>
                  <select
                    value={filterPosition}
                    onChange={(e) => handleFilterChange(e.target.value)}
                    className="border rounded px-3 py-2"
                  >
                    {positions.map(pos => (
                      <option key={pos} value={pos}>{pos}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search players or teams..."
                    value={searchTerm}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="border rounded px-3 py-2 w-full"
                  />
                </div>
              </div>

              {/* Players List */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left p-2">Player</th>
                      <th className="text-left p-2">Pos</th>
                      <th className="text-left p-2">Team</th>
                      <th className="text-right p-2">Fantasy Pts</th>
                      <th className="text-center p-2">Select</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentPlayers.map((player, index) => (
                      <tr
                        key={player.player_id}
                        className={`border-b hover:bg-gray-50 ${
                          selectedPlayer?.player_id === player.player_id ? 'bg-blue-50' : ''
                        }`}
                      >
                        <td className="p-2 font-medium">{player.name}</td>
                        <td className="p-2">{player.position}</td>
                        <td className="p-2">{player.team}</td>
                        <td className="p-2 text-right">{player.fantasy_points.toFixed(1)}</td>
                        <td className="p-2 text-center">
                          <button
                            onClick={() => setSelectedPlayer(player)}
                            className={`px-3 py-1 rounded text-xs ${
                              selectedPlayer?.player_id === player.player_id
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 hover:bg-gray-300'
                            }`}
                          >
                            {selectedPlayer?.player_id === player.player_id ? 'Selected' : 'Select'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex justify-center items-center mt-4 space-x-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {currentPage} of {totalPages}
                  </span>
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Draft Panel */}
          <div className="xl:col-span-1 space-y-6">
            {/* Selected Player */}
            <div className="bg-white shadow-md rounded-lg p-4">
              <h3 className="font-bold mb-2">Selected Player</h3>
              {selectedPlayer ? (
                <div className="bg-blue-50 p-3 rounded">
                  <div className="font-medium">{selectedPlayer.name}</div>
                  <div className="text-sm text-gray-600">
                    {selectedPlayer.position} - {selectedPlayer.team}
                  </div>
                  <div className="text-sm">{selectedPlayer.fantasy_points.toFixed(1)} pts</div>
                </div>
              ) : (
                <div className="text-gray-500 text-center py-4">
                  No player selected
                </div>
              )}
            </div>

            {/* Team Selection */}
            <div className="bg-white shadow-md rounded-lg p-4">
              <h3 className="font-bold mb-2">Draft To Team</h3>
              <div className="space-y-2">
                {members.map(member => (
                  <button
                    key={member.id}
                    onClick={() => setSelectedUser(member)}
                    className={`w-full text-left p-3 rounded border ${
                      selectedUser?.id === member.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="font-medium">{member.user.username}</div>
                    <div className="text-sm text-gray-600">{member.team_name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Draft Button */}
            <div className="bg-white shadow-md rounded-lg p-4">
              <button
                onClick={handleDraftPlayer}
                disabled={!selectedPlayer || !selectedUser || draftLoading}
                className={`w-full font-bold py-3 px-4 rounded ${
                  draftLoading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : selectedPlayer && selectedUser
                    ? 'bg-green-500 hover:bg-green-700 text-white'
                    : 'bg-gray-300 cursor-not-allowed text-gray-500'
                }`}
              >
                {draftLoading ? 'Drafting...' : 'Draft Player'}
              </button>

              <button
                onClick={handleCompleteDraft}
                className="w-full mt-3 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
              >
                Complete Draft
              </button>
            </div>

            {/* Recent Picks */}
            <div className="bg-white shadow-md rounded-lg p-4">
              <h3 className="font-bold mb-2">Recent Picks</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {draftedPlayers
                  .sort((a, b) => b.draft_order - a.draft_order)
                  .slice(0, 10)
                  .map((pick) => (
                    <div key={pick.id} className="text-sm p-2 bg-gray-50 rounded">
                      <div className="font-medium">{pick.player_name}</div>
                      <div className="text-gray-600">
                        {pick.position} → {pick.team_name}
                      </div>
                    </div>
                  ))}
                {draftedPlayers.length === 0 && (
                  <div className="text-gray-500 text-center py-4">
                    No picks yet
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DraftInterface;