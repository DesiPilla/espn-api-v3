import React, { useEffect, useState } from 'react';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const LeaderBoard = ({ leagueId, isDraftComplete }) => {
    const [teamsData, setTeamsData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isDraftComplete && leagueId) {
            loadLeaderboardData();
        }
    }, [leagueId, isDraftComplete]);

    const loadLeaderboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Use getPlayoffStats instead of getDraftedTeams for accurate round-by-round scoring
            const playoffData = await playoffPoolAPI.getPlayoffStats(leagueId);
            setTeamsData(playoffData);
        } catch (err) {
            console.error('Error loading leaderboard data:', err);
            setError('Failed to load leaderboard data');
        } finally {
            setLoading(false);
        }
    };

    // Don't render anything if draft is not complete
    if (!isDraftComplete) {
        return null;
    }

    if (loading) {
        return (
            <div style={{ 
                padding: '20px', 
                textAlign: 'center',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                marginTop: '24px'
            }}>
                Loading leaderboard...
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ 
                padding: '20px', 
                textAlign: 'center',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                marginTop: '24px',
                color: '#dc2626'
            }}>
                {error}
            </div>
        );
    }

    if (!teamsData || !teamsData.teams || teamsData.teams.length === 0) {
        return null;
    }

    const teams = teamsData.teams;

    // Calculate team round totals from individual players' round_points
    const processedTeams = teams.map(team => {
        const roundTotals = {
            WC: 0,
            DIV: 0,
            CON: 0,
            SB: 0,
        };

        // Sum up each player's round points for the team
        team.players.forEach((player) => {
            if (player.round_points) {
                roundTotals.WC += player.round_points.WC || 0;
                roundTotals.DIV += player.round_points.DIV || 0;
                roundTotals.CON += player.round_points.CON || 0;
                roundTotals.SB += player.round_points.SB || 0;
            }
        });

        // Calculate total from round totals instead of using backend total_points
        const calculatedTotal =
            roundTotals.WC + roundTotals.DIV + roundTotals.CON + roundTotals.SB;

        return {
            ...team,
            roundTotals,
            total_points: calculatedTotal, // Use our calculated total
        };
    });

    // Sort teams by total points (descending)
    const sortedTeams = [...processedTeams].sort((a, b) => {
        const aTotal = a.total_points || 0;
        const bTotal = b.total_points || 0;
        return bTotal - aTotal;
    });

    return (
        <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
            marginTop: '24px'
        }}>
            {/* Header */}
            <div style={{
                backgroundColor: '#f8fafc',
                borderBottom: '1px solid #e2e8f0',
                padding: '16px 20px'
            }}>
                <h3 style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1f2937',
                    margin: '0'
                }}>
                    🏆 Leaderboard
                </h3>
            </div>

            {/* Table */}
            <div style={{ overflow: 'auto' }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'collapse'
                }}>
                    <thead>
                        <tr style={{ backgroundColor: '#f9fafb' }}>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'left',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                Rank
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'left',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                Team Name
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'left',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                Owner
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'center',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                WC
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'center',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                DIV
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'center',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                CON
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'center',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                SB
                            </th>
                            <th style={{
                                padding: '12px 16px',
                                textAlign: 'center',
                                fontSize: '12px',
                                fontWeight: '600',
                                color: '#374151',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                borderBottom: '1px solid #e5e7eb'
                            }}>
                                Total
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedTeams.map((team, index) => {
                            const isFirstPlace = index === 0 && team.total_points > 0;
                            const isSecondPlace = index === 1 && team.total_points > 0;
                            const isThirdPlace = index === 2 && team.total_points > 0;
                            
                            let rankDisplay = index + 1;
                            if (isFirstPlace) rankDisplay = '🥇';
                            else if (isSecondPlace) rankDisplay = '🥈';
                            else if (isThirdPlace) rankDisplay = '🥉';

                            return (
                                <tr 
                                    key={`${team.user?.id || "unclaimed"}-${team.team_name}`}
                                    style={{
                                        backgroundColor: isFirstPlace ? '#fef3c7' : 
                                                        isSecondPlace ? '#f3f4f6' :
                                                        isThirdPlace ? '#fdf2f8' : 'white',
                                        borderBottom: '1px solid #f3f4f6'
                                    }}
                                >
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        color: '#1f2937'
                                    }}>
                                        {rankDisplay}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        color: '#1f2937'
                                    }}>
                                        {team.team_name}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        color: '#6b7280'
                                    }}>
                                        {team.user?.username || 'Unclaimed'}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        color: '#374151',
                                        textAlign: 'center'
                                    }}>
                                        {(team.roundTotals.WC || 0).toFixed(1)}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        color: '#374151',
                                        textAlign: 'center'
                                    }}>
                                        {(team.roundTotals.DIV || 0).toFixed(1)}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        color: '#374151',
                                        textAlign: 'center'
                                    }}>
                                        {(team.roundTotals.CON || 0).toFixed(1)}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        color: '#374151',
                                        textAlign: 'center'
                                    }}>
                                        {(team.roundTotals.SB || 0).toFixed(1)}
                                    </td>
                                    <td style={{
                                        padding: '12px 16px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        color: '#1f2937',
                                        textAlign: 'center'
                                    }}>
                                        {(team.total_points || 0).toFixed(1)}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Footer note if all scores are zero */}
            {sortedTeams.every(team => (team.total_points || 0) === 0) && (
                <div style={{
                    padding: '16px 20px',
                    backgroundColor: '#f9fafb',
                    borderTop: '1px solid #e5e7eb',
                    fontSize: '14px',
                    color: '#6b7280',
                    textAlign: 'center'
                }}>
                    Scores will update as playoff games are played.
                </div>
            )}
        </div>
    );
};

export default LeaderBoard;