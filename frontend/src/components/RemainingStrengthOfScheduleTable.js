import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import './styles/tableStyles.css';

const RemainingStrengthOfScheduleTable = ({ leagueId, leagueYear, week }) => {
    const [remainingStrengthOfScheduleData, setRemainingStrengthOfScheduleData] = useState(null);
    const [minWeek, setMinWeek] = useState(null);
    const [maxWeek, setMaxWeek] = useState(null);
    
    // Fetch remaining strength of schedule data
    useEffect(() => {
        const fetchRemainingStrengthOfScheduleData = async (week) => {
            try {
            const response = await fetch(
                `/api/remaining-strength-of-schedule/${leagueYear}/${leagueId}/?week=${week}`
            );
    
            if (!response.ok) {
                const errorData = await response.json();
                console.error("Backend error:", errorData);
                throw new Error(`Failed to fetch simulation data (status ${response.status})`);
            }
    
            const data = await response.json();
            setRemainingStrengthOfScheduleData(data.remaining_strength_of_schedule);
            setMinWeek(data.min_week > 0 ? data.min_week : null);
            setMaxWeek(data.max_week > 0 ? data.max_week : null);
            console.log("Remaining strength of schedule data fetched:", data);
            } catch (error) {
                console.error("Error fetching remaining strength of schedule data:", error);
            }
        };

        if (leagueYear && leagueId && week) {
            fetchRemainingStrengthOfScheduleData(week);
        }
    }, [leagueYear, leagueId, week]);

    console.log('minWeek:', minWeek);
    console.log('maxWeek:', maxWeek);

    return (
        <div className="wrapper-wide">
            <h2>
                Remaining Strength of Schedule
                {minWeek && maxWeek
                    ? minWeek === maxWeek
                        ? ` for Week ${minWeek}` // Show only one week if minWeek equals maxWeek
                        : ` for Weeks ${minWeek}-${maxWeek}` // Show range if minWeek and maxWeek are different
                    : ""}
            </h2>
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th className="team-name-column">Team</th>
                        <th className="team-name-column">Owner</th>
                        <th>Opponent Points For</th>
                        <th>Opponent Win %</th>
                        <th>Opponent Power Rank</th>
                        <th>Overall Difficulty</th>
                    </tr>
                </thead>
                <tbody>
                    {remainingStrengthOfScheduleData === null ? (
                        <LoadingRow text="Calculating remaining strength of schedule..." colSpan="6" />
                    ) : (
                        remainingStrengthOfScheduleData.map((team, index) => (
                            <tr key={index} className={index % 2 === 0 ? "even-row" : "odd-row"}>
                                <td className="team-name-column">{team.team}</td>
                                <td className="team-name-column">{team.owner}</td>
                                <td>{team.opp_points_for}</td>
                                <td>{team.opp_win_pct}</td>
                                <td>{team.opp_power_rank}</td>
                                <td>{team.overall_difficulty}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

RemainingStrengthOfScheduleTable.propTypes = {
    data: PropTypes.arrayOf(
        PropTypes.shape({
            team: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            opp_points_for: PropTypes.string.isRequired,
            opp_win_pct: PropTypes.string.isRequired,
            opp_power_rank: PropTypes.string.isRequired,
            overall_difficulty: PropTypes.string.isRequired,
        })
    ),
};

export default RemainingStrengthOfScheduleTable;
