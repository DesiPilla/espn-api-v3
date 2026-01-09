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
                      onClick={() =>
                          navigate(`/playoff-pool/league/${leagueId}`)
                      }
                      className="mb-4 text-blue-600 hover:text-blue-800"
                  >
                      ← Back to League
                  </button>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                      Drafted Teams
                  </h1>
                  <p className="text-gray-600">{league?.name}</p>
                  <div className="text-sm text-gray-500 mt-2">
                      {teamsData?.total_teams} teams •{" "}
                      {teamsData?.total_players} total players drafted
                  </div>
              </div>

              {/* Team Rosters Grid */}
              <div
                  style={{
                      display: "grid",
                      gridTemplateColumns:
                          "repeat(auto-fit, minmax(350px, 1fr))",
                      gap: "24px",
                  }}
              >
                  {teams.map((team) => (
                      <div
                          key={`${team.user?.id || "unclaimed"}-${
                              team.team_name
                          }`}
                          style={{
                              backgroundColor: "white",
                              boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                              border: "1px solid #e2e8f0",
                              borderRadius: "8px",
                              overflow: "hidden",
                          }}
                      >
                          {/* Team Header */}
                          <div
                              style={{
                                  backgroundColor: "#f8fafc",
                                  borderBottom: "1px solid #e2e8f0",
                                  padding: "16px 20px",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "18px",
                                      fontWeight: "600",
                                      color: "#1f2937",
                                      margin: "0 0 4px 0",
                                  }}
                              >
                                  {team.team_name}
                              </h3>
                              <div
                                  style={{
                                      display: "flex",
                                      justifyContent: "space-between",
                                      alignItems: "center",
                                  }}
                              >
                                  <div>
                                      <div
                                          style={{
                                              fontSize: "14px",
                                              color: "#6b7280",
                                          }}
                                      >
                                          {team.user?.username || "Unclaimed"}
                                          {team.user?.id === user?.id && (
                                              <span
                                                  style={{
                                                      marginLeft: "8px",
                                                      color: "#059669",
                                                      fontWeight: "500",
                                                  }}
                                              >
                                                  (You)
                                              </span>
                                          )}
                                      </div>
                                  </div>
                                  <div
                                      style={{
                                          textAlign: "right",
                                      }}
                                  >
                                      <div
                                          style={{
                                              fontSize: "16px",
                                              fontWeight: "600",
                                              color: "#1f2937",
                                          }}
                                      >
                                          {team.total_points.toFixed(1)} pts
                                      </div>
                                      <div
                                          style={{
                                              fontSize: "12px",
                                              color: "#6b7280",
                                          }}
                                      >
                                          {team.players.length} players
                                      </div>
                                  </div>
                              </div>
                          </div>

                          {/* Roster Table */}
                          <div style={{ padding: "16px 20px" }}>
                              <h4
                                  style={{
                                      fontSize: "14px",
                                      fontWeight: "600",
                                      color: "#374151",
                                      margin: "0 0 12px 0",
                                      borderBottom: "1px solid #e5e7eb",
                                      paddingBottom: "8px",
                                  }}
                              >
                                  Roster Breakdown
                              </h4>

                              {/* Table Headers */}
                              <div
                                  style={{
                                      display: "grid",
                                      gridTemplateColumns: "15% 55% 30%",
                                      backgroundColor: "#f1f5f9",
                                      borderRadius: "6px 6px 0 0",
                                      border: "1px solid #e2e8f0",
                                      borderBottom: "none",
                                  }}
                              >
                                  <div
                                      style={{
                                          padding: "8px 12px",
                                          fontSize: "12px",
                                          fontWeight: "500",
                                          color: "#64748b",
                                          textTransform: "uppercase",
                                          letterSpacing: "0.05em",
                                          textAlign: "center",
                                      }}
                                  >
                                      POS
                                  </div>
                                  <div
                                      style={{
                                          padding: "8px 12px",
                                          fontSize: "12px",
                                          fontWeight: "500",
                                          color: "#64748b",
                                          textTransform: "uppercase",
                                          letterSpacing: "0.05em",
                                      }}
                                  >
                                      PLAYER
                                  </div>
                                  <div
                                      style={{
                                          padding: "8px 12px",
                                          fontSize: "12px",
                                          fontWeight: "500",
                                          color: "#64748b",
                                          textTransform: "uppercase",
                                          letterSpacing: "0.05em",
                                          textAlign: "right",
                                      }}
                                  >
                                      POINTS
                                  </div>
                              </div>

                              {/* Table Rows */}
                              <div
                                  style={{
                                      border: "1px solid #e2e8f0",
                                      borderRadius: "0 0 6px 6px",
                                      backgroundColor: "white",
                                  }}
                              >
                                  {team.players
                                      .sort(
                                          (a, b) =>
                                              b.fantasy_points -
                                              a.fantasy_points
                                      )
                                      .map((player, index) => (
                                          <div
                                              key={player.id}
                                              style={{
                                                  display: "grid",
                                                  gridTemplateColumns:
                                                      "15% 55% 30%",
                                                  borderBottom:
                                                      index <
                                                      team.players.length - 1
                                                          ? "1px solid #f1f5f9"
                                                          : "none",
                                                  alignItems: "center",
                                                  transition:
                                                      "background-color 0.15s",
                                              }}
                                              onMouseEnter={(e) =>
                                                  (e.currentTarget.style.backgroundColor =
                                                      "#f8fafc")
                                              }
                                              onMouseLeave={(e) =>
                                                  (e.currentTarget.style.backgroundColor =
                                                      "transparent")
                                              }
                                          >
                                              {/* Position with colored badge */}
                                              <div
                                                  style={{
                                                      textAlign: "center",
                                                      padding: "12px 8px",
                                                  }}
                                              >
                                                  <span
                                                      style={{
                                                          display:
                                                              "inline-block",
                                                          padding: "4px 8px",
                                                          borderRadius: "12px",
                                                          fontSize: "11px",
                                                          fontWeight: "600",
                                                          backgroundColor:
                                                              {
                                                                  QB: "#dbeafe",
                                                                  RB: "#dcfce7",
                                                                  WR: "#fef3c7",
                                                                  TE: "#f3e8ff",
                                                                  K: "#fee2e2",
                                                                  DST: "#e0f2fe",
                                                              }[
                                                                  player
                                                                      .position
                                                              ] || "#f1f5f9",
                                                          color:
                                                              {
                                                                  QB: "#1e40af",
                                                                  RB: "#166534",
                                                                  WR: "#92400e",
                                                                  TE: "#7c3aed",
                                                                  K: "#dc2626",
                                                                  DST: "#0369a1",
                                                              }[
                                                                  player
                                                                      .position
                                                              ] || "#64748b",
                                                      }}
                                                  >
                                                      {player.position}
                                                  </span>
                                              </div>

                                              {/* Player Name and NFL Team */}
                                              <div
                                                  style={{
                                                      padding: "12px 8px",
                                                  }}
                                              >
                                                  <div
                                                      style={{
                                                          fontSize: "14px",
                                                          fontWeight: "500",
                                                          color: "#1f2937",
                                                          marginBottom: "2px",
                                                      }}
                                                  >
                                                      {player.player_name}
                                                  </div>
                                                  <div
                                                      style={{
                                                          fontSize: "12px",
                                                          color: "#6b7280",
                                                      }}
                                                  >
                                                      {player.team}
                                                  </div>
                                              </div>

                                              {/* Points */}
                                              <div
                                                  style={{
                                                      textAlign: "right",
                                                      padding: "12px 8px",
                                                  }}
                                              >
                                                  <div
                                                      style={{
                                                          fontSize: "14px",
                                                          fontWeight: "500",
                                                          color: "#1f2937",
                                                      }}
                                                  >
                                                      {player.fantasy_points.toFixed(
                                                          1
                                                      )}
                                                  </div>
                                              </div>
                                          </div>
                                      ))}
                              </div>
                          </div>
                      </div>
                  ))}
              </div>
          </div>
      </div>
  );
};

export default DraftedTeams;