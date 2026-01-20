import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePlayoffPoolAuth } from "../../components/PlayoffPool/AuthContext";
import playoffPoolAPI from "../../utils/PlayoffPool/api";
import ESPNStyleLeagueMembers from "../../components/PlayoffPool/ESPNStyleLeagueMembers";
import LeagueDetails from "../../components/PlayoffPool/LeagueDetails";
import ScoringSettingsEditor from "../../components/PlayoffPool/ScoringSettingsEditor";
import LeaderBoard from "../../components/PlayoffPool/LeaderBoard";
import Footer from "../../components/Footer";
const LeagueDetail = () => {
    const { leagueId } = useParams();
    const navigate = useNavigate();
    const { user } = usePlayoffPoolAuth();
    const leaderboardRef = useRef(null);

    const [league, setLeague] = useState(null);
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [selectedTeamForInvite, setSelectedTeamForInvite] = useState(null);
    const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
    const [teamToRemove, setTeamToRemove] = useState(null);
    const [showScoringEditor, setShowScoringEditor] = useState(false);
    const [showResetConfirm, setShowResetConfirm] = useState(false);
    const [resetLoading, setResetLoading] = useState(false);

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
                playoffPoolAPI.getLeagueMembers(leagueId),
            ]);

            setLeague(leagueData);
            setMembers(membersData);
        } catch (err) {
            setError("Failed to load league data");
            console.error("Error loading league:", err);
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

    const handleEditTeams = () => {
        navigate(`/playoff-pool/league/${leagueId}/edit-teams`);
    };

    const handleBackToDashboard = () => {
        navigate("/playoff-pool");
    };

    const handleDeleteLeague = async () => {
        if (!isAdmin) {
            alert("Only league administrators can delete the league");
            return;
        }

        const confirmMessage = `Are you sure you want to delete the league "${league?.name}"? This action cannot be undone and will remove all teams, drafts, and league data.`;

        if (!window.confirm(confirmMessage)) {
            return;
        }

        try {
            await playoffPoolAPI.deleteLeague(leagueId);
            alert("League deleted successfully");
            navigate("/playoff-pool");
        } catch (err) {
            alert(err.response?.data?.error || "Failed to delete league");
            console.error("Error deleting league:", err);
        }
    };

    const handleOpenScoringEditor = () => {
        setShowScoringEditor(true);
    };

    const handleCloseScoringEditor = () => {
        setShowScoringEditor(false);
    };

    const handleScoringSettingsSaved = () => {
        setShowScoringEditor(false);
        // Reload leaderboard to reflect new fantasy point calculations
        if (leaderboardRef.current) {
            leaderboardRef.current.reload();
        }
    };

    const handleResetDraft = async () => {
        if (resetLoading) return;

        setResetLoading(true);
        try {
            await playoffPoolAPI.resetDraft(leagueId);
            setShowResetConfirm(false);
            await loadLeagueData(); // Refresh league data
        } catch (error) {
            console.error("Reset draft error:", error);
            alert(error.response?.data?.error || "Failed to reset draft");
        } finally {
            setResetLoading(false);
        }
    };

    const handleCreateTeam = async (teamName) => {
        if (!teamName || !teamName.trim()) {
            alert("Please enter a team name");
            return;
        }

        try {
            await playoffPoolAPI.createTeam(leagueId, teamName.trim());
            await loadLeagueData(); // Refresh data
        } catch (err) {
            alert(err.response?.data?.error || "Failed to create team");
            throw err; // Re-throw so the component can handle it
        }
    };

    const handleInviteFriend = (teamId, teamName) => {
        const inviteLink = `${window.location.origin}/playoff-pool/join?league=${leagueId}&team=${teamId}`;
        const message = `Join my NFL playoff pool "${league?.name}"! Click this link to claim the ${teamName} team: ${inviteLink}`;

        if (navigator.clipboard) {
            navigator.clipboard
                .writeText(message)
                .then(() => {
                    alert("Invite message copied to clipboard!");
                })
                .catch(() => {
                    // Fallback
                    prompt("Copy this invite message:", message);
                });
        } else {
            // Fallback for older browsers
            prompt("Copy this invite message:", message);
        }
    };

    const handleInviteToLeague = () => {
        const inviteLink = `${window.location.origin}/playoff-pool/join?league=${leagueId}`;
        const message = `Join my NFL playoff pool "${league?.name}"! Click this link to join: ${inviteLink}`;

        if (navigator.clipboard) {
            navigator.clipboard
                .writeText(message)
                .then(() => {
                    alert("League invite link copied to clipboard!");
                })
                .catch(() => {
                    // Fallback
                    prompt("Copy this league invite link:", message);
                });
        } else {
            // Fallback for older browsers
            prompt("Copy this league invite link:", message);
        }
    };

    const handleRemoveTeam = async (teamId) => {
        try {
            console.log(
                "Attempting to remove team:",
                teamId,
                "from league:",
                leagueId
            );
            await playoffPoolAPI.removeTeam(leagueId, teamId);
            console.log("Team removed successfully");
            setShowRemoveConfirm(false);
            setTeamToRemove(null);
            await loadLeagueData(); // Refresh data
        } catch (err) {
            console.error("Remove team error:", err);
            console.error("Error response:", err.response);
            alert(err.response?.data?.error || "Failed to remove team");
        }
    };

    const confirmRemoveTeam = (team) => {
        setTeamToRemove(team);
        setShowRemoveConfirm(true);
    };

    const handleClaimTeam = async (team) => {
        try {
            const response = await playoffPoolAPI.claimTeam(leagueId, team.id);

            // Check if confirmation is required for multiple teams
            if (response.requires_confirmation) {
                const confirmed = window.confirm(response.message);
                if (confirmed) {
                    // Retry with confirmation
                    await playoffPoolAPI.claimTeam(leagueId, team.id, true);
                    await loadLeagueData(); // Refresh data
                }
            } else {
                await loadLeagueData(); // Refresh data
            }
        } catch (err) {
            console.error("Claim team error:", err);
            alert(err.response?.data?.error || "Failed to claim team");
        }
    };

    const handleUnclaimTeam = async (team) => {
        const confirmed = window.confirm(
            `Are you sure you want to unclaim "${team.team_name}"? This will make it available for others to claim.`
        );

        if (confirmed) {
            try {
                await playoffPoolAPI.unclaimTeam(leagueId, team.id);
                await loadLeagueData(); // Refresh data
            } catch (err) {
                console.error("Unclaim team error:", err);
                alert(err.response?.data?.error || "Failed to unclaim team");
            }
        }
    };

    const isAdmin = league?.user_membership?.is_admin;
    const canStartDraft =
        isAdmin && !league?.is_draft_complete && !league?.draft_started_at;
    const draftInProgress =
        league?.draft_started_at && !league?.is_draft_complete;
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
                    ← Back to Dashboard
                </button>
            </div>
        );
    }

    return (
        <>
            <div className="min-h-screen bg-gray-50 py-8">
                <div className="container mx-auto px-4">
                    {/* Header */}
                    <div className="mb-8">
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "12px",
                                marginBottom: "16px",
                            }}
                        >
                            <button
                                onClick={handleBackToDashboard}
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
                                }}
                                onMouseEnter={(e) =>
                                    (e.target.style.backgroundColor = "#4b5563")
                                }
                                onMouseLeave={(e) =>
                                    (e.target.style.backgroundColor = "#6b7280")
                                }
                            >
                                ← Back to Dashboard
                            </button>

                            <button
                                onClick={handleInviteToLeague}
                                style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    padding: "8px 16px",
                                    backgroundColor: "#3b82f6",
                                    color: "white",
                                    fontWeight: "500",
                                    fontSize: "13px",
                                    borderRadius: "6px",
                                    border: "none",
                                    cursor: "pointer",
                                    transition: "background-color 0.15s",
                                    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                                }}
                                onMouseEnter={(e) =>
                                    (e.target.style.backgroundColor = "#2563eb")
                                }
                                onMouseLeave={(e) =>
                                    (e.target.style.backgroundColor = "#3b82f6")
                                }
                            >
                                📧 Invite to League
                            </button>
                        </div>
                    </div>

                    {/* League Details Widget - Always visible */}
                    <div className="mb-8">
                        <LeagueDetails
                            league={league}
                            members={members}
                            isAdmin={isAdmin}
                            draftInProgress={draftInProgress}
                            draftComplete={draftComplete}
                            handleStartDraft={handleStartDraft}
                            handleViewDraftedTeams={handleViewDraftedTeams}
                            handleEditTeams={handleEditTeams}
                            handleOpenScoringEditor={handleOpenScoringEditor}
                            handleResetDraft={() => setShowResetConfirm(true)}
                        />
                    </div>

                    {/* League Members - Show only before draft starts */}
                    {!draftInProgress && !draftComplete && (
                        <div className="grid grid-cols-1 gap-8">
                            <div>
                                <ESPNStyleLeagueMembers
                                    league={league}
                                    members={members}
                                    user={user}
                                    isAdmin={isAdmin}
                                    handleInviteFriend={handleInviteFriend}
                                    confirmRemoveTeam={confirmRemoveTeam}
                                    handleClaimTeam={handleClaimTeam}
                                    handleUnclaimTeam={handleUnclaimTeam}
                                    handleCreateTeam={handleCreateTeam}
                                    handleDeleteLeague={handleDeleteLeague}
                                    leagueId={leagueId}
                                    actionButtons={
                                        <div
                                            style={{
                                                display: "flex",
                                                justifyContent: "flex-end",
                                                alignItems: "center",
                                                gap: "12px",
                                                flexWrap: "wrap",
                                            }}
                                        >
                                            {canStartDraft && (
                                                <button
                                                    onClick={handleStartDraft}
                                                    style={{
                                                        display: "inline-flex",
                                                        alignItems: "center",
                                                        padding: "12px 20px",
                                                        backgroundColor:
                                                            "#10b981",
                                                        color: "white",
                                                        fontWeight: "600",
                                                        fontSize: "14px",
                                                        borderRadius: "8px",
                                                        border: "none",
                                                        cursor: "pointer",
                                                        transition:
                                                            "background-color 0.15s",
                                                        boxShadow:
                                                            "0 1px 3px rgba(0, 0, 0, 0.1)",
                                                    }}
                                                    onMouseEnter={(e) =>
                                                        (e.target.style.backgroundColor =
                                                            "#059669")
                                                    }
                                                    onMouseLeave={(e) =>
                                                        (e.target.style.backgroundColor =
                                                            "#10b981")
                                                    }
                                                >
                                                    Start Draft
                                                </button>
                                            )}

                                            <button
                                                onClick={
                                                    handleOpenScoringEditor
                                                }
                                                style={{
                                                    display: "inline-flex",
                                                    alignItems: "center",
                                                    padding: "12px 20px",
                                                    backgroundColor: "#7c3aed",
                                                    color: "white",
                                                    fontWeight: "600",
                                                    fontSize: "14px",
                                                    borderRadius: "8px",
                                                    border: "none",
                                                    cursor: "pointer",
                                                    transition:
                                                        "background-color 0.15s",
                                                    boxShadow:
                                                        "0 1px 3px rgba(0, 0, 0, 0.1)",
                                                }}
                                                onMouseEnter={(e) =>
                                                    (e.target.style.backgroundColor =
                                                        "#6d28d9")
                                                }
                                                onMouseLeave={(e) =>
                                                    (e.target.style.backgroundColor =
                                                        "#7c3aed")
                                                }
                                            >
                                                {isAdmin
                                                    ? "Edit Scoring Settings"
                                                    : "Show Scoring Settings"}
                                            </button>

                                            {members.length <
                                                league?.num_teams && (
                                                <div
                                                    style={{
                                                        display: "flex",
                                                        alignItems: "center",
                                                        padding: "8px 12px",
                                                        backgroundColor:
                                                            "#fef3c7",
                                                        color: "#92400e",
                                                        fontSize: "14px",
                                                        borderRadius: "8px",
                                                        fontWeight: "500",
                                                    }}
                                                >
                                                    ⏳ Waiting for more members
                                                    to join...
                                                </div>
                                            )}
                                        </div>
                                    }
                                />
                            </div>
                        </div>
                    )}

                    {/* LeaderBoard */}
                    <LeaderBoard
                        ref={leaderboardRef}
                        leagueId={leagueId}
                        isDraftComplete={draftComplete}
                    />
                </div>
            </div>

            {/* Remove Team Confirmation Modal - positioned as proper overlay */}
            {showRemoveConfirm && teamToRemove && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
                    style={{
                        position: "fixed",
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        zIndex: 999999,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                    onClick={(e) => {
                        // Close modal if clicking the overlay
                        if (e.target === e.currentTarget) {
                            setShowRemoveConfirm(false);
                            setTeamToRemove(null);
                        }
                    }}
                >
                    <div
                        className="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 p-6"
                        style={{
                            position: "relative",
                            zIndex: 1000000,
                            backgroundColor: "white",
                            borderRadius: "8px",
                            padding: "24px",
                            margin: "16px",
                            maxWidth: "400px",
                            width: "100%",
                            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3
                            style={{
                                fontSize: "18px",
                                fontWeight: "bold",
                                marginBottom: "16px",
                                color: "#dc2626",
                            }}
                        >
                            Remove Team
                        </h3>
                        <p
                            style={{
                                marginBottom: "16px",
                                color: "#374151",
                                lineHeight: "1.5",
                            }}
                        >
                            Are you sure you want to remove{" "}
                            <strong>{teamToRemove.team_name}</strong>
                            {teamToRemove.user && (
                                <span>
                                    {" "}
                                    (managed by{" "}
                                    <strong>
                                        {teamToRemove.user.username}
                                    </strong>
                                    )
                                </span>
                            )}
                            ? This action cannot be undone.
                        </p>
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "flex-end",
                                gap: "12px",
                            }}
                        >
                            <button
                                onClick={() => {
                                    setShowRemoveConfirm(false);
                                    setTeamToRemove(null);
                                }}
                                style={{
                                    padding: "8px 16px",
                                    border: "1px solid #d1d5db",
                                    borderRadius: "6px",
                                    backgroundColor: "white",
                                    color: "#374151",
                                    cursor: "pointer",
                                    fontSize: "14px",
                                    fontWeight: "500",
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() =>
                                    handleRemoveTeam(teamToRemove.id)
                                }
                                style={{
                                    padding: "8px 16px",
                                    border: "none",
                                    borderRadius: "6px",
                                    backgroundColor: "#dc2626",
                                    color: "white",
                                    cursor: "pointer",
                                    fontSize: "14px",
                                    fontWeight: "500",
                                }}
                            >
                                Remove Team
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reset Draft Confirmation Modal */}
            {showResetConfirm && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
                    style={{
                        position: "fixed",
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        zIndex: 999999,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                    onClick={(e) => {
                        if (e.target === e.currentTarget) {
                            setShowResetConfirm(false);
                        }
                    }}
                >
                    <div
                        className="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 p-6"
                        style={{
                            position: "relative",
                            zIndex: 1000000,
                            backgroundColor: "white",
                            borderRadius: "8px",
                            padding: "24px",
                            margin: "16px",
                            maxWidth: "500px",
                            width: "100%",
                            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3
                            style={{
                                fontSize: "18px",
                                fontWeight: "bold",
                                marginBottom: "16px",
                                color: "#dc2626",
                            }}
                        >
                            Reset Draft
                        </h3>
                        <p
                            style={{
                                marginBottom: "20px",
                                color: "#374151",
                                lineHeight: "1.5",
                            }}
                        >
                            <strong>Warning:</strong> This will completely reset
                            the draft and remove all drafted players from all
                            teams. This action cannot be undone.
                        </p>
                        <p
                            style={{
                                marginBottom: "20px",
                                color: "#6b7280",
                                fontSize: "14px",
                                lineHeight: "1.4",
                            }}
                        >
                            • All drafted players will be returned to the
                            available pool
                            <br />
                            • Draft order will be reset
                            <br />• Draft status will be set to "not started"
                        </p>
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "flex-end",
                                gap: "12px",
                            }}
                        >
                            <button
                                onClick={() => setShowResetConfirm(false)}
                                disabled={resetLoading}
                                style={{
                                    padding: "8px 16px",
                                    border: "1px solid #d1d5db",
                                    borderRadius: "6px",
                                    backgroundColor: "white",
                                    color: "#374151",
                                    cursor: resetLoading
                                        ? "not-allowed"
                                        : "pointer",
                                    fontSize: "14px",
                                    fontWeight: "500",
                                    opacity: resetLoading ? 0.5 : 1,
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleResetDraft}
                                disabled={resetLoading}
                                style={{
                                    padding: "8px 16px",
                                    border: "none",
                                    borderRadius: "6px",
                                    backgroundColor: "#dc2626",
                                    color: "white",
                                    cursor: resetLoading
                                        ? "not-allowed"
                                        : "pointer",
                                    fontSize: "14px",
                                    fontWeight: "500",
                                    opacity: resetLoading ? 0.5 : 1,
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "8px",
                                }}
                            >
                                {resetLoading ? "Resetting..." : "Reset Draft"}
                                {resetLoading && (
                                    <div
                                        style={{
                                            width: "16px",
                                            height: "16px",
                                            border: "2px solid rgba(255,255,255,0.3)",
                                            borderTop: "2px solid white",
                                            borderRadius: "50%",
                                            animation:
                                                "spin 1s linear infinite",
                                        }}
                                    />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Scoring Settings Editor */}
            {showScoringEditor && (
                <ScoringSettingsEditor
                    leagueId={leagueId}
                    onClose={handleCloseScoringEditor}
                    onSave={handleScoringSettingsSaved}
                    readOnly={false}
                    isAdmin={isAdmin}
                    draftInProgress={draftInProgress}
                    draftComplete={draftComplete}
                />
            )}
            <Footer />
        </>
    );
};

export default LeagueDetail;
