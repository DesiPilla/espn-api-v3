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
    navigate("/playoff-pool/join");
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
      <div className="min-h-screen bg-gray-50 py-8">
          <div className="container mx-auto px-4">
              {/* Header */}
              <div
                  style={{
                      backgroundColor: "white",
                      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                      overflow: "hidden",
                      marginBottom: "24px",
                  }}
              >
                  <div
                      style={{
                          backgroundColor: "#f8fafc",
                          borderBottom: "1px solid #e2e8f0",
                          padding: "24px",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                      }}
                  >
                      <div>
                          <h1
                              style={{
                                  fontSize: "28px",
                                  fontWeight: "700",
                                  color: "#1f2937",
                                  margin: 0,
                                  marginBottom: "8px",
                              }}
                          >
                              Welcome back,{" "}
                              {user?.display_name || user?.username}!
                          </h1>
                          <p
                              style={{
                                  fontSize: "16px",
                                  color: "#6b7280",
                                  margin: 0,
                              }}
                          >
                              Manage your playoff pool leagues
                          </p>
                      </div>
                      <button
                          onClick={handleLogout}
                          style={{
                              padding: "8px 16px",
                              fontSize: "14px",
                              fontWeight: "500",
                              borderRadius: "6px",
                              border: "1px solid #ef4444",
                              backgroundColor: "#ef4444",
                              color: "#ffffff",
                              cursor: "pointer",
                              transition: "all 0.15s",
                          }}
                          onMouseEnter={(e) =>
                              (e.target.style.backgroundColor = "#dc2626")
                          }
                          onMouseLeave={(e) =>
                              (e.target.style.backgroundColor = "#ef4444")
                          }
                      >
                          Logout
                      </button>
                  </div>

                  {/* Action Buttons */}
                  <div
                      style={{
                          padding: "24px",
                          borderBottom: "1px solid #f1f5f9",
                          backgroundColor: "#fafbfc",
                      }}
                  >
                      <div
                          style={{
                              display: "flex",
                              gap: "16px",
                              flexWrap: "wrap",
                          }}
                      >
                          <button
                              onClick={handleCreateLeague}
                              style={{
                                  padding: "12px 24px",
                                  fontSize: "14px",
                                  fontWeight: "600",
                                  borderRadius: "8px",
                                  border: "1px solid #3b82f6",
                                  backgroundColor: "#3b82f6",
                                  color: "#ffffff",
                                  cursor: "pointer",
                                  transition: "all 0.15s",
                              }}
                              onMouseEnter={(e) =>
                                  (e.target.style.backgroundColor = "#2563eb")
                              }
                              onMouseLeave={(e) =>
                                  (e.target.style.backgroundColor = "#3b82f6")
                              }
                          >
                              Create New League
                          </button>
                          <button
                              onClick={handleJoinLeague}
                              style={{
                                  padding: "12px 24px",
                                  fontSize: "14px",
                                  fontWeight: "600",
                                  borderRadius: "8px",
                                  border: "1px solid #10b981",
                                  backgroundColor: "#10b981",
                                  color: "#ffffff",
                                  cursor: "pointer",
                                  transition: "all 0.15s",
                              }}
                              onMouseEnter={(e) =>
                                  (e.target.style.backgroundColor = "#059669")
                              }
                              onMouseLeave={(e) =>
                                  (e.target.style.backgroundColor = "#10b981")
                              }
                          >
                              Join Existing League
                          </button>
                      </div>
                  </div>
              </div>

              {/* Error Display */}
              {error && (
                  <div
                      style={{
                          backgroundColor: "#fef2f2",
                          border: "1px solid #fecaca",
                          borderRadius: "8px",
                          padding: "16px",
                          marginBottom: "24px",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                      }}
                  >
                      <span style={{ color: "#dc2626", fontSize: "14px" }}>
                          {error}
                      </span>
                      <button
                          onClick={loadLeagues}
                          style={{
                              color: "#dc2626",
                              textDecoration: "underline",
                              background: "none",
                              border: "none",
                              cursor: "pointer",
                              fontSize: "14px",
                          }}
                      >
                          Try Again
                      </button>
                  </div>
              )}

              {/* Leagues Table */}
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
                          Your Leagues
                      </h2>
                      <span
                          style={{
                              fontSize: "14px",
                              fontWeight: "500",
                              color: "#6b7280",
                          }}
                      >
                          {leagues.length}{" "}
                          {leagues.length === 1 ? "League" : "Leagues"}
                      </span>
                  </div>

                  {leagues.length === 0 ? (
                      <div
                          style={{
                              padding: "48px 24px",
                              textAlign: "center",
                              color: "#9ca3af",
                          }}
                      >
                          <p
                              style={{
                                  fontSize: "18px",
                                  marginBottom: "16px",
                                  fontWeight: "500",
                              }}
                          >
                              No leagues yet!
                          </p>
                          <p style={{ fontSize: "14px", marginBottom: "0" }}>
                              Create or join a league to get started.
                          </p>
                      </div>
                  ) : (
                      <>
                          {/* Table Headers */}
                          <div
                              style={{
                                  display: "grid",
                                  gridTemplateColumns:
                                      "5% 30% 10% 20% 15% 10% 10%",
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
                                  #
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
                                  LEAGUE NAME
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
                                  TEAMS
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
                                  YOUR TEAM
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
                                  POSITIONS
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
                                  STATUS
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
                                  CREATED
                              </div>
                          </div>

                          {/* Table Body */}
                          <div>
                              {leagues.map((league, index) => (
                                  <div
                                      key={league.id}
                                      onClick={() =>
                                          handleLeagueClick(league.id)
                                      }
                                      style={{
                                          display: "grid",
                                          gridTemplateColumns:
                                              "5% 30% 10% 20% 15% 10% 10%",
                                          padding: "16px 0",
                                          borderBottom: "1px solid #f1f5f9",
                                          alignItems: "center",
                                          transition: "background-color 0.15s",
                                          cursor: "pointer",
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
                                      {/* Index */}
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
                                              {index + 1}
                                          </span>
                                      </div>

                                      {/* League Name */}
                                      <div style={{ padding: "0 8px" }}>
                                          <div
                                              style={{
                                                  fontSize: "16px",
                                                  fontWeight: "600",
                                                  color: "#1f2937",
                                                  marginBottom: "4px",
                                              }}
                                          >
                                              {league.name}
                                          </div>
                                          <div
                                              style={{
                                                  fontSize: "12px",
                                                  color: "#6b7280",
                                              }}
                                          >
                                              {league.league_year} NFL Season
                                          </div>
                                      </div>

                                      {/* Teams Count */}
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
                                                  backgroundColor: "#f1f5f9",
                                                  color: "#374151",
                                              }}
                                          >
                                              {league.member_count || 0} /{" "}
                                              {league.num_teams}
                                          </span>
                                      </div>

                                      {/* Your Team */}
                                      <div style={{ padding: "0 8px" }}>
                                          {league.user_membership ? (
                                              <div>
                                                  <div
                                                      style={{
                                                          fontSize: "14px",
                                                          fontWeight: "500",
                                                          color: "#1f2937",
                                                      }}
                                                  >
                                                      {
                                                          league.user_membership
                                                              .team_name
                                                      }
                                                  </div>
                                                  {league.user_membership
                                                      .is_admin && (
                                                      <span
                                                          style={{
                                                              display:
                                                                  "inline-block",
                                                              padding:
                                                                  "2px 6px",
                                                              borderRadius:
                                                                  "8px",
                                                              fontSize: "10px",
                                                              fontWeight: "600",
                                                              backgroundColor:
                                                                  "#dbeafe",
                                                              color: "#1e40af",
                                                              marginTop: "2px",
                                                          }}
                                                      >
                                                          Admin
                                                      </span>
                                                  )}
                                              </div>
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

                                      {/* Positions */}
                                      <div
                                          style={{
                                              textAlign: "center",
                                              padding: "0 8px",
                                          }}
                                      >
                                          <span
                                              style={{
                                                  fontSize: "12px",
                                                  color: "#6b7280",
                                              }}
                                          >
                                              {Array.isArray(
                                                  league.positions_included
                                              )
                                                  ? league.positions_included
                                                        .length
                                                  : 0}{" "}
                                              pos
                                          </span>
                                      </div>

                                      {/* Status */}
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
                                                  fontSize: "11px",
                                                  fontWeight: "600",
                                                  backgroundColor:
                                                      league.is_draft_complete
                                                          ? "#dcfce7"
                                                          : league.draft_started_at
                                                          ? "#fef3c7"
                                                          : "#f1f5f9",
                                                  color: league.is_draft_complete
                                                      ? "#166534"
                                                      : league.draft_started_at
                                                      ? "#92400e"
                                                      : "#64748b",
                                              }}
                                          >
                                              {league.is_draft_complete
                                                  ? "Complete"
                                                  : league.draft_started_at
                                                  ? "In Progress"
                                                  : "Not Started"}
                                          </span>
                                      </div>

                                      {/* Created Date */}
                                      <div
                                          style={{
                                              textAlign: "center",
                                              padding: "0 8px",
                                          }}
                                      >
                                          <span
                                              style={{
                                                  fontSize: "12px",
                                                  color: "#6b7280",
                                              }}
                                          >
                                              {league.created_at_est
                                                  ? new Date(
                                                        league.created_at_est
                                                    ).toLocaleDateString(
                                                        "en-US",
                                                        {
                                                            timeZone:
                                                                "America/New_York",
                                                            month: "short",
                                                            day: "numeric",
                                                            year: "numeric",
                                                        }
                                                    )
                                                  : new Date(
                                                        league.created_at
                                                    ).toLocaleDateString(
                                                        "en-US",
                                                        {
                                                            month: "short",
                                                            day: "numeric",
                                                            year: "numeric",
                                                        }
                                                    )}
                                          </span>
                                      </div>
                                  </div>
                              ))}
                          </div>
                      </>
                  )}
              </div>
          </div>
      </div>
  );
};

export default Dashboard;