import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePlayoffPoolAuth } from "../../components/PlayoffPool/AuthContext";
import playoffPoolAPI from "../../utils/PlayoffPool/api";

const DraftInterface = () => {
    const { leagueId } = useParams();
    const navigate = useNavigate();

    const [league, setLeague] = useState(null);
    const [members, setMembers] = useState([]);
    const [availablePlayers, setAvailablePlayers] = useState([]);
    const [draftedPlayers, setDraftedPlayers] = useState([]);
    const [teamRosters, setTeamRosters] = useState({});
    const [selectedPlayer, setSelectedPlayer] = useState(null);
    const [selectedUser, setSelectedUser] = useState(null);
    const [filterPosition, setFilterPosition] = useState("ALL");
    const [searchTerm, setSearchTerm] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [playersPerPage] = useState(10);
    const [loading, setLoading] = useState(true);
    const [draftLoading, setDraftLoading] = useState(false);
    const [undoLoading, setUndoLoading] = useState(false);
    const [resetLoading, setResetLoading] = useState(false);
    const [showResetWarning, setShowResetWarning] = useState(false);
    const [error, setError] = useState(null);
    const [showRosterPanel, setShowRosterPanel] = useState(false);
    const [selectedRosterTeam, setSelectedRosterTeam] = useState("");

    useEffect(() => {
        if (leagueId) {
            loadDraftData();
        }
    }, [leagueId]);

    // Initialize selectedRosterTeam to first team when members are loaded
    useEffect(() => {
        if (members.length > 0 && !selectedRosterTeam) {
            const firstMember = members[0];
            const firstTeamId =
                firstMember.user?.id || `unclaimed_${firstMember.team_name}`;
            setSelectedRosterTeam(firstTeamId);
        }
    }, [members, selectedRosterTeam]);

    const loadDraftData = async (skipLoadingState = false) => {
        try {
            if (!skipLoadingState) {
                setLoading(true);
            }
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
                const teamsData = await playoffPoolAPI.getDraftedTeams(
                    leagueId
                );
                const allDrafted = [];
                const teamRostersByUser = {};

                teamsData.teams.forEach((team) => {
                    const userId =
                        team.user?.id || `unclaimed_${team.team_name}`;
                    teamRostersByUser[userId] = {
                        ...team,
                        playersByPosition: {},
                    };

                    team.players.forEach((player) => {
                        // Add fantasy team info to player object for Recent Picks display
                        const playerWithTeam = {
                            ...player,
                            fantasy_team_name: team.team_name,
                            fantasy_team_user: team.user,
                        };
                        allDrafted.push(playerWithTeam);

                        // Group players by position for this team
                        const position = player.position;
                        if (
                            !teamRostersByUser[userId].playersByPosition[
                                position
                            ]
                        ) {
                            teamRostersByUser[userId].playersByPosition[
                                position
                            ] = [];
                        }
                        teamRostersByUser[userId].playersByPosition[
                            position
                        ].push(player);
                    });
                });

                setDraftedPlayers(allDrafted);
                setTeamRosters(teamRostersByUser);
            } catch (err) {
                console.warn("No drafted players yet");
                setTeamRosters({});
            }
        } catch (err) {
            setError("Failed to load draft data");
            console.error("Error loading draft data:", err);
        } finally {
            if (!skipLoadingState) {
                setLoading(false);
            }
        }
    };

    // Helper function to get position limits for a team
    const getPositionLimits = (league) => {
        if (!league?.roster_config) return {};

        const limits = {};
        Object.entries(league.roster_config).forEach(([position, count]) => {
            if (position === "flex") {
                // Handle flex positions separately - keep the entire flex config
                limits.flex = count; // This should be the entire flex configuration object
            } else {
                limits[position] = count;
            }
        });

        return limits;
    };

    // Check if a team can draft a player in a specific position
    const canDraftPosition = (teamId, position) => {
        if (!league?.roster_config || !teamRosters[teamId]) return true;

        const positionLimits = getPositionLimits(league);
        const teamRoster = teamRosters[teamId];
        const playersAtPosition =
            teamRoster.playersByPosition[position]?.length || 0;

        // Get direct position limit
        const directLimit = positionLimits[position] || 0;

        // Check if direct limit is exceeded
        const directLimitExceeded =
            directLimit > 0 && playersAtPosition >= directLimit;

        // Check if this position is FLEX-eligible
        const isFlexEligible =
            positionLimits.flex &&
            positionLimits.flex.eligible_positions &&
            positionLimits.flex.eligible_positions.includes(position);

        // If direct limit is exceeded OR position has no direct limit but is flex-eligible,
        // check FLEX availability
        if (directLimitExceeded || (directLimit === 0 && isFlexEligible)) {
            if (isFlexEligible) {
                const flexEligiblePositions =
                    positionLimits.flex.eligible_positions;

                // Count total flex eligible players
                const totalFlexPlayers = flexEligiblePositions.reduce(
                    (sum, pos) => {
                        return (
                            sum +
                            (teamRoster.playersByPosition[pos]?.length || 0)
                        );
                    },
                    0
                );

                // Calculate how many flex spots are available
                const usedDirectSpots = flexEligiblePositions.reduce(
                    (sum, pos) => {
                        const directLimit = positionLimits[pos] || 0;
                        const playersAtPos =
                            teamRoster.playersByPosition[pos]?.length || 0;
                        return sum + Math.min(playersAtPos, directLimit);
                    },
                    0
                );

                const availableFlexSpots =
                    (positionLimits.flex.count || 0) -
                    (totalFlexPlayers - usedDirectSpots);
                return availableFlexSpots > 0;
            } else {
                // Position has direct limit but can't use FLEX
                return false;
            }
        }

        // If we have a direct limit and haven't exceeded it, allow the draft
        if (directLimit > 0 && playersAtPosition < directLimit) {
            return true;
        }

        // If no direct limit and not flex-eligible, block the draft
        if (directLimit === 0 && !isFlexEligible) {
            return false;
        }

        return true;
    };

    // Get roster summary for a team
    const getTeamRosterSummary = (teamId) => {
        if (!teamRosters[teamId] || !league?.roster_config) return {};

        const summary = {};
        const positionLimits = getPositionLimits(league);
        const teamRoster = teamRosters[teamId];

        Object.keys(positionLimits).forEach((position) => {
            if (position === "flex") {
                const flexConfig = positionLimits.flex;
                const eligiblePositions = flexConfig.eligible_positions || [
                    "RB",
                    "WR",
                    "TE",
                ];
                const totalEligible = eligiblePositions.reduce((sum, pos) => {
                    return (
                        sum + (teamRoster.playersByPosition[pos]?.length || 0)
                    );
                }, 0);

                summary.flex = {
                    current: Math.max(
                        0,
                        totalEligible -
                            eligiblePositions.reduce((sum, pos) => {
                                return (
                                    sum +
                                    Math.min(
                                        teamRoster.playersByPosition[pos]
                                            ?.length || 0,
                                        positionLimits[pos] || 0
                                    )
                                );
                            }, 0)
                    ),
                    max: flexConfig.count || 0,
                };
            } else {
                summary[position] = {
                    current:
                        teamRoster.playersByPosition[position]?.length || 0,
                    max: positionLimits[position] || 0,
                };
            }
        });

        return summary;
    };

    // Create individual roster slots based on roster configuration
    const createRosterSlots = (teamId) => {
        if (!league?.roster_config) return [];

        const slots = [];
        const positionLimits = getPositionLimits(league);
        const teamRoster = teamRosters[teamId];

        // Create slots for each position in order: QB, RB, WR, TE, FLEX, DST, K
        const positionOrder = ["QB", "RB", "WR", "TE", "flex", "DST", "K"];

        positionOrder.forEach((position) => {
            if (positionLimits[position]) {
                const count =
                    position === "flex"
                        ? positionLimits.flex.count
                        : positionLimits[position];

                for (let i = 0; i < count; i++) {
                    let slotPlayer = null;

                    if (position === "flex") {
                        // For flex, find eligible players that aren't already in direct position slots
                        const eligiblePositions = positionLimits.flex
                            .eligible_positions || ["RB", "WR", "TE"];
                        const allFlexEligible = [];

                        eligiblePositions.forEach((pos) => {
                            const posPlayers =
                                teamRoster?.playersByPosition[pos] || [];
                            allFlexEligible.push(...posPlayers);
                        });

                        // Sort by draft order to assign to flex consistently
                        allFlexEligible.sort(
                            (a, b) => a.draft_order - b.draft_order
                        );

                        // Skip players already assigned to direct positions
                        let flexAssignedCount = 0;
                        eligiblePositions.forEach((pos) => {
                            const directLimit = positionLimits[pos] || 0;
                            flexAssignedCount += directLimit;
                        });

                        if (allFlexEligible[flexAssignedCount + i]) {
                            slotPlayer = allFlexEligible[flexAssignedCount + i];
                        }
                    } else {
                        // Direct position assignment
                        const positionPlayers =
                            teamRoster?.playersByPosition[position] || [];
                        if (positionPlayers[i]) {
                            slotPlayer = positionPlayers[i];
                        }
                    }

                    slots.push({
                        position: position === "flex" ? "FLEX" : position,
                        player: slotPlayer,
                        slotIndex: i,
                        isEmpty: !slotPlayer,
                    });
                }
            }
        });

        return slots;
    };

    const handleDraftPlayer = async () => {
        if (!selectedPlayer || !selectedUser) {
            // Allow drafting to unclaimed teams (selectedUser can be null)
            if (!selectedPlayer || selectedUser === undefined) {
                alert("Please select a player and a team");
                return;
            }
        }

        // Validate roster limits
        const teamId =
            selectedUser?.user?.id || `unclaimed_${selectedUser?.team_name}`;
        const playerPosition = selectedPlayer.position;

        if (!canDraftPosition(teamId, playerPosition)) {
            alert(
                `Cannot draft ${selectedPlayer.name} (${playerPosition}). Team roster is full for this position.`
            );
            return;
        }

        try {
            setDraftLoading(true);

            // Use team_id (membership id) for specificity, allow null user
            await playoffPoolAPI.draftPlayer(
                leagueId,
                selectedPlayer.gsis_id,
                selectedUser?.user?.id || null,
                selectedUser?.id || null
            );

            // Reload draft data to update UI without showing main loading state
            await loadDraftData(true);

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

    const handleResetDraft = () => {
        setShowResetWarning(true);
    };

    const confirmResetDraft = async () => {
        try {
            setResetLoading(true);
            setShowResetWarning(false);
            await playoffPoolAPI.resetDraft(leagueId);
            // Reload data to reflect changes
            await loadDraftData();
            alert("Draft has been successfully reset!");
        } catch (err) {
            alert(err.response?.data?.error || "Failed to reset draft");
            console.error("Error resetting draft:", err);
        } finally {
            setResetLoading(false);
        }
    };

    const cancelResetDraft = () => {
        setShowResetWarning(false);
    };

    // Filter players based on position and search term
    const filteredPlayers = availablePlayers
        .filter((player) => {
            const matchesPosition =
                filterPosition === "ALL" ||
                player.position === filterPosition ||
                (filterPosition === "FLEX" &&
                    league?.roster_config?.flex?.eligible_positions?.includes(
                        player.position
                    ));
            const matchesSearch =
                !searchTerm ||
                player.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                player.team.toLowerCase().includes(searchTerm.toLowerCase());
            return matchesPosition && matchesSearch;
        })
        .sort((a, b) => {
            // Primary sort by draft value (descending)
            if (b.draft_value !== a.draft_value) {
                return b.draft_value - a.draft_value;
            }
            // Secondary sort by regular season points (descending)
            if (b.fantasy_points !== a.fantasy_points) {
                return b.fantasy_points - a.fantasy_points;
            }
            // Tertiary sort by player name for consistency
            const nameA = a.name || "";
            const nameB = b.name || "";
            return nameA.localeCompare(nameB);
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

    const positions = React.useMemo(() => {
        if (!league || !league.positions_included) {
            return ["ALL", ...new Set(availablePlayers.map((p) => p.position))];
        }
        const basePositions = [
            "ALL",
            ...league.positions_included.filter((pos) =>
                availablePlayers.some((p) => p.position === pos)
            ),
        ];

        // Add FLEX if flex is configured
        if (
            league.roster_config &&
            league.roster_config.flex &&
            league.roster_config.flex.count > 0
        ) {
            basePositions.push("FLEX");
        }

        return basePositions;
    }, [league, availablePlayers]);
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
        <>
            <style>
                {`
                    @keyframes spin {
                        from {
                            transform: rotate(0deg);
                        }
                        to {
                            transform: rotate(360deg);
                        }
                    }
                `}
            </style>
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="container mx-auto px-4">
                    {/* Header */}
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            marginBottom: "24px",
                        }}
                    >
                        <div>
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
                        <div
                            style={{
                                display: "flex",
                                gap: "12px",
                                marginTop: "32px",
                            }}
                        >
                            <button
                                onClick={handleResetDraft}
                                disabled={
                                    resetLoading || draftedPlayers.length === 0
                                }
                                style={{
                                    background:
                                        resetLoading ||
                                        draftedPlayers.length === 0
                                            ? "#9ca3af"
                                            : "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "12px",
                                    padding: "12px 24px",
                                    fontSize: "16px",
                                    fontWeight: "600",
                                    cursor:
                                        resetLoading ||
                                        draftedPlayers.length === 0
                                            ? "not-allowed"
                                            : "pointer",
                                    boxShadow:
                                        resetLoading ||
                                        draftedPlayers.length === 0
                                            ? "none"
                                            : "0 4px 12px rgba(245, 158, 11, 0.3)",
                                    transition: "all 0.2s ease",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                                onMouseEnter={(e) => {
                                    if (
                                        !resetLoading &&
                                        draftedPlayers.length > 0
                                    ) {
                                        e.target.style.transform =
                                            "translateY(-1px)";
                                        e.target.style.boxShadow =
                                            "0 6px 16px rgba(245, 158, 11, 0.4)";
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (
                                        !resetLoading &&
                                        draftedPlayers.length > 0
                                    ) {
                                        e.target.style.transform =
                                            "translateY(0)";
                                        e.target.style.boxShadow =
                                            "0 4px 12px rgba(245, 158, 11, 0.3)";
                                    }
                                }}
                                title={
                                    draftedPlayers.length === 0
                                        ? "No draft picks to reset"
                                        : "Reset the entire draft"
                                }
                            >
                                {resetLoading
                                    ? "🔄 Resetting..."
                                    : "🔄 Reset Draft"}
                            </button>
                            <button
                                onClick={handleCompleteDraft}
                                style={{
                                    background:
                                        "linear-gradient(135deg, #dc2626 0%, #991b1b 100%)",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "12px",
                                    padding: "12px 24px",
                                    fontSize: "16px",
                                    fontWeight: "600",
                                    cursor: "pointer",
                                    boxShadow:
                                        "0 4px 12px rgba(220, 38, 38, 0.3)",
                                    transition: "all 0.2s ease",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.transform =
                                        "translateY(-1px)";
                                    e.target.style.boxShadow =
                                        "0 6px 16px rgba(220, 38, 38, 0.4)";
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.transform = "translateY(0)";
                                    e.target.style.boxShadow =
                                        "0 4px 12px rgba(220, 38, 38, 0.3)";
                                }}
                                title="Finalize and close the draft"
                            >
                                🏁 Complete Draft
                            </button>
                        </div>
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
                                        {Math.min(
                                            endIndex,
                                            filteredPlayers.length
                                        )}{" "}
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
                                                    handleFilterChange(
                                                        e.target.value
                                                    )
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
                                                    <option
                                                        key={pos}
                                                        value={pos}
                                                    >
                                                        {pos}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div
                                            style={{
                                                flex: 1,
                                                minWidth: "200px",
                                                display: "flex",
                                                alignItems: "center",
                                                gap: "8px",
                                            }}
                                        >
                                            <label
                                                style={{
                                                    fontSize: "12px",
                                                    fontWeight: "500",
                                                    color: "#64748b",
                                                    textTransform: "uppercase",
                                                    letterSpacing: "0.05em",
                                                    whiteSpace: "nowrap",
                                                }}
                                            >
                                                SEARCH:
                                            </label>
                                            <input
                                                type="text"
                                                placeholder="Search players or teams..."
                                                value={searchTerm}
                                                onChange={(e) =>
                                                    handleSearchChange(
                                                        e.target.value
                                                    )
                                                }
                                                style={{
                                                    padding: "6px 12px",
                                                    border: "1px solid #d1d5db",
                                                    borderRadius: "6px",
                                                    fontSize: "14px",
                                                    flex: 1,
                                                    maxWidth: "300px",
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
                                            "5% 8% 20% 8% 14% 10% 10% 15% 10%",
                                        backgroundColor: "#f1f5f9",
                                        borderBottom: "1px solid #e2e8f0",
                                    }}
                                >
                                    <div
                                        style={{
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
                                            fontSize: "12px",
                                            fontWeight: "500",
                                            color: "#64748b",
                                            textTransform: "uppercase",
                                            letterSpacing: "0.05em",
                                            textAlign: "center",
                                        }}
                                    >
                                        DRAFT VALUE
                                    </div>
                                    <div
                                        style={{
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                        const globalRank =
                                            startIndex + index + 1;
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
                                                        "5% 8% 20% 8% 14% 10% 10% 15% 10%",
                                                    padding: "12px 0",
                                                    borderBottom:
                                                        "1px solid #f1f5f9",
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
                                                            display:
                                                                "inline-block",
                                                            padding: "4px 8px",
                                                            borderRadius:
                                                                "12px",
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
                                                {/* Player Name and Info */}
                                                <div
                                                    style={{ padding: "0 8px" }}
                                                >
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
                                                            display:
                                                                "inline-block",
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
                                                {/* Draft Value */}
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
                                                            color: "#059669",
                                                        }}
                                                    >
                                                        {(
                                                            player.draft_value ||
                                                            0
                                                        ).toFixed(1)}
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
                                                                setSelectedUser(
                                                                    null
                                                                );
                                                            } else {
                                                                setSelectedPlayer(
                                                                    player
                                                                );
                                                                setSelectedUser(
                                                                    null
                                                                );
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
                                                            transition:
                                                                "all 0.15s",
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
                                                                selectedUser?.id ||
                                                                ""
                                                            }
                                                            style={{
                                                                padding:
                                                                    "4px 8px",
                                                                fontSize:
                                                                    "12px",
                                                                borderRadius:
                                                                    "4px",
                                                                border: "1px solid #d1d5db",
                                                                backgroundColor:
                                                                    "#ffffff",
                                                                color: "#374151",
                                                                width: "100%",
                                                                maxWidth:
                                                                    "130px",
                                                            }}
                                                            onChange={(e) => {
                                                                const selectedMember =
                                                                    members.find(
                                                                        (m) =>
                                                                            m.id.toString() ===
                                                                            e
                                                                                .target
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
                                                            {members.map(
                                                                (member) => {
                                                                    const teamId =
                                                                        member
                                                                            .user
                                                                            ?.id ||
                                                                        `unclaimed_${member.team_name}`;
                                                                    const canDraft =
                                                                        canDraftPosition(
                                                                            teamId,
                                                                            player.position
                                                                        );
                                                                    return (
                                                                        <option
                                                                            key={
                                                                                member.id
                                                                            }
                                                                            value={
                                                                                member.id
                                                                            }
                                                                            style={{
                                                                                color: canDraft
                                                                                    ? "#374151"
                                                                                    : "#9ca3af",
                                                                                backgroundColor:
                                                                                    canDraft
                                                                                        ? "white"
                                                                                        : "#f9fafb",
                                                                            }}
                                                                            disabled={
                                                                                !canDraft
                                                                            }
                                                                        >
                                                                            {
                                                                                member.team_name
                                                                            }
                                                                            {!canDraft &&
                                                                                " (Position Full)"}
                                                                        </option>
                                                                    );
                                                                }
                                                            )}
                                                        </select>
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
                                                    )}
                                                </div>;
                                                {
                                                    /* Draft Button - Only for selected player with team */
                                                }
                                                <div
                                                    style={{
                                                        textAlign: "center",
                                                        padding: "0 4px",
                                                    }}
                                                >
                                                    {isSelected &&
                                                    selectedUser ? (
                                                        (() => {
                                                            const teamId =
                                                                selectedUser
                                                                    ?.user
                                                                    ?.id ||
                                                                `unclaimed_${selectedUser?.team_name}`;
                                                            const canDraft =
                                                                canDraftPosition(
                                                                    teamId,
                                                                    player.position
                                                                );
                                                            const isDisabled =
                                                                draftLoading ||
                                                                !canDraft;

                                                            return (
                                                                <button
                                                                    onClick={() => {
                                                                        setSelectedPlayer(
                                                                            player
                                                                        );
                                                                        setTimeout(
                                                                            () => {
                                                                                handleDraftPlayer();
                                                                            },
                                                                            0
                                                                        );
                                                                    }}
                                                                    disabled={
                                                                        isDisabled
                                                                    }
                                                                    style={{
                                                                        padding:
                                                                            "4px 8px",
                                                                        fontSize:
                                                                            "11px",
                                                                        fontWeight:
                                                                            "500",
                                                                        borderRadius:
                                                                            "4px",
                                                                        border: `1px solid ${
                                                                            canDraft
                                                                                ? "#10b981"
                                                                                : "#dc2626"
                                                                        }`,
                                                                        backgroundColor:
                                                                            isDisabled
                                                                                ? "#9ca3af"
                                                                                : draftLoading
                                                                                ? "#059669"
                                                                                : canDraft
                                                                                ? "#10b981"
                                                                                : "#dc2626",
                                                                        color: "#ffffff",
                                                                        cursor: isDisabled
                                                                            ? "not-allowed"
                                                                            : "pointer",
                                                                        transition:
                                                                            "all 0.15s",
                                                                        minWidth:
                                                                            "50px",
                                                                        whiteSpace:
                                                                            "nowrap",
                                                                        display:
                                                                            "inline-flex",
                                                                        alignItems:
                                                                            "center",
                                                                        justifyContent:
                                                                            "center",
                                                                        gap: "4px",
                                                                    }}
                                                                    title={
                                                                        !canDraft
                                                                            ? "Position roster is full"
                                                                            : ""
                                                                    }
                                                                    onMouseEnter={(
                                                                        e
                                                                    ) => {
                                                                        if (
                                                                            !isDisabled &&
                                                                            canDraft
                                                                        ) {
                                                                            e.target.style.backgroundColor =
                                                                                "#059669";
                                                                        }
                                                                    }}
                                                                    onMouseLeave={(
                                                                        e
                                                                    ) => {
                                                                        if (
                                                                            !isDisabled &&
                                                                            canDraft
                                                                        ) {
                                                                            e.target.style.backgroundColor =
                                                                                "#10b981";
                                                                        }
                                                                    }}
                                                                >
                                                                    {draftLoading && (
                                                                        <svg
                                                                            style={{
                                                                                animation:
                                                                                    "spin 1s linear infinite",
                                                                                width: "12px",
                                                                                height: "12px",
                                                                            }}
                                                                            xmlns="http://www.w3.org/2000/svg"
                                                                            fill="none"
                                                                            viewBox="0 0 24 24"
                                                                        >
                                                                            <circle
                                                                                style={{
                                                                                    opacity: 0.25,
                                                                                }}
                                                                                cx="12"
                                                                                cy="12"
                                                                                r="10"
                                                                                stroke="currentColor"
                                                                                strokeWidth="4"
                                                                            />
                                                                            <path
                                                                                style={{
                                                                                    opacity: 0.75,
                                                                                }}
                                                                                fill="currentColor"
                                                                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                                            />
                                                                        </svg>
                                                                    )}
                                                                    {draftLoading
                                                                        ? "Drafting..."
                                                                        : !canDraft
                                                                        ? "Full"
                                                                        : "Draft"}
                                                                </button>
                                                            );
                                                        })()
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
                                                    )}
                                                </div>;
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
                                            No players found matching your
                                            search criteria
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
                                            disabled={
                                                currentPage === totalPages
                                            }
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
                        <div
                            className="xl:col-span-1 space-y-6"
                            style={{ marginTop: "24px" }}
                        >
                            {/* Team Roster Panel */}
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
                                        padding: "16px 20px",
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >
                                    <h3
                                        style={{
                                            fontSize: "16px",
                                            fontWeight: "600",
                                            color: "#1f2937",
                                            margin: 0,
                                        }}
                                    >
                                        Team Rosters
                                    </h3>
                                    <button
                                        onClick={() =>
                                            setShowRosterPanel(!showRosterPanel)
                                        }
                                        style={{
                                            padding: "4px 8px",
                                            fontSize: "12px",
                                            backgroundColor: showRosterPanel
                                                ? "#3b82f6"
                                                : "#e5e7eb",
                                            color: showRosterPanel
                                                ? "white"
                                                : "#374151",
                                            border: "none",
                                            borderRadius: "4px",
                                            cursor: "pointer",
                                        }}
                                    >
                                        {showRosterPanel ? "Hide" : "Show"}
                                    </button>
                                </div>

                                {/* Roster Content */}
                                {showRosterPanel && (
                                    <div style={{ padding: "16px" }}>
                                        {/* Team Dropdown */}
                                        <div style={{ marginBottom: "16px" }}>
                                            <label
                                                style={{
                                                    display: "block",
                                                    fontSize: "14px",
                                                    fontWeight: "600",
                                                    color: "#374151",
                                                    marginBottom: "8px",
                                                }}
                                            >
                                                Select Team
                                            </label>
                                            <select
                                                value={selectedRosterTeam}
                                                onChange={(e) =>
                                                    setSelectedRosterTeam(
                                                        e.target.value
                                                    )
                                                }
                                                style={{
                                                    width: "100%",
                                                    padding: "8px 12px",
                                                    border: "1px solid #d1d5db",
                                                    borderRadius: "6px",
                                                    backgroundColor: "white",
                                                    fontSize: "14px",
                                                }}
                                            >
                                                <option value="">
                                                    Choose a team...
                                                </option>
                                                {Object.entries(
                                                    teamRosters
                                                ).map(([teamId, roster]) => (
                                                    <option
                                                        key={teamId}
                                                        value={teamId}
                                                    >
                                                        {roster.team_name}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Roster Display */}
                                        {selectedRosterTeam &&
                                        teamRosters[selectedRosterTeam] ? (
                                            <div>
                                                {/* Position Tracker */}
                                                <div
                                                    style={{
                                                        marginBottom: "16px",
                                                        padding: "12px",
                                                        backgroundColor:
                                                            "#f8fafc",
                                                        borderRadius: "6px",
                                                        border: "1px solid #e2e8f0",
                                                    }}
                                                >
                                                    <h4
                                                        style={{
                                                            fontSize: "14px",
                                                            fontWeight: "600",
                                                            color: "#374151",
                                                            margin: "0 0 8px 0",
                                                        }}
                                                    >
                                                        Position Tracker
                                                    </h4>
                                                    <div
                                                        style={{
                                                            display: "grid",
                                                            gridTemplateColumns:
                                                                "repeat(auto-fit, minmax(80px, 1fr))",
                                                            gap: "8px",
                                                        }}
                                                    >
                                                        {[
                                                            "QB",
                                                            "RB",
                                                            "WR",
                                                            "TE",
                                                            "flex",
                                                            "DST",
                                                            "K",
                                                        ]
                                                            .map((position) => {
                                                                const summary =
                                                                    getTeamRosterSummary(
                                                                        selectedRosterTeam
                                                                    );
                                                                const counts =
                                                                    summary[
                                                                        position
                                                                    ];
                                                                if (!counts)
                                                                    return null;
                                                                const isEmpty =
                                                                    counts.current ===
                                                                    0;
                                                                const isPartial =
                                                                    counts.current >
                                                                        0 &&
                                                                    counts.current <
                                                                        counts.max;
                                                                const isFull =
                                                                    counts.current ===
                                                                    counts.max;

                                                                return (
                                                                    <div
                                                                        key={
                                                                            position
                                                                        }
                                                                        style={{
                                                                            padding:
                                                                                "6px 8px",
                                                                            borderRadius:
                                                                                "4px",
                                                                            fontSize:
                                                                                "11px",
                                                                            fontWeight:
                                                                                "600",
                                                                            textAlign:
                                                                                "center",
                                                                            backgroundColor:
                                                                                isEmpty
                                                                                    ? "#e5e7eb"
                                                                                    : isPartial
                                                                                    ? "#fef3c7"
                                                                                    : "#dcfce7",
                                                                            color: isEmpty
                                                                                ? "#6b7280"
                                                                                : isPartial
                                                                                ? "#d97706"
                                                                                : "#166534",
                                                                            border: `1px solid ${
                                                                                isEmpty
                                                                                    ? "#d1d5db"
                                                                                    : isPartial
                                                                                    ? "#fbbf24"
                                                                                    : "#16a34a"
                                                                            }`,
                                                                        }}
                                                                    >
                                                                        {(position ===
                                                                        "flex"
                                                                            ? "FLEX"
                                                                            : position
                                                                        ).toUpperCase()}
                                                                        <br />
                                                                        {
                                                                            counts.current
                                                                        }
                                                                        /
                                                                        {
                                                                            counts.max
                                                                        }
                                                                    </div>
                                                                );
                                                            })
                                                            .filter(Boolean)}
                                                    </div>
                                                </div>

                                                {/* Roster Breakdown */}
                                                <div>
                                                    <h4
                                                        style={{
                                                            fontSize: "14px",
                                                            fontWeight: "600",
                                                            color: "#1f2937",
                                                            margin: "0 0 12px 0",
                                                            borderBottom:
                                                                "1px solid #e5e7eb",
                                                            paddingBottom:
                                                                "8px",
                                                        }}
                                                    >
                                                        Roster Breakdown
                                                    </h4>
                                                    <div
                                                        style={{
                                                            display: "flex",
                                                            flexDirection:
                                                                "column",
                                                            gap: "6px",
                                                        }}
                                                    >
                                                        {createRosterSlots(
                                                            selectedRosterTeam
                                                        ).map((slot, index) => (
                                                            <div
                                                                key={`${slot.position}-${slot.slotIndex}`}
                                                                style={{
                                                                    display:
                                                                        "flex",
                                                                    justifyContent:
                                                                        "space-between",
                                                                    alignItems:
                                                                        "center",
                                                                    padding:
                                                                        "8px 12px",
                                                                    backgroundColor:
                                                                        slot.isEmpty
                                                                            ? "#f9fafb"
                                                                            : "#f0f9ff",
                                                                    borderRadius:
                                                                        "6px",
                                                                    border: `1px solid ${
                                                                        slot.isEmpty
                                                                            ? "#e5e7eb"
                                                                            : "#bfdbfe"
                                                                    }`,
                                                                    minHeight:
                                                                        "40px",
                                                                }}
                                                            >
                                                                <span
                                                                    style={{
                                                                        fontWeight:
                                                                            "600",
                                                                        color:
                                                                            slot.position ===
                                                                            "FLEX"
                                                                                ? "#7c3aed"
                                                                                : "#2563eb",
                                                                        fontSize:
                                                                            "12px",
                                                                        minWidth:
                                                                            "40px",
                                                                    }}
                                                                >
                                                                    {
                                                                        slot.position
                                                                    }
                                                                </span>

                                                                {slot.player ? (
                                                                    <div
                                                                        style={{
                                                                            display:
                                                                                "flex",
                                                                            alignItems:
                                                                                "center",
                                                                            gap: "8px",
                                                                            flex: 1,
                                                                            justifyContent:
                                                                                "flex-end",
                                                                        }}
                                                                    >
                                                                        <div
                                                                            style={{
                                                                                textAlign:
                                                                                    "right",
                                                                            }}
                                                                        >
                                                                            <div
                                                                                style={{
                                                                                    fontSize:
                                                                                        "13px",
                                                                                    fontWeight:
                                                                                        "500",
                                                                                    color: "#1f2937",
                                                                                }}
                                                                            >
                                                                                {
                                                                                    slot
                                                                                        .player
                                                                                        .player_name
                                                                                }
                                                                            </div>
                                                                            <div
                                                                                style={{
                                                                                    fontSize:
                                                                                        "11px",
                                                                                    color: "#6b7280",
                                                                                }}
                                                                            >
                                                                                {
                                                                                    slot
                                                                                        .player
                                                                                        .nfl_team
                                                                                }{" "}
                                                                                •{" "}
                                                                                {slot.player.fantasy_points?.toFixed(
                                                                                    1
                                                                                )}{" "}
                                                                                pts
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                ) : (
                                                                    <span
                                                                        style={{
                                                                            color: "#9ca3af",
                                                                            fontSize:
                                                                                "12px",
                                                                            fontStyle:
                                                                                "italic",
                                                                        }}
                                                                    >
                                                                        Empty
                                                                    </span>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <div
                                                style={{
                                                    textAlign: "center",
                                                    color: "#9ca3af",
                                                    padding: "20px",
                                                }}
                                            >
                                                {Object.entries(teamRosters)
                                                    .length === 0
                                                    ? "No teams have drafted players yet"
                                                    : "Select a team to view their roster"}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Recent Picks - ESPN Style Table */}
                            <div
                                style={{
                                    backgroundColor: "white",
                                    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                                    border: "1px solid #e2e8f0",
                                    borderRadius: "8px",
                                    overflow: "hidden",
                                    marginTop: "24px",
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
                                        gridTemplateColumns:
                                            "8% 15% 30% 15% 20% 12%",
                                        backgroundColor: "#f1f5f9",
                                        borderBottom: "1px solid #e2e8f0",
                                    }}
                                >
                                    <div
                                        style={{
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                            padding: "8px 4px",
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
                                                        backgroundColor:
                                                            isLatestPick
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
                                                                fontSize:
                                                                    "14px",
                                                                fontWeight:
                                                                    "600",
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
                                                                padding:
                                                                    "4px 8px",
                                                                borderRadius:
                                                                    "12px",
                                                                fontSize:
                                                                    "12px",
                                                                fontWeight:
                                                                    "600",
                                                                backgroundColor:
                                                                    {
                                                                        QB: "#dbeafe",
                                                                        RB: "#dcfce7",
                                                                        WR: "#fef3c7",
                                                                        TE: "#f3e8ff",
                                                                        K: "#fee2e2",
                                                                        DST: "#e0f2fe",
                                                                    }[
                                                                        pick
                                                                            .position
                                                                    ] ||
                                                                    "#f1f5f9",
                                                                color:
                                                                    {
                                                                        QB: "#1e40af",
                                                                        RB: "#166534",
                                                                        WR: "#92400e",
                                                                        TE: "#7c3aed",
                                                                        K: "#dc2626",
                                                                        DST: "#0369a1",
                                                                    }[
                                                                        pick
                                                                            .position
                                                                    ] ||
                                                                    "#64748b",
                                                            }}
                                                        >
                                                            {pick.position}
                                                        </span>
                                                    </div>

                                                    {/* Player Name */}
                                                    <div
                                                        style={{
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                fontSize:
                                                                    "14px",
                                                                fontWeight:
                                                                    "500",
                                                                color: "#1f2937",
                                                            }}
                                                        >
                                                            {pick.player_name}
                                                        </div>
                                                        {/* NFL Team (under player name) */}
                                                        <div
                                                            style={{
                                                                fontSize:
                                                                    "12px",
                                                                color: "#6b7280",
                                                            }}
                                                        >
                                                            {pick.nfl_team ||
                                                                pick.team ||
                                                                "N/A"}
                                                        </div>
                                                    </div>

                                                    {/* Fantasy Team Name */}
                                                    <div
                                                        style={{
                                                            padding: "0 8px",
                                                        }}
                                                    >
                                                        <div
                                                            style={{
                                                                fontSize:
                                                                    "14px",
                                                                color: "#1f2937",
                                                            }}
                                                        >
                                                            {pick.fantasy_team_name ||
                                                                "Unknown Team"}
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
                                                                fontSize:
                                                                    "12px",
                                                                color: "#6b7280",
                                                            }}
                                                        >
                                                            {(() => {
                                                                try {
                                                                    const draftDate =
                                                                        pick.drafted_at_est ||
                                                                        pick.drafted_at;
                                                                    if (
                                                                        !draftDate
                                                                    )
                                                                        return "N/A";

                                                                    const date =
                                                                        new Date(
                                                                            draftDate
                                                                        );
                                                                    if (
                                                                        isNaN(
                                                                            date.getTime()
                                                                        )
                                                                    )
                                                                        return "Invalid Date";

                                                                    return (
                                                                        date.toLocaleString(
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
                                                                        ) +
                                                                        " EST"
                                                                    );
                                                                } catch (error) {
                                                                    return "Invalid Date";
                                                                }
                                                            })()}
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
                                                                disabled={
                                                                    undoLoading
                                                                }
                                                                style={{
                                                                    padding:
                                                                        "4px 8px",
                                                                    fontSize:
                                                                        "12px",
                                                                    fontWeight:
                                                                        "500",
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
                                                                onMouseEnter={(
                                                                    e
                                                                ) => {
                                                                    if (
                                                                        !undoLoading
                                                                    ) {
                                                                        e.target.style.backgroundColor =
                                                                            "#fecaca";
                                                                    }
                                                                }}
                                                                onMouseLeave={(
                                                                    e
                                                                ) => {
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
                                                                    fontSize:
                                                                        "12px",
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
                        ;
                    </div>
                </div>

                {/* Reset Draft Warning Modal */}
                {showResetWarning && (
                    <div
                        style={{
                            position: "fixed",
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: "rgba(0, 0, 0, 0.7)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            zIndex: 1001,
                        }}
                    >
                        <div
                            style={{
                                backgroundColor: "white",
                                borderRadius: "12px",
                                padding: "32px",
                                maxWidth: "500px",
                                width: "90%",
                                boxShadow: "0 20px 25px rgba(0, 0, 0, 0.15)",
                            }}
                        >
                            <div
                                style={{
                                    textAlign: "center",
                                    marginBottom: "24px",
                                }}
                            >
                                <div
                                    style={{
                                        width: "48px",
                                        height: "48px",
                                        backgroundColor: "#dc2626",
                                        borderRadius: "50%",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        margin: "0 auto 16px",
                                        fontSize: "24px",
                                    }}
                                >
                                    ⚠️
                                </div>
                                <h3
                                    style={{
                                        fontSize: "20px",
                                        fontWeight: "bold",
                                        color: "#1f2937",
                                        margin: "0 0 8px 0",
                                    }}
                                >
                                    Warning: Reset Entire Draft
                                </h3>
                                <p
                                    style={{
                                        fontSize: "14px",
                                        color: "#6b7280",
                                        lineHeight: "1.5",
                                        margin: 0,
                                    }}
                                >
                                    This will delete ALL draft picks and return
                                    the league to "ready to draft" status. This
                                    action cannot be undone.
                                </p>
                            </div>

                            <div
                                style={{
                                    padding: "20px",
                                    backgroundColor: "#fef2f2",
                                    borderRadius: "8px",
                                    marginBottom: "24px",
                                    border: "1px solid #f87171",
                                }}
                            >
                                <p
                                    style={{
                                        fontSize: "14px",
                                        color: "#991b1b",
                                        fontWeight: "500",
                                        margin: 0,
                                    }}
                                >
                                    {draftedPlayers.length > 0
                                        ? `This will remove ${draftedPlayers.length} draft picks. All teams will need to re-draft their players.`
                                        : "No draft picks found to reset."}
                                </p>
                            </div>

                            <div
                                style={{
                                    display: "flex",
                                    gap: "12px",
                                    justifyContent: "flex-end",
                                }}
                            >
                                <button
                                    onClick={cancelResetDraft}
                                    style={{
                                        padding: "12px 20px",
                                        backgroundColor: "white",
                                        border: "1px solid #d1d5db",
                                        borderRadius: "8px",
                                        fontSize: "14px",
                                        fontWeight: "500",
                                        color: "#374151",
                                        cursor: "pointer",
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmResetDraft}
                                    disabled={resetLoading}
                                    style={{
                                        padding: "12px 20px",
                                        backgroundColor: resetLoading
                                            ? "#fca5a5"
                                            : "#dc2626",
                                        border: "none",
                                        borderRadius: "8px",
                                        fontSize: "14px",
                                        fontWeight: "500",
                                        color: "white",
                                        cursor: resetLoading
                                            ? "not-allowed"
                                            : "pointer",
                                    }}
                                >
                                    {resetLoading
                                        ? "Resetting..."
                                        : "Reset Draft"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default DraftInterface;
