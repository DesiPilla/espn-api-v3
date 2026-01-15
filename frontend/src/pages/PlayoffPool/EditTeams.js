import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePlayoffPoolAuth } from "../../components/PlayoffPool/AuthContext";
import playoffPoolAPI from "../../utils/PlayoffPool/api";
import ESPNStyleLeagueMembers from "../../components/PlayoffPool/ESPNStyleLeagueMembers";
import Footer from "../../components/Footer";

const EditTeams = () => {
    const { leagueId } = useParams();
    const navigate = useNavigate();
    const { user } = usePlayoffPoolAuth();

    const [league, setLeague] = useState(null);
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [selectedTeamForInvite, setSelectedTeamForInvite] = useState(null);
    const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
    const [teamToRemove, setTeamToRemove] = useState(null);

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

    const handleBackToLeague = () => {
        navigate(`/playoff-pool/league/${leagueId}`);
    };

    const handleInviteFriend = (teamId) => {
        setSelectedTeamForInvite(teamId);
        setShowInviteModal(true);
    };

    const handleSendInvite = async (email) => {
        try {
            await playoffPoolAPI.sendInvite(
                leagueId,
                email,
                selectedTeamForInvite
            );
            alert("Invitation sent successfully!");
            setShowInviteModal(false);
            setSelectedTeamForInvite(null);
        } catch (err) {
            alert(
                err.response?.data?.error ||
                    "Failed to send invite. Please check the email address."
            );
        }
    };

    const confirmRemoveTeam = (teamId, teamName) => {
        setTeamToRemove({ id: teamId, name: teamName });
        setShowRemoveConfirm(true);
    };

    const handleRemoveTeam = async () => {
        try {
            await playoffPoolAPI.removeTeamFromLeague(
                leagueId,
                teamToRemove.id
            );
            await loadLeagueData();
            setShowRemoveConfirm(false);
            setTeamToRemove(null);
        } catch (err) {
            alert(err.response?.data?.error || "Failed to remove team");
        }
    };

    const handleClaimTeam = async (teamId) => {
        try {
            await playoffPoolAPI.claimTeam(leagueId, teamId);
            await loadLeagueData();
        } catch (err) {
            alert(err.response?.data?.error || "Failed to claim team");
        }
    };

    const handleUnclaimTeam = async (teamId) => {
        try {
            await playoffPoolAPI.unclaimTeam(leagueId, teamId);
            await loadLeagueData();
        } catch (err) {
            alert(err.response?.data?.error || "Failed to unclaim team");
        }
    };

    const handleCreateTeam = async (teamName) => {
        try {
            await playoffPoolAPI.createTeam(leagueId, teamName);
            await loadLeagueData();
        } catch (err) {
            throw err;
        }
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

    const isAdmin = league?.user_membership?.is_admin;

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="flex justify-center">
                    <div className="text-lg">Loading teams...</div>
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
                    onClick={handleBackToLeague}
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                    Back to League
                </button>
            </div>
        );
    }

    return (
        <>
            <div className="min-h-screen bg-gray-50">
                <div className="container mx-auto px-4 py-8">
                    {/* Header */}
                    <div className="mb-6">
                        <button
                            onClick={handleBackToLeague}
                            className="mb-4 text-blue-600 hover:text-blue-800 flex items-center"
                        >
                            ← Back to League
                        </button>
                        <h1 className="text-3xl font-bold text-gray-900">
                            Edit Teams - {league?.name}
                        </h1>
                    </div>

                    {/* League Members */}
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
                            actionButtons={null}
                        />
                    </div>
                </div>
            </div>

            {/* Remove Team Confirmation Modal */}
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
                    onClick={() => {
                        setShowRemoveConfirm(false);
                        setTeamToRemove(null);
                    }}
                >
                    <div
                        className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
                        style={{
                            position: "relative",
                            zIndex: 1000000,
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-bold mb-4">
                            Confirm Team Removal
                        </h3>
                        <p className="mb-6">
                            Are you sure you want to remove "{teamToRemove.name}
                            " from the league?
                        </p>
                        <div className="flex justify-end space-x-4">
                            <button
                                onClick={() => {
                                    setShowRemoveConfirm(false);
                                    setTeamToRemove(null);
                                }}
                                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRemoveTeam}
                                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                            >
                                Remove
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Invite Modal */}
            {showInviteModal && (
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
                    onClick={() => {
                        setShowInviteModal(false);
                        setSelectedTeamForInvite(null);
                    }}
                >
                    <div
                        className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
                        style={{
                            position: "relative",
                            zIndex: 1000000,
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-bold mb-4">
                            Invite Friend
                        </h3>
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                const email =
                                    e.target.elements.email.value.trim();
                                if (email) {
                                    handleSendInvite(email);
                                }
                            }}
                        >
                            <div className="mb-4">
                                <label className="block text-sm font-medium mb-2">
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    name="email"
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required
                                />
                            </div>
                            <div className="flex justify-end space-x-4">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowInviteModal(false);
                                        setSelectedTeamForInvite(null);
                                    }}
                                    className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                >
                                    Send Invite
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <Footer />
        </>
    );
};

export default EditTeams;
