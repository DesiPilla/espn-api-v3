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
  const [undoLoading, setUndoLoading] = useState(false);
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
              playoffPoolAPI.getAvailablePlayers(leagueId),
          ]);

          setLeague(leagueData);
          setMembers(membersData);
          setAvailablePlayers(playersData);

          // Load drafted teams data to show current picks
          try {
              const teamsData = await playoffPoolAPI.getDraftedTeams(leagueId);
              const allDrafted = [];
              teamsData.teams.forEach((team) => {
                  team.players.forEach((player) => allDrafted.push(player));
              });
              setDraftedPlayers(allDrafted);
          } catch (err) {
              console.warn("No drafted players yet");
          }
      } catch (err) {
          setError("Failed to load draft data");
          console.error("Error loading draft data:", err);
      } finally {
          setLoading(false);
      }
  };

  const handleDraftPlayer = async () => {
      if (!selectedPlayer || !selectedUser) {
          alert("Please select both a player and a team");
          return;
      }

      try {
          setDraftLoading(true);

          // Use team_id (membership id) instead of user_id for specificity
          await playoffPoolAPI.draftPlayer(
              leagueId,
              selectedPlayer.player_id,
              selectedUser.user.id,
              selectedUser.id
          );

          // Reload draft data to update UI
          await loadDraftData();

          // Clear selections
          setSelectedPlayer(null);
          setSelectedUser(null);
      } catch (err) {
          alert(err.response?.data?.error || "Failed to draft player");
          console.error("Error drafting player:", err);
      } finally {
          setDraftLoading(false);
      }
  };

  const handleCompleteDraft = async () => {
      if (
          window.confirm(
              "Are you sure you want to complete the draft? This action cannot be undone."
          )
      ) {
          try {
              await playoffPoolAPI.completeDraft(leagueId);
              navigate(`/playoff-pool/league/${leagueId}/teams`);
          } catch (err) {
              alert("Failed to complete draft");
              console.error("Error completing draft:", err);
          }
      }
  };

  const handleUndoDraft = async () => {
      if (
          !window.confirm(
              "Are you sure you want to undo the most recent draft pick? This action cannot be undone."
          )
      ) {
          return;
      }

      try {
          setUndoLoading(true);

          await playoffPoolAPI.undoDraft(leagueId);

          // Reload draft data to update UI
          await loadDraftData();
      } catch (err) {
          alert(err.response?.data?.error || "Failed to undo draft pick");
          console.error("Error undoing draft pick:", err);
      } finally {
          setUndoLoading(false);
      }
  };

  // Filter players based on position and search term
  const filteredPlayers = availablePlayers
      .filter((player) => {
          const matchesPosition =
              filterPosition === "ALL" || player.position === filterPosition;
          const matchesSearch =
              !searchTerm ||
              player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              player.team.toLowerCase().includes(searchTerm.toLowerCase());
          return matchesPosition && matchesSearch;
      })
      .sort((a, b) => {
          // Primary sort by fantasy points (descending)
          if (b.fantasy_points !== a.fantasy_points) {
              return b.fantasy_points - a.fantasy_points;
          }
          // Secondary sort by player name for consistency
          return a.name.localeCompare(b.name);
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
      // Clear selected player when search changes to prevent inconsistent state
      if (selectedPlayer) {
          setSelectedPlayer(null);
          setSelectedUser(null);
      }
  };

  const handleFilterChange = (value) => {
      setFilterPosition(value);
      setCurrentPage(1);
      // Clear selected player when filter changes to prevent inconsistent state
      if (selectedPlayer) {
          setSelectedPlayer(null);
          setSelectedUser(null);
      }
  };

  const positions = [
      "ALL",
      ...new Set(availablePlayers.map((p) => p.position)),
  ];
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
                      onClick={() =>
                          navigate(`/playoff-pool/league/${leagueId}`)
                      }
                      className="mb-4 text-blue-600 hover:text-blue-800"
                  >
                      ← Back to League
                  </button>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                      Draft Interface
                  </h1>
                  <p className="text-gray-600">{league?.name}</p>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                  {/* Available Players */}
                  <div className="xl:col-span-2">
                      <div
                          style={{
                              backgroundColor: "white",
                              boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                              border: "1px solid #e2e8f0",
                              borderRadius: "8px",
                              overflow: "hidden",
                          }}
                      >
                          {/* Header */}
                          <div
                              style={{
                                  backgroundColor: "#f8fafc",
                                  borderBottom: "1px solid #e2e8f0",
                                  padding: "16px 24px",
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                              }}
                          >
                              <h2
                                  style={{
                                      fontSize: "18px",
                                      fontWeight: "600",
                                      color: "#1f2937",
                                      margin: 0,
                                  }}
                              >
                                  Available Players
                              </h2>
                              <span
                                  style={{
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      color: "#6b7280",
                                  }}
                              >
                                  {startIndex + 1}-
                                  {Math.min(endIndex, filteredPlayers.length)}{" "}
                                  of {filteredPlayers.length} players
                              </span>
                          </div>

                          {/* Filters */}
                          <div
                              style={{
                                  padding: "16px 24px",
                                  borderBottom: "1px solid #f1f5f9",
                                  backgroundColor: "#fafbfc",
                              }}
                          >
                              <div
                                  style={{
                                      display: "flex",
                                      gap: "16px",
                                      flexWrap: "wrap",
                                      alignItems: "center",
                                  }}
                              >
                                  <div>
                                      <label
                                          style={{
                                              fontSize: "12px",
                                              fontWeight: "500",
                                              color: "#64748b",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              marginRight: "8px",
                                          }}
                                      >
                                          Position:
                                      </label>
                                      <select
                                          value={filterPosition}
                                          onChange={(e) =>
                                              handleFilterChange(e.target.value)
                                          }
                                          style={{
                                              padding: "6px 12px",
                                              border: "1px solid #d1d5db",
                                              borderRadius: "6px",
                                              fontSize: "14px",
                                              backgroundColor: "white",
                                              minWidth: "100px",
                                          }}
                                      >
                                          {positions.map((pos) => (
                                              <option key={pos} value={pos}>
                                                  {pos}
                                              </option>
                                          ))}
                                      </select>
                                  </div>
                                  <div style={{ flex: 1, minWidth: "200px" }}>
                                      <label
                                          style={{
                                              fontSize: "12px",
                                              fontWeight: "500",
                                              color: "#64748b",
                                              textTransform: "uppercase",
                                              letterSpacing: "0.05em",
                                              marginRight: "8px",
                                          }}
                                      >
                                          Search:
                                      </label>
                                      <input
                                          type="text"
                                          placeholder="Search players or teams..."
                                          value={searchTerm}
                                          onChange={(e) =>
                                              handleSearchChange(e.target.value)
                                          }
                                          style={{
                                              padding: "6px 12px",
                                              border: "1px solid #d1d5db",
                                              borderRadius: "6px",
                                              fontSize: "14px",
                                              width: "100%",
                                          }}
                                      />
                                  </div>
                              </div>
                          </div>

                          {/* Table Headers */}
                          <div
                              style={{
                                  display: "grid",
                                  gridTemplateColumns:
                                      "6% 10% 25% 10% 15% 8% 16% 10%",
                                  backgroundColor: "#f1f5f9",
                                  borderBottom: "1px solid #e2e8f0",
                              }}
                          >
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  RANK
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
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
                                      padding: "12px 8px",
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
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  NFL TEAM
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  REGULAR SEASON POINT TOTAL
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  SELECT
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  DRAFT TO TEAM
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  DRAFT
                              </div>
                          </div>

                          {/* Table Body */}
                          <div>
                              {currentPlayers.map((player, index) => {
                                  const globalRank = startIndex + index + 1;
                                  const playerTeamId = `player-${player.player_id}-team`;
                                  const isSelected =
                                      selectedPlayer?.player_id ===
                                      player.player_id;
                                  return (
                                      <div
                                          key={player.player_id}
                                          style={{
                                              display: "grid",
                                              gridTemplateColumns:
                                                  "6% 10% 25% 10% 15% 8% 16% 10%",
                                              padding: "12px 0",
                                              borderBottom: "1px solid #f1f5f9",
                                              alignItems: "center",
                                              transition:
                                                  "background-color 0.15s",
                                              backgroundColor: isSelected
                                                  ? "#dbeafe"
                                                  : "transparent",
                                          }}
                                          onMouseEnter={(e) =>
                                              (e.currentTarget.style.backgroundColor =
                                                  isSelected
                                                      ? "#bfdbfe"
                                                      : "#f8fafc")
                                          }
                                          onMouseLeave={(e) =>
                                              (e.currentTarget.style.backgroundColor =
                                                  isSelected
                                                      ? "#dbeafe"
                                                      : "transparent")
                                          }
                                      >
                                          {/* Global Rank */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      fontSize: "14px",
                                                      fontWeight: "600",
                                                      color: "#6b7280",
                                                  }}
                                              >
                                                  {globalRank}
                                              </span>
                                          </div>

                                          {/* Position with colored badge */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      display: "inline-block",
                                                      padding: "4px 8px",
                                                      borderRadius: "12px",
                                                      fontSize: "12px",
                                                      fontWeight: "600",
                                                      backgroundColor:
                                                          {
                                                              QB: "#dbeafe",
                                                              RB: "#dcfce7",
                                                              WR: "#fef3c7",
                                                              TE: "#f3e8ff",
                                                              K: "#fee2e2",
                                                              DST: "#e0f2fe",
                                                          }[player.position] ||
                                                          "#f1f5f9",
                                                      color:
                                                          {
                                                              QB: "#1e40af",
                                                              RB: "#166534",
                                                              WR: "#92400e",
                                                              TE: "#7c3aed",
                                                              K: "#dc2626",
                                                              DST: "#0369a1",
                                                          }[player.position] ||
                                                          "#64748b",
                                                  }}
                                              >
                                                  {player.position}
                                              </span>
                                          </div>

                                          {/* Player Name and Info */}
                                          <div style={{ padding: "0 8px" }}>
                                              <div
                                                  style={{
                                                      fontSize: "14px",
                                                      fontWeight: "500",
                                                      color: "#1f2937",
                                                  }}
                                              >
                                                  {player.name}
                                              </div>
                                          </div>

                                          {/* NFL Team */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      display: "inline-block",
                                                      padding: "2px 6px",
                                                      borderRadius: "4px",
                                                      fontSize: "12px",
                                                      fontWeight: "600",
                                                      backgroundColor:
                                                          "#f1f5f9",
                                                      color: "#374151",
                                                  }}
                                              >
                                                  {player.team}
                                              </span>
                                          </div>

                                          {/* Regular Season Point Total */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      fontSize: "14px",
                                                      fontWeight: "600",
                                                      color: "#1f2937",
                                                  }}
                                              >
                                                  {player.fantasy_points.toFixed(
                                                      1
                                                  )}
                                              </span>
                                          </div>

                                          {/* Select Button */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              <button
                                                  onClick={() => {
                                                      if (isSelected) {
                                                          setSelectedPlayer(
                                                              null
                                                          );
                                                          setSelectedUser(null);
                                                      } else {
                                                          setSelectedPlayer(
                                                              player
                                                          );
                                                          setSelectedUser(null);
                                                      }
                                                  }}
                                                  style={{
                                                      padding: "6px 12px",
                                                      fontSize: "12px",
                                                      fontWeight: "500",
                                                      borderRadius: "6px",
                                                      border: isSelected
                                                          ? "1px solid #3b82f6"
                                                          : "1px solid #d1d5db",
                                                      backgroundColor:
                                                          isSelected
                                                              ? "#3b82f6"
                                                              : "#ffffff",
                                                      color: isSelected
                                                          ? "#ffffff"
                                                          : "#374151",
                                                      cursor: "pointer",
                                                      transition: "all 0.15s",
                                                      minWidth: "70px",
                                                  }}
                                                  onMouseEnter={(e) => {
                                                      if (!isSelected) {
                                                          e.target.style.backgroundColor =
                                                              "#f3f4f6";
                                                          e.target.style.borderColor =
                                                              "#9ca3af";
                                                      }
                                                  }}
                                                  onMouseLeave={(e) => {
                                                      if (!isSelected) {
                                                          e.target.style.backgroundColor =
                                                              "#ffffff";
                                                          e.target.style.borderColor =
                                                              "#d1d5db";
                                                      }
                                                  }}
                                              >
                                                  {isSelected
                                                      ? "Selected"
                                                      : "Select"}
                                              </button>
                                          </div>

                                          {/* Team Selection Dropdown - Only for selected player */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 4px",
                                              }}
                                          >
                                              {isSelected ? (
                                                  <select
                                                      id={playerTeamId}
                                                      value={
                                                          selectedUser?.id || ""
                                                      }
                                                      style={{
                                                          padding: "4px 8px",
                                                          fontSize: "12px",
                                                          borderRadius: "4px",
                                                          border: "1px solid #d1d5db",
                                                          backgroundColor:
                                                              "#ffffff",
                                                          color: "#374151",
                                                          width: "100%",
                                                          maxWidth: "120px",
                                                      }}
                                                      onChange={(e) => {
                                                          const selectedMember =
                                                              members.find(
                                                                  (m) =>
                                                                      m.id.toString() ===
                                                                      e.target
                                                                          .value
                                                              );
                                                          setSelectedUser(
                                                              selectedMember ||
                                                                  null
                                                          );
                                                      }}
                                                  >
                                                      <option value="">
                                                          Select Team
                                                      </option>
                                                      {members.map((member) => (
                                                          <option
                                                              key={member.id}
                                                              value={member.id}
                                                          >
                                                              {member.team_name}
                                                          </option>
                                                      ))}
                                                  </select>
                                              ) : (
                                                  <span
                                                      style={{
                                                          fontSize: "12px",
                                                          color: "#9ca3af",
                                                      }}
                                                  >
                                                      -
                                                  </span>
                                              )}
                                          </div>

                                          {/* Draft Button - Only for selected player with team */}
                                          <div
                                              style={{
                                                  textAlign: "center",
                                                  padding: "0 8px",
                                              }}
                                          >
                                              {isSelected && selectedUser ? (
                                                  <button
                                                      onClick={
                                                          handleDraftPlayer
                                                      }
                                                      disabled={draftLoading}
                                                      style={{
                                                          padding: "6px 12px",
                                                          fontSize: "12px",
                                                          fontWeight: "500",
                                                          borderRadius: "6px",
                                                          border: "1px solid #10b981",
                                                          backgroundColor:
                                                              draftLoading
                                                                  ? "#9ca3af"
                                                                  : "#10b981",
                                                          color: "#ffffff",
                                                          cursor: draftLoading
                                                              ? "not-allowed"
                                                              : "pointer",
                                                          transition:
                                                              "all 0.15s",
                                                          minWidth: "60px",
                                                      }}
                                                      onMouseEnter={(e) => {
                                                          if (!draftLoading) {
                                                              e.target.style.backgroundColor =
                                                                  "#059669";
                                                          }
                                                      }}
                                                      onMouseLeave={(e) => {
                                                          if (!draftLoading) {
                                                              e.target.style.backgroundColor =
                                                                  "#10b981";
                                                          }
                                                      }}
                                                  >
                                                      {draftLoading
                                                          ? "..."
                                                          : "Draft"}
                                                  </button>
                                              ) : (
                                                  <span
                                                      style={{
                                                          fontSize: "12px",
                                                          color: "#9ca3af",
                                                      }}
                                                  >
                                                      -
                                                  </span>
                                              )}
                                          </div>
                                      </div>
                                  );
                              })}

                              {currentPlayers.length === 0 && (
                                  <div
                                      style={{
                                          textAlign: "center",
                                          padding: "32px",
                                          color: "#9ca3af",
                                      }}
                                  >
                                      No players found matching your search
                                      criteria
                                  </div>
                              )}
                          </div>

                          {/* Pagination Controls */}
                          {totalPages > 1 && (
                              <div
                                  style={{
                                      padding: "16px 24px",
                                      borderTop: "1px solid #f1f5f9",
                                      backgroundColor: "#fafbfc",
                                      display: "flex",
                                      justifyContent: "center",
                                      alignItems: "center",
                                      gap: "12px",
                                  }}
                              >
                                  <button
                                      onClick={() =>
                                          setCurrentPage(
                                              Math.max(1, currentPage - 1)
                                          )
                                      }
                                      disabled={currentPage === 1}
                                      style={{
                                          padding: "8px 16px",
                                          fontSize: "14px",
                                          fontWeight: "500",
                                          borderRadius: "6px",
                                          border: "1px solid #d1d5db",
                                          backgroundColor:
                                              currentPage === 1
                                                  ? "#f9fafb"
                                                  : "#ffffff",
                                          color:
                                              currentPage === 1
                                                  ? "#9ca3af"
                                                  : "#374151",
                                          cursor:
                                              currentPage === 1
                                                  ? "not-allowed"
                                                  : "pointer",
                                          transition: "all 0.15s",
                                      }}
                                  >
                                      Previous
                                  </button>

                                  <span
                                      style={{
                                          padding: "8px 16px",
                                          fontSize: "14px",
                                          fontWeight: "500",
                                          color: "#6b7280",
                                      }}
                                  >
                                      Page {currentPage} of {totalPages}
                                  </span>

                                  <button
                                      onClick={() =>
                                          setCurrentPage(
                                              Math.min(
                                                  totalPages,
                                                  currentPage + 1
                                              )
                                          )
                                      }
                                      disabled={currentPage === totalPages}
                                      style={{
                                          padding: "8px 16px",
                                          fontSize: "14px",
                                          fontWeight: "500",
                                          borderRadius: "6px",
                                          border: "1px solid #d1d5db",
                                          backgroundColor:
                                              currentPage === totalPages
                                                  ? "#f9fafb"
                                                  : "#ffffff",
                                          color:
                                              currentPage === totalPages
                                                  ? "#9ca3af"
                                                  : "#374151",
                                          cursor:
                                              currentPage === totalPages
                                                  ? "not-allowed"
                                                  : "pointer",
                                          transition: "all 0.15s",
                                      }}
                                  >
                                      Next
                                  </button>
                              </div>
                          )}
                      </div>
                  </div>

                  {/* Draft Panel */}
                  <div className="xl:col-span-1 space-y-6">
                      {/* Complete Draft Button */}
                      <div className="bg-white shadow-md rounded-lg p-4">
                          <button
                              onClick={handleCompleteDraft}
                              className="w-full bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                          >
                              Complete Draft
                          </button>
                      </div>

                      {/* Recent Picks - ESPN Style Table */}
                      <div
                          style={{
                              backgroundColor: "white",
                              boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                              border: "1px solid #e2e8f0",
                              borderRadius: "8px",
                              overflow: "hidden",
                          }}
                      >
                          {/* Table Header */}
                          <div
                              style={{
                                  backgroundColor: "#f8fafc",
                                  borderBottom: "1px solid #e2e8f0",
                                  padding: "16px 24px",
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "18px",
                                      fontWeight: "600",
                                      color: "#1f2937",
                                      margin: 0,
                                  }}
                              >
                                  Recent Picks (All Teams)
                              </h3>
                              <span
                                  style={{
                                      fontSize: "14px",
                                      fontWeight: "500",
                                      color: "#6b7280",
                                  }}
                              >
                                  Last 10 Picks
                              </span>
                          </div>

                          {/* Table Headers */}
                          <div
                              style={{
                                  display: "grid",
                                  gridTemplateColumns: "8% 15% 30% 15% 20% 12%",
                                  backgroundColor: "#f1f5f9",
                                  borderBottom: "1px solid #e2e8f0",
                              }}
                          >
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  PICK
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
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
                                      padding: "12px 8px",
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
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                  }}
                              >
                                  TEAM
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  DRAFTED
                              </div>
                              <div
                                  style={{
                                      padding: "12px 8px",
                                      fontSize: "12px",
                                      fontWeight: "500",
                                      color: "#64748b",
                                      textTransform: "uppercase",
                                      letterSpacing: "0.05em",
                                      textAlign: "center",
                                  }}
                              >
                                  ACTION
                              </div>
                          </div>

                          {/* Table Body */}
                          <div>
                              {draftedPlayers
                                  .sort(
                                      (a, b) =>
                                          new Date(b.drafted_at) -
                                          new Date(a.drafted_at)
                                  )
                                  .slice(0, 10)
                                  .map((pick, index) => {
                                      const isLatestPick =
                                          index === 0 &&
                                          draftedPlayers.length > 0;
                                      return (
                                          <div
                                              key={pick.id}
                                              style={{
                                                  display: "grid",
                                                  gridTemplateColumns:
                                                      "8% 15% 30% 15% 20% 12%",
                                                  padding: "12px 0",
                                                  borderBottom:
                                                      "1px solid #f1f5f9",
                                                  alignItems: "center",
                                                  transition:
                                                      "background-color 0.15s",
                                                  backgroundColor: isLatestPick
                                                      ? "#fef3c7"
                                                      : "transparent",
                                              }}
                                              onMouseEnter={(e) =>
                                                  (e.currentTarget.style.backgroundColor =
                                                      isLatestPick
                                                          ? "#fde68a"
                                                          : "#f8fafc")
                                              }
                                              onMouseLeave={(e) =>
                                                  (e.currentTarget.style.backgroundColor =
                                                      isLatestPick
                                                          ? "#fef3c7"
                                                          : "transparent")
                                              }
                                          >
                                              {/* Pick Number */}
                                              <div
                                                  style={{
                                                      textAlign: "center",
                                                      padding: "0 8px",
                                                  }}
                                              >
                                                  <span
                                                      style={{
                                                          fontSize: "14px",
                                                          fontWeight: "600",
                                                          color: "#1f2937",
                                                      }}
                                                  >
                                                      #{pick.draft_order}
                                                  </span>
                                              </div>

                                              {/* Position with colored badge */}
                                              <div
                                                  style={{
                                                      textAlign: "center",
                                                      padding: "0 8px",
                                                  }}
                                              >
                                                  <span
                                                      style={{
                                                          display:
                                                              "inline-block",
                                                          padding: "4px 8px",
                                                          borderRadius: "12px",
                                                          fontSize: "12px",
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
                                                                  pick.position
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
                                                                  pick.position
                                                              ] || "#64748b",
                                                      }}
                                                  >
                                                      {pick.position}
                                                  </span>
                                              </div>

                                              {/* Player Name */}
                                              <div style={{ padding: "0 8px" }}>
                                                  <div
                                                      style={{
                                                          fontSize: "14px",
                                                          fontWeight: "500",
                                                          color: "#1f2937",
                                                      }}
                                                  >
                                                      {pick.player_name}
                                                  </div>
                                                  <div
                                                      style={{
                                                          fontSize: "12px",
                                                          color: "#6b7280",
                                                      }}
                                                  >
                                                      {pick.team}
                                                  </div>
                                              </div>

                                              {/* Team Name */}
                                              <div style={{ padding: "0 8px" }}>
                                                  <div
                                                      style={{
                                                          fontSize: "14px",
                                                          color: "#1f2937",
                                                      }}
                                                  >
                                                      {pick.team_name}
                                                  </div>
                                              </div>

                                              {/* Drafted Time */}
                                              <div
                                                  style={{
                                                      textAlign: "center",
                                                      padding: "0 8px",
                                                  }}
                                              >
                                                  <div
                                                      style={{
                                                          fontSize: "12px",
                                                          color: "#6b7280",
                                                      }}
                                                  >
                                                      {new Date(
                                                          pick.drafted_at
                                                      ).toLocaleString(
                                                          "en-US",
                                                          {
                                                              timeZone:
                                                                  "America/New_York",
                                                              month: "short",
                                                              day: "numeric",
                                                              hour: "numeric",
                                                              minute: "2-digit",
                                                              hour12: true,
                                                          }
                                                      )}{" "}
                                                      EST
                                                  </div>
                                              </div>

                                              {/* Action Button */}
                                              <div
                                                  style={{
                                                      textAlign: "center",
                                                      padding: "0 8px",
                                                  }}
                                              >
                                                  {isLatestPick ? (
                                                      <button
                                                          onClick={
                                                              handleUndoDraft
                                                          }
                                                          disabled={undoLoading}
                                                          style={{
                                                              padding:
                                                                  "4px 8px",
                                                              fontSize: "12px",
                                                              fontWeight: "500",
                                                              borderRadius:
                                                                  "4px",
                                                              border: "1px solid #ef4444",
                                                              backgroundColor:
                                                                  undoLoading
                                                                      ? "#fca5a5"
                                                                      : "#fee2e2",
                                                              color: "#dc2626",
                                                              cursor: undoLoading
                                                                  ? "not-allowed"
                                                                  : "pointer",
                                                              transition:
                                                                  "all 0.15s",
                                                          }}
                                                          onMouseEnter={(e) => {
                                                              if (
                                                                  !undoLoading
                                                              ) {
                                                                  e.target.style.backgroundColor =
                                                                      "#fecaca";
                                                              }
                                                          }}
                                                          onMouseLeave={(e) => {
                                                              if (
                                                                  !undoLoading
                                                              ) {
                                                                  e.target.style.backgroundColor =
                                                                      "#fee2e2";
                                                              }
                                                          }}
                                                      >
                                                          {undoLoading
                                                              ? "Undoing..."
                                                              : "Undo"}
                                                      </button>
                                                  ) : (
                                                      <span
                                                          style={{
                                                              fontSize: "12px",
                                                              color: "#9ca3af",
                                                          }}
                                                      >
                                                          -
                                                      </span>
                                                  )}
                                              </div>
                                          </div>
                                      );
                                  })}
                              {draftedPlayers.length === 0 && (
                                  <div
                                      style={{
                                          textAlign: "center",
                                          padding: "32px",
                                          color: "#9ca3af",
                                      }}
                                  >
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