import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';
import Footer from "../../components/Footer";

const JoinLeague = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { user } = usePlayoffPoolAuth();

    const [leagueId, setLeagueId] = useState(searchParams.get("league") || "");
    const [leagueInfo, setLeagueInfo] = useState(null);
    const [members, setMembers] = useState([]);
    const [selectedTeamId, setSelectedTeamId] = useState(null);
    const [creatingNewTeam, setCreatingNewTeam] = useState(false);
    const [newTeamName, setNewTeamName] = useState("");
    const [loading, setLoading] = useState(false);
    const [joinLoading, setJoinLoading] = useState(false);
    const [error, setError] = useState(null);
    const [confirmationNeeded, setConfirmationNeeded] = useState(null);

    useEffect(() => {
        // If coming from invite link with team parameter
        const teamId = searchParams.get("team");
        if (teamId) {
            setSelectedTeamId(teamId);
        }
    }, [searchParams]);

    useEffect(() => {
        if (leagueId) {
            loadLeagueInfo();
        }
    }, [leagueId]);

    const loadLeagueInfo = async () => {
        try {
            setLoading(true);
            setError(null);

            const [leagueData, membersData] = await Promise.all([
                playoffPoolAPI.getLeagueInfo(leagueId),
                playoffPoolAPI.getLeagueMembers(leagueId),
            ]);

            setLeagueInfo(leagueData);
            setMembers(membersData);

            // Auto-select first unclaimed team if coming from invite
            if (!selectedTeamId && leagueData.unclaimed_team_list.length > 0) {
                setSelectedTeamId(leagueData.unclaimed_team_list[0].id);
            }
        } catch (err) {
            setError(err.response?.data?.error || "League not found");
            setLeagueInfo(null);
            setMembers([]);
        } finally {
            setLoading(false);
        }
    };

    const handleClaimTeam = async (teamId) => {
        if (!user) {
            alert("Please log in first");
            return;
        }

        try {
            setJoinLoading(true);
            setError(null);
            setConfirmationNeeded(null);

            const result = await playoffPoolAPI.claimTeam(leagueId, teamId);

            // Check if confirmation is needed
            if (result.requires_confirmation) {
                setConfirmationNeeded({
                    ...result,
                    action: "claim",
                    teamId: teamId,
                });
                return;
            }

            // Success - navigate to league
            navigate(`/playoff-pool/league/${leagueId}`);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to claim team");
        } finally {
            setJoinLoading(false);
        }
    };

    const handleCreateTeam = async () => {
        if (!user || !newTeamName.trim()) {
            alert(
                newTeamName.trim()
                    ? "Please log in first"
                    : "Please enter a team name"
            );
            return;
        }

        try {
            setJoinLoading(true);
            setError(null);
            setConfirmationNeeded(null);

            const result = await playoffPoolAPI.joinLeague(
                leagueId,
                newTeamName.trim()
            );

            // Check if confirmation is needed
            if (result.requires_confirmation) {
                setConfirmationNeeded({
                    ...result,
                    action: "create",
                    teamName: newTeamName.trim(),
                });
                return;
            }

            // Success - navigate to league
            navigate(`/playoff-pool/league/${leagueId}`);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to create team");
        } finally {
            setJoinLoading(false);
        }
    };

    const handleConfirmMultiple = async () => {
        try {
            setJoinLoading(true);
            setError(null);

            if (confirmationNeeded.action === "claim") {
                await playoffPoolAPI.claimTeam(
                    leagueId,
                    confirmationNeeded.teamId,
                    true
                );
            } else if (confirmationNeeded.action === "create") {
                await playoffPoolAPI.joinLeague(
                    leagueId,
                    confirmationNeeded.teamName,
                    true
                );
            }

            // Success - navigate to league
            navigate(`/playoff-pool/league/${leagueId}`);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to join league");
        } finally {
            setJoinLoading(false);
            setConfirmationNeeded(null);
        }
    };

    const handleBackToDashboard = () => {
        navigate("/playoff-pool");
    };

    const cancelCreatingTeam = () => {
        setCreatingNewTeam(false);
        setNewTeamName("");
    };

    const startCreatingTeam = () => {
        setCreatingNewTeam(true);
        setNewTeamName("");
        setSelectedTeamId(null);
    };

    if (!user) {
        return (
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="container mx-auto px-4">
                    <div className="max-w-md mx-auto bg-white shadow-md rounded-lg p-6">
                        <h1 className="text-2xl font-bold mb-4">Join League</h1>
                        <p className="text-gray-600 mb-4">
                            Please log in or register to join a league.
                        </p>
                        <button
                            onClick={() => {
                                // Preserve query parameters when redirecting to login
                                const queryString = searchParams.toString();
                                const redirectPath = queryString
                                    ? `/playoff-pool/?redirect=join&${queryString}`
                                    : "/playoff-pool/";
                                navigate(redirectPath);
                            }}
                            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full"
                        >
                            Log In / Register
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="container mx-auto px-4">
                <div className="max-w-6xl mx-auto">
                    <button
                        onClick={handleBackToDashboard}
                        style={{
                            marginBottom: "24px",
                            padding: "8px 16px",
                            fontSize: "14px",
                            fontWeight: "500",
                            borderRadius: "6px",
                            border: "1px solid #3b82f6",
                            backgroundColor: "transparent",
                            color: "#3b82f6",
                            cursor: "pointer",
                            transition: "all 0.15s",
                        }}
                        onMouseEnter={(e) => {
                            e.target.style.backgroundColor = "#3b82f6";
                            e.target.style.color = "#ffffff";
                        }}
                        onMouseLeave={(e) => {
                            e.target.style.backgroundColor = "transparent";
                            e.target.style.color = "#3b82f6";
                        }}
                    >
                        ← Back to Dashboard
                    </button>

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
                                    Join League
                                </h1>
                                <p
                                    style={{
                                        fontSize: "16px",
                                        color: "#6b7280",
                                        margin: 0,
                                    }}
                                >
                                    Claim an existing team or create a new one
                                </p>
                            </div>
                        </div>

                        {/* League ID Input */}
                        <div
                            style={{
                                padding: "24px",
                                borderBottom: "1px solid #f1f5f9",
                                backgroundColor: "#fafbfc",
                            }}
                        >
                            <label
                                style={{
                                    display: "block",
                                    fontSize: "14px",
                                    fontWeight: "500",
                                    color: "#374151",
                                    marginBottom: "8px",
                                }}
                            >
                                League ID
                            </label>
                            <div
                                style={{
                                    display: "flex",
                                    gap: "12px",
                                    alignItems: "center",
                                }}
                            >
                                <input
                                    type="text"
                                    value={leagueId}
                                    onChange={(e) =>
                                        setLeagueId(e.target.value)
                                    }
                                    placeholder="4"
                                    style={{
                                        flex: 1,
                                        padding: "12px 16px",
                                        fontSize: "16px",
                                        border: "1px solid #d1d5db",
                                        borderRadius: "8px",
                                        outline: "none",
                                        transition: "border-color 0.15s",
                                    }}
                                    onFocus={(e) =>
                                        (e.target.style.borderColor = "#3b82f6")
                                    }
                                    onBlur={(e) =>
                                        (e.target.style.borderColor = "#d1d5db")
                                    }
                                />
                                <button
                                    onClick={loadLeagueInfo}
                                    disabled={!leagueId.trim() || loading}
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
                                        opacity:
                                            !leagueId.trim() || loading
                                                ? 0.5
                                                : 1,
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!e.target.disabled)
                                            e.target.style.backgroundColor =
                                                "#2563eb";
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!e.target.disabled)
                                            e.target.style.backgroundColor =
                                                "#3b82f6";
                                    }}
                                >
                                    {loading ? "Finding..." : "Find League"}
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
                            <span
                                style={{ color: "#dc2626", fontSize: "14px" }}
                            >
                                {error}
                            </span>
                            <button
                                onClick={loadLeagueInfo}
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

                    {/* League Info and Teams Table */}
                    {leagueInfo && (
                        <div
                            style={{
                                backgroundColor: "white",
                                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                                border: "1px solid #e2e8f0",
                                borderRadius: "8px",
                                overflow: "hidden",
                            }}
                        >
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
                                    {leagueInfo.name}
                                </h2>
                                <div
                                    style={{
                                        display: "flex",
                                        gap: "16px",
                                        alignItems: "center",
                                        fontSize: "14px",
                                        color: "#6b7280",
                                    }}
                                >
                                    <span>
                                        Created by: {leagueInfo.created_by}
                                    </span>
                                    <span>
                                        Teams:{" "}
                                        {leagueInfo.claimed_teams +
                                            leagueInfo.unclaimed_teams}{" "}
                                        / {leagueInfo.num_teams}
                                    </span>
                                    <span>
                                        Available: {leagueInfo.available_spots}
                                    </span>
                                </div>
                            </div>

                            {leagueInfo.unclaimed_teams > 0 ||
                            leagueInfo.available_spots > 0 ? (
                                <>
                                    {/* Table Headers */}
                                    <div
                                        style={{
                                            display: "grid",
                                            gridTemplateColumns:
                                                "8% 8% 25% 25% 22% 12%",
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
                                                textAlign: "center",
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
                                            }}
                                        >
                                            TEAM NAME
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
                                            MANAGER
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
                                            ACTION
                                        </div>
                                    </div>

                                    {/* Table Body */}
                                    <div
                                        style={{
                                            borderTop: "1px solid #f1f5f9",
                                        }}
                                    >
                                        {(() => {
                                            const allSlots = [];

                                            // Add actual teams
                                            members.forEach((member, index) => {
                                                allSlots.push({
                                                    type: "team",
                                                    data: member,
                                                    index: index + 1,
                                                });
                                            });

                                            // Add empty slots if can create new teams
                                            if (
                                                leagueInfo.available_spots > 0
                                            ) {
                                                allSlots.push({
                                                    type: "empty",
                                                    index: members.length + 1,
                                                });
                                            }

                                            return allSlots.map((slot) => (
                                                <div
                                                    key={
                                                        slot.type === "team"
                                                            ? slot.data.id
                                                            : "empty-new"
                                                    }
                                                    style={{
                                                        display: "grid",
                                                        gridTemplateColumns:
                                                            "8% 8% 25% 25% 22% 12%",
                                                        padding: "12px 0",
                                                        borderBottom:
                                                            "1px solid #f1f5f9",
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
                                                    {/* Position Number */}
                                                    <div
                                                        style={{
                                                            textAlign: "center",
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        <span
                                                            style={{
                                                                fontSize:
                                                                    "14px",
                                                                fontWeight:
                                                                    "500",
                                                                color: "#1f2937",
                                                            }}
                                                        >
                                                            {slot.index}
                                                        </span>
                                                    </div>

                                                    {/* Team Logo/Icon */}
                                                    <div
                                                        style={{
                                                            textAlign: "center",
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        {slot.type ===
                                                        "team" ? (
                                                            <div
                                                                style={{
                                                                    width: "32px",
                                                                    height: "32px",
                                                                    background:
                                                                        slot
                                                                            .data
                                                                            .user
                                                                            ? "linear-gradient(135deg, #3b82f6, #8b5cf6)"
                                                                            : "#f1f5f9",
                                                                    borderRadius:
                                                                        "50%",
                                                                    display:
                                                                        "flex",
                                                                    alignItems:
                                                                        "center",
                                                                    justifyContent:
                                                                        "center",
                                                                    boxShadow:
                                                                        "0 1px 3px rgba(0, 0, 0, 0.1)",
                                                                    margin: "0 auto",
                                                                }}
                                                            >
                                                                <span
                                                                    style={{
                                                                        color: slot
                                                                            .data
                                                                            .user
                                                                            ? "white"
                                                                            : "#64748b",
                                                                        fontSize:
                                                                            "12px",
                                                                        fontWeight:
                                                                            "bold",
                                                                    }}
                                                                >
                                                                    {slot.data.team_name
                                                                        .charAt(
                                                                            0
                                                                        )
                                                                        .toUpperCase()}
                                                                </span>
                                                            </div>
                                                        ) : (
                                                            <div
                                                                style={{
                                                                    width: "32px",
                                                                    height: "32px",
                                                                    backgroundColor:
                                                                        "#e2e8f0",
                                                                    borderRadius:
                                                                        "50%",
                                                                    display:
                                                                        "flex",
                                                                    alignItems:
                                                                        "center",
                                                                    justifyContent:
                                                                        "center",
                                                                    margin: "0 auto",
                                                                }}
                                                            >
                                                                <span
                                                                    style={{
                                                                        color: "#94a3b8",
                                                                        fontSize:
                                                                            "12px",
                                                                    }}
                                                                >
                                                                    +
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Team Name */}
                                                    <div
                                                        style={{
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        {slot.type ===
                                                        "team" ? (
                                                            <div
                                                                style={{
                                                                    fontSize:
                                                                        "14px",
                                                                    fontWeight:
                                                                        "500",
                                                                    color: "#1f2937",
                                                                }}
                                                            >
                                                                {
                                                                    slot.data
                                                                        .team_name
                                                                }
                                                            </div>
                                                        ) : creatingNewTeam ? (
                                                            <div
                                                                style={{
                                                                    display:
                                                                        "flex",
                                                                    gap: "4px",
                                                                    alignItems:
                                                                        "center",
                                                                }}
                                                            >
                                                                <input
                                                                    type="text"
                                                                    value={
                                                                        newTeamName
                                                                    }
                                                                    onChange={(
                                                                        e
                                                                    ) =>
                                                                        setNewTeamName(
                                                                            e
                                                                                .target
                                                                                .value
                                                                        )
                                                                    }
                                                                    placeholder="Enter team name..."
                                                                    style={{
                                                                        fontSize:
                                                                            "14px",
                                                                        padding:
                                                                            "4px 8px",
                                                                        border: "1px solid #d1d5db",
                                                                        borderRadius:
                                                                            "4px",
                                                                        flex: 1,
                                                                        outline:
                                                                            "none",
                                                                    }}
                                                                    autoFocus
                                                                    onKeyPress={(
                                                                        e
                                                                    ) => {
                                                                        if (
                                                                            e.key ===
                                                                            "Enter"
                                                                        )
                                                                            handleCreateTeam();
                                                                        if (
                                                                            e.key ===
                                                                            "Escape"
                                                                        )
                                                                            cancelCreatingTeam();
                                                                    }}
                                                                />
                                                            </div>
                                                        ) : (
                                                            <div
                                                                style={{
                                                                    fontSize:
                                                                        "14px",
                                                                    color: "#9ca3af",
                                                                    fontStyle:
                                                                        "italic",
                                                                }}
                                                            >
                                                                Available
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Manager Name */}
                                                    <div
                                                        style={{
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        {slot.type ===
                                                        "team" ? (
                                                            <div
                                                                style={{
                                                                    fontSize:
                                                                        "14px",
                                                                    color: "#1f2937",
                                                                }}
                                                            >
                                                                {slot.data.user
                                                                    ? slot.data
                                                                          .user
                                                                          .username
                                                                    : "Unclaimed"}
                                                            </div>
                                                        ) : (
                                                            <div
                                                                style={{
                                                                    fontSize:
                                                                        "14px",
                                                                    color: "#9ca3af",
                                                                }}
                                                            >
                                                                -
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Status */}
                                                    <div
                                                        style={{
                                                            textAlign: "center",
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                display: "flex",
                                                                flexWrap:
                                                                    "wrap",
                                                                gap: "4px",
                                                                justifyContent:
                                                                    "center",
                                                                alignItems:
                                                                    "center",
                                                            }}
                                                        >
                                                            {slot.type ===
                                                            "team" ? (
                                                                slot.data
                                                                    .user ? (
                                                                    <span
                                                                        style={{
                                                                            display:
                                                                                "inline-flex",
                                                                            alignItems:
                                                                                "center",
                                                                            padding:
                                                                                "4px 8px",
                                                                            borderRadius:
                                                                                "9999px",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontWeight:
                                                                                "500",
                                                                            backgroundColor:
                                                                                "#dcfce7",
                                                                            color: "#166534",
                                                                        }}
                                                                    >
                                                                        Joined
                                                                    </span>
                                                                ) : (
                                                                    <span
                                                                        style={{
                                                                            display:
                                                                                "inline-flex",
                                                                            alignItems:
                                                                                "center",
                                                                            padding:
                                                                                "4px 8px",
                                                                            borderRadius:
                                                                                "9999px",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontWeight:
                                                                                "500",
                                                                            backgroundColor:
                                                                                "#fef3c7",
                                                                            color: "#92400e",
                                                                        }}
                                                                    >
                                                                        Unclaimed
                                                                    </span>
                                                                )
                                                            ) : (
                                                                <span
                                                                    style={{
                                                                        display:
                                                                            "inline-flex",
                                                                        alignItems:
                                                                            "center",
                                                                        padding:
                                                                            "4px 8px",
                                                                        borderRadius:
                                                                            "9999px",
                                                                        fontSize:
                                                                            "12px",
                                                                        fontWeight:
                                                                            "500",
                                                                        backgroundColor:
                                                                            "#f1f5f9",
                                                                        color: "#475569",
                                                                    }}
                                                                >
                                                                    Open
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Action */}
                                                    <div
                                                        style={{
                                                            textAlign: "center",
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                display: "flex",
                                                                gap: "4px",
                                                                justifyContent:
                                                                    "center",
                                                                alignItems:
                                                                    "center",
                                                                flexWrap:
                                                                    "wrap",
                                                            }}
                                                        >
                                                            {slot.type ===
                                                            "team" ? (
                                                                !slot.data
                                                                    .user ? (
                                                                    <button
                                                                        onClick={() =>
                                                                            handleClaimTeam(
                                                                                slot
                                                                                    .data
                                                                                    .id
                                                                            )
                                                                        }
                                                                        disabled={
                                                                            joinLoading
                                                                        }
                                                                        style={{
                                                                            display:
                                                                                "inline-flex",
                                                                            alignItems:
                                                                                "center",
                                                                            padding:
                                                                                "4px 8px",
                                                                            border: "1px solid #34d399",
                                                                            borderRadius:
                                                                                "4px",
                                                                            backgroundColor:
                                                                                "transparent",
                                                                            color: "#34d399",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontWeight:
                                                                                "500",
                                                                            cursor: "pointer",
                                                                            transition:
                                                                                "all 0.15s",
                                                                            opacity:
                                                                                joinLoading
                                                                                    ? 0.5
                                                                                    : 1,
                                                                        }}
                                                                        onMouseEnter={(
                                                                            e
                                                                        ) => {
                                                                            if (
                                                                                !e
                                                                                    .target
                                                                                    .disabled
                                                                            ) {
                                                                                e.target.style.backgroundColor =
                                                                                    "#34d399";
                                                                                e.target.style.color =
                                                                                    "#ffffff";
                                                                            }
                                                                        }}
                                                                        onMouseLeave={(
                                                                            e
                                                                        ) => {
                                                                            if (
                                                                                !e
                                                                                    .target
                                                                                    .disabled
                                                                            ) {
                                                                                e.target.style.backgroundColor =
                                                                                    "transparent";
                                                                                e.target.style.color =
                                                                                    "#34d399";
                                                                            }
                                                                        }}
                                                                    >
                                                                        {joinLoading
                                                                            ? "Joining..."
                                                                            : "Claim"}
                                                                    </button>
                                                                ) : (
                                                                    <span
                                                                        style={{
                                                                            fontSize:
                                                                                "12px",
                                                                            color: "#9ca3af",
                                                                        }}
                                                                    >
                                                                        -
                                                                    </span>
                                                                )
                                                            ) : creatingNewTeam ? (
                                                                <div
                                                                    style={{
                                                                        display:
                                                                            "flex",
                                                                        gap: "2px",
                                                                    }}
                                                                >
                                                                    <button
                                                                        onClick={
                                                                            handleCreateTeam
                                                                        }
                                                                        disabled={
                                                                            !newTeamName.trim() ||
                                                                            joinLoading
                                                                        }
                                                                        style={{
                                                                            padding:
                                                                                "4px 8px",
                                                                            border: "1px solid #34d399",
                                                                            borderRadius:
                                                                                "4px",
                                                                            backgroundColor:
                                                                                "transparent",
                                                                            color: "#34d399",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontWeight:
                                                                                "500",
                                                                            cursor: "pointer",
                                                                            transition:
                                                                                "all 0.15s",
                                                                            opacity:
                                                                                !newTeamName.trim() ||
                                                                                joinLoading
                                                                                    ? 0.5
                                                                                    : 1,
                                                                        }}
                                                                    >
                                                                        ✓
                                                                    </button>
                                                                    <button
                                                                        onClick={
                                                                            cancelCreatingTeam
                                                                        }
                                                                        style={{
                                                                            padding:
                                                                                "4px 8px",
                                                                            border: "1px solid #ef4444",
                                                                            borderRadius:
                                                                                "4px",
                                                                            backgroundColor:
                                                                                "transparent",
                                                                            color: "#ef4444",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontWeight:
                                                                                "500",
                                                                            cursor: "pointer",
                                                                            transition:
                                                                                "all 0.15s",
                                                                        }}
                                                                    >
                                                                        ✕
                                                                    </button>
                                                                </div>
                                                            ) : (
                                                                <button
                                                                    onClick={
                                                                        startCreatingTeam
                                                                    }
                                                                    disabled={
                                                                        joinLoading
                                                                    }
                                                                    style={{
                                                                        display:
                                                                            "inline-flex",
                                                                        alignItems:
                                                                            "center",
                                                                        padding:
                                                                            "4px 8px",
                                                                        border: "1px solid #3b82f6",
                                                                        borderRadius:
                                                                            "4px",
                                                                        backgroundColor:
                                                                            "transparent",
                                                                        color: "#3b82f6",
                                                                        fontSize:
                                                                            "12px",
                                                                        fontWeight:
                                                                            "500",
                                                                        cursor: "pointer",
                                                                        transition:
                                                                            "all 0.15s",
                                                                        opacity:
                                                                            joinLoading
                                                                                ? 0.5
                                                                                : 1,
                                                                    }}
                                                                    onMouseEnter={(
                                                                        e
                                                                    ) => {
                                                                        if (
                                                                            !e
                                                                                .target
                                                                                .disabled
                                                                        ) {
                                                                            e.target.style.backgroundColor =
                                                                                "#3b82f6";
                                                                            e.target.style.color =
                                                                                "#ffffff";
                                                                        }
                                                                    }}
                                                                    onMouseLeave={(
                                                                        e
                                                                    ) => {
                                                                        if (
                                                                            !e
                                                                                .target
                                                                                .disabled
                                                                        ) {
                                                                            e.target.style.backgroundColor =
                                                                                "transparent";
                                                                            e.target.style.color =
                                                                                "#3b82f6";
                                                                        }
                                                                    }}
                                                                >
                                                                    Create
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ));
                                        })()}
                                    </div>
                                </>
                            ) : (
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
                                        League Full
                                    </p>
                                    <p
                                        style={{
                                            fontSize: "14px",
                                            marginBottom: "0",
                                        }}
                                    >
                                        This league is full and has no available
                                        spots.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Confirmation Modal */}
                {confirmationNeeded && (
                    <div
                        style={{
                            position: "fixed",
                            inset: 0,
                            backgroundColor: "rgba(0, 0, 0, 0.5)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            zIndex: 50,
                        }}
                    >
                        <div
                            style={{
                                backgroundColor: "white",
                                borderRadius: "8px",
                                padding: "24px",
                                maxWidth: "400px",
                                width: "100%",
                                margin: "16px",
                            }}
                        >
                            <h3
                                style={{
                                    fontSize: "18px",
                                    fontWeight: "700",
                                    marginBottom: "16px",
                                    color: "#1f2937",
                                }}
                            >
                                Multiple Teams Confirmation
                            </h3>
                            <p
                                style={{
                                    marginBottom: "16px",
                                    color: "#6b7280",
                                }}
                            >
                                {confirmationNeeded.message}
                            </p>
                            {confirmationNeeded.team_name && (
                                <p
                                    style={{
                                        fontSize: "14px",
                                        color: "#6b7280",
                                        marginBottom: "16px",
                                    }}
                                >
                                    Team: {confirmationNeeded.team_name}
                                </p>
                            )}
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "flex-end",
                                    gap: "12px",
                                }}
                            >
                                <button
                                    onClick={() => setConfirmationNeeded(null)}
                                    disabled={joinLoading}
                                    style={{
                                        padding: "8px 16px",
                                        border: "1px solid #d1d5db",
                                        borderRadius: "6px",
                                        backgroundColor: "transparent",
                                        color: "#374151",
                                        cursor: "pointer",
                                        transition: "all 0.15s",
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleConfirmMultiple}
                                    disabled={joinLoading}
                                    style={{
                                        padding: "8px 16px",
                                        border: "1px solid #10b981",
                                        borderRadius: "6px",
                                        backgroundColor: "#10b981",
                                        color: "#ffffff",
                                        cursor: "pointer",
                                        transition: "all 0.15s",
                                        opacity: joinLoading ? 0.5 : 1,
                                    }}
                                >
                                    {joinLoading
                                        ? "Joining..."
                                        : `Yes, create ${confirmationNeeded.ordinal} team`}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            <Footer />
        </div>
    );
};

export default JoinLeague;