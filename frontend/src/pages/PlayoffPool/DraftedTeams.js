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

            const [leagueData, playoffData] = await Promise.all([
                playoffPoolAPI.getLeague(leagueId),
                playoffPoolAPI.getPlayoffStats(leagueId),
            ]);

            setLeague(leagueData);

            // If playoff stats returns empty teams, try to get basic drafted team data
            if (!playoffData.teams || playoffData.teams.length === 0) {
                try {
                    // Try the fallback API, but if it fails, create empty structure with team data from league
                    const draftedData = await playoffPoolAPI.getDraftedTeams(
                        leagueId,
                        false
                    );
                    setTeamsData(draftedData);
                    setError(
                        "Playoff stats are not yet available for this season"
                    );
                } catch (fallbackErr) {
                    console.error("Fallback API failed:", fallbackErr);
                    // Create a basic structure with empty teams if we can't get drafted teams
                    // This ensures the UI shows something rather than being completely empty
                    const emptyTeamsData = {
                        teams: [],
                        total_teams: 0,
                        playoff_rounds: [],
                        year:
                            leagueData.league_year || new Date().getFullYear(),
                        data_source: "none",
                    };
                    setTeamsData(emptyTeamsData);
                    setError(
                        "No teams found for this league - try adding some drafted players first"
                    );
                }
            } else {
                setTeamsData(playoffData);
            }
        } catch (err) {
            console.error("Error loading teams:", err);
            // Fallback to regular drafted teams if playoff stats call fails completely
            try {
                const [leagueData, draftedData] = await Promise.all([
                    playoffPoolAPI.getLeague(leagueId),
                    playoffPoolAPI.getDraftedTeams(leagueId, false), // Use static points
                ]);

                setLeague(leagueData);
                setTeamsData(draftedData);
                setError("Playoff stats are not yet available for this season");
            } catch (fallbackErr) {
                setError("Failed to load teams data");
            }
        } finally {
            setLoading(false);
        }
    };

    const getPositionCounts = (players) => {
        const counts = {};
        players.forEach((player) => {
            counts[player.position] = (counts[player.position] || 0) + 1;
        });
        return counts;
    };

    const getPositionTotals = (players) => {
        const totals = {};
        players.forEach((player) => {
            totals[player.position] =
                (totals[player.position] || 0) + player.fantasy_points;
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

    // Only show error state if there's a critical error AND no teams data
    if (
        error &&
        (!teamsData || !teamsData.teams || teamsData.teams.length === 0)
    ) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
                <button
                    onClick={() => navigate(`/playoff-pool/league/${leagueId}`)}
                    style={{
                        display: "inline-flex",
                        alignItems: "center",
                        padding: "12px 20px",
                        backgroundColor: "#3b82f6",
                        color: "white",
                        fontWeight: "600",
                        fontSize: "14px",
                        borderRadius: "8px",
                        border: "none",
                        cursor: "pointer",
                        transition: "background-color 0.15s",
                        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                    }}
                    onMouseEnter={(e) =>
                        (e.target.style.backgroundColor = "#2563eb")
                    }
                    onMouseLeave={(e) =>
                        (e.target.style.backgroundColor = "#3b82f6")
                    }
                >
                    ← Back to League
                </button>
            </div>
        );
    }

    const teams = teamsData?.teams || [];

    // Calculate total players from teams data
    const totalPlayers = teams.reduce(
        (total, team) => total + (team.players?.length || 0),
        0
    );

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="container mx-auto px-4">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() =>
                            navigate(`/playoff-pool/league/${leagueId}`)
                        }
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            padding: "8px 16px",
                            backgroundColor: "#6b7280",
                            color: "white",
                            fontWeight: "500",
                            fontSize: "13px",
                            borderRadius: "6px",
                            border: "none",
                            cursor: "pointer",
                            transition: "background-color 0.15s",
                            boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                            marginBottom: "20px",
                        }}
                        onMouseEnter={(e) =>
                            (e.target.style.backgroundColor = "#4b5563")
                        }
                        onMouseLeave={(e) =>
                            (e.target.style.backgroundColor = "#6b7280")
                        }
                    >
                        ← Back to League
                    </button>

                    {/* Warning message if there's an error but teams data exists */}
                    {error &&
                        teamsData &&
                        teamsData.teams &&
                        teamsData.teams.length > 0 && (
                            <div
                                style={{
                                    backgroundColor: "#fef3c7",
                                    border: "1px solid #f59e0b",
                                    borderRadius: "8px",
                                    padding: "12px 16px",
                                    marginBottom: "20px",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "16px",
                                        height: "16px",
                                        borderRadius: "50%",
                                        backgroundColor: "#f59e0b",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "11px",
                                        fontWeight: "bold",
                                        color: "white",
                                    }}
                                >
                                    !
                                </div>
                                <span
                                    style={{
                                        fontSize: "14px",
                                        color: "#92400e",
                                        fontWeight: "500",
                                    }}
                                >
                                    {error}
                                </span>
                            </div>
                        )}

                    {/* League Information Card */}
                    <div
                        style={{
                            backgroundColor: "white",
                            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                            padding: "24px",
                            marginBottom: "24px",
                        }}
                    >
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                                marginBottom: "16px",
                            }}
                        >
                            <div>
                                <h1
                                    style={{
                                        fontSize: "24px",
                                        fontWeight: "700",
                                        color: "#1f2937",
                                        margin: "0 0 8px 0",
                                    }}
                                >
                                    Drafted Teams
                                </h1>
                                <h2
                                    style={{
                                        fontSize: "18px",
                                        fontWeight: "600",
                                        color: "#374151",
                                        margin: "0",
                                    }}
                                >
                                    {league?.name}
                                </h2>
                            </div>
                            <div
                                style={{
                                    textAlign: "right",
                                }}
                            >
                                {teamsData?.year && (
                                    <div
                                        style={{
                                            fontSize: "16px",
                                            fontWeight: "600",
                                            color: "#1f2937",
                                            marginBottom: "4px",
                                        }}
                                    >
                                        {teamsData.year} Season
                                    </div>
                                )}
                                {teamsData?.data_source === "playoff_stats" && (
                                    <div
                                        style={{
                                            display: "inline-block",
                                            padding: "4px 8px",
                                            backgroundColor: "#10b981",
                                            color: "white",
                                            fontSize: "12px",
                                            fontWeight: "500",
                                            borderRadius: "12px",
                                        }}
                                    >
                                        Live Playoff Stats
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* League Stats */}
                        <div
                            style={{
                                display: "flex",
                                gap: "24px",
                                paddingTop: "16px",
                                borderTop: "1px solid #f1f5f9",
                            }}
                        >
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "8px",
                                        height: "8px",
                                        backgroundColor: "#3b82f6",
                                        borderRadius: "50%",
                                    }}
                                ></div>
                                <span
                                    style={{
                                        fontSize: "14px",
                                        color: "#6b7280",
                                    }}
                                >
                                    <strong style={{ color: "#1f2937" }}>
                                        {teamsData?.total_teams || 0}
                                    </strong>{" "}
                                    teams
                                </span>
                            </div>
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "8px",
                                        height: "8px",
                                        backgroundColor: "#10b981",
                                        borderRadius: "50%",
                                    }}
                                ></div>
                                <span
                                    style={{
                                        fontSize: "14px",
                                        color: "#6b7280",
                                    }}
                                >
                                    <strong style={{ color: "#1f2937" }}>
                                        {totalPlayers}
                                    </strong>{" "}
                                    total players drafted
                                </span>
                            </div>
                        </div>

                        {/* Playoff Rounds Legend */}
                        {teamsData?.playoff_rounds &&
                            teamsData.playoff_rounds.length > 0 && (
                                <div
                                    style={{
                                        marginTop: "16px",
                                        paddingTop: "16px",
                                        borderTop: "1px solid #f1f5f9",
                                    }}
                                >
                                    <div
                                        style={{
                                            fontSize: "14px",
                                            fontWeight: "600",
                                            color: "#374151",
                                            marginBottom: "12px",
                                        }}
                                    >
                                        Playoff Rounds:
                                    </div>
                                    <div
                                        style={{
                                            display: "flex",
                                            flexWrap: "wrap",
                                            gap: "8px",
                                        }}
                                    >
                                        {teamsData.playoff_rounds.map(
                                            (round) => {
                                                const roundNames = {
                                                    WC: "Wild Card",
                                                    DIV: "Divisional",
                                                    CON: "Conference Championship",
                                                    SB: "Super Bowl",
                                                };
                                                return (
                                                    <span
                                                        key={round}
                                                        style={{
                                                            padding: "6px 12px",
                                                            backgroundColor:
                                                                "#dbeafe",
                                                            color: "#1e40af",
                                                            borderRadius:
                                                                "16px",
                                                            fontSize: "13px",
                                                            fontWeight: "500",
                                                        }}
                                                    >
                                                        {round}:{" "}
                                                        {roundNames[round] ||
                                                            round}
                                                    </span>
                                                );
                                            }
                                        )}
                                    </div>
                                </div>
                            )}
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
                                            {teamsData?.data_source ===
                                            "static_points"
                                                ? "0.0"
                                                : (
                                                      team.total_points || 0
                                                  ).toFixed(1)}{" "}
                                            pts
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
                                        gridTemplateColumns:
                                            "10% 35% 10% 10% 10% 10% 15%",
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
                                            padding: "8px 4px",
                                            fontSize: "11px",
                                            fontWeight: "600",
                                            color: "#64748b",
                                            textAlign: "center",
                                        }}
                                    >
                                        WC
                                    </div>
                                    <div
                                        style={{
                                            padding: "8px 4px",
                                            fontSize: "11px",
                                            fontWeight: "600",
                                            color: "#64748b",
                                            textAlign: "center",
                                        }}
                                    >
                                        DIV
                                    </div>
                                    <div
                                        style={{
                                            padding: "8px 4px",
                                            fontSize: "11px",
                                            fontWeight: "600",
                                            color: "#64748b",
                                            textAlign: "center",
                                        }}
                                    >
                                        CON
                                    </div>
                                    <div
                                        style={{
                                            padding: "8px 4px",
                                            fontSize: "11px",
                                            fontWeight: "600",
                                            color: "#64748b",
                                            textAlign: "center",
                                        }}
                                    >
                                        SB
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
                                        TOTAL
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
                                        .sort((a, b) => {
                                            // When using static points, treat all as 0 for sorting (maintain original order)
                                            if (
                                                teamsData?.data_source ===
                                                "static_points"
                                            ) {
                                                return 0;
                                            }

                                            const aPoints =
                                                a.total_points ||
                                                a.fantasy_points ||
                                                0;
                                            const bPoints =
                                                b.total_points ||
                                                b.fantasy_points ||
                                                0;
                                            return bPoints - aPoints;
                                        })
                                        .map((player, index) => (
                                            <div
                                                key={
                                                    player.gsis_id || player.id
                                                }
                                                style={{
                                                    display: "grid",
                                                    gridTemplateColumns:
                                                        "10% 35% 10% 10% 10% 10% 15%",
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
                                                            borderRadius:
                                                                "12px",
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
                                                        {player.nfl_team ||
                                                            player.team}
                                                    </div>
                                                </div>

                                                {/* WC Points */}
                                                <div
                                                    style={{
                                                        textAlign: "center",
                                                        padding: "12px 4px",
                                                        fontSize: "13px",
                                                        color: "#1f2937",
                                                    }}
                                                >
                                                    {player.round_points?.WC !==
                                                        undefined &&
                                                    player.round_points.WC > 0
                                                        ? parseFloat(
                                                              player
                                                                  .round_points
                                                                  .WC
                                                          ).toFixed(1)
                                                        : "-"}
                                                </div>

                                                {/* DIV Points */}
                                                <div
                                                    style={{
                                                        textAlign: "center",
                                                        padding: "12px 4px",
                                                        fontSize: "13px",
                                                        color: "#1f2937",
                                                    }}
                                                >
                                                    {player.round_points
                                                        ?.DIV !== undefined &&
                                                    player.round_points.DIV > 0
                                                        ? parseFloat(
                                                              player
                                                                  .round_points
                                                                  .DIV
                                                          ).toFixed(1)
                                                        : "-"}
                                                </div>

                                                {/* CON Points */}
                                                <div
                                                    style={{
                                                        textAlign: "center",
                                                        padding: "12px 4px",
                                                        fontSize: "13px",
                                                        color: "#1f2937",
                                                    }}
                                                >
                                                    {player.round_points
                                                        ?.CON !== undefined &&
                                                    player.round_points.CON > 0
                                                        ? parseFloat(
                                                              player
                                                                  .round_points
                                                                  .CON
                                                          ).toFixed(1)
                                                        : "-"}
                                                </div>

                                                {/* SB Points */}
                                                <div
                                                    style={{
                                                        textAlign: "center",
                                                        padding: "12px 4px",
                                                        fontSize: "13px",
                                                        color: "#1f2937",
                                                    }}
                                                >
                                                    {player.round_points?.SB !==
                                                        undefined &&
                                                    player.round_points.SB > 0
                                                        ? parseFloat(
                                                              player
                                                                  .round_points
                                                                  .SB
                                                          ).toFixed(1)
                                                        : "-"}
                                                </div>

                                                {/* Total Points */}
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
                                                        {teamsData?.data_source ===
                                                        "static_points"
                                                            ? "0.0"
                                                            : (
                                                                  player.total_points ||
                                                                  player.fantasy_points ||
                                                                  0
                                                              ).toFixed(1)}
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