import React from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import PendingDataNotice from "./PendingDataNotice";
import CopyableContainer from "./CopyableContainer";
import './styles/tableStyles.css';

const PlayoffOddsTable = ({
    data,
    playoffTeams,
    selectedWeek,
    pendingData,
}) => {
    return (
        <CopyableContainer
            title={`Playoff Odds (prior to Week ${selectedWeek} matchups)`}
            fileName={`playoff-odds-week-${selectedWeek}`}
        >
            <PendingDataNotice
                dataType="playoff odds"
                isPending={pendingData}
            />
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th className="team-name-column">Team</th>
                        <th className="team-name-column">Owner</th>
                        <th>Projected Wins</th>
                        <th>Projected Losses</th>
                        <th>Projected Ties</th>
                        <th>Projected Points For</th>
                        <th>Playoff Odds</th>
                    </tr>
                </thead>
                <tbody>
                    {data === null || playoffTeams === null ? (
                        <LoadingRow
                            text="Calculating playoff odds..."
                            colSpan="7"
                        />
                    ) : (
                        data.map((team, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td className="team-name-column">
                                    {team.team}
                                </td>
                                <td className="team-name-column">
                                    {team.owner}
                                </td>
                                <td>{team.projected_wins.toFixed(1)}</td>
                                <td>{team.projected_losses.toFixed(1)}</td>
                                <td>{team.projected_ties.toFixed(1)}</td>
                                <td>{team.projected_points_for.toFixed(2)}</td>
                                <td>{(team.playoff_odds * 100).toFixed(1)}%</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
            <p>
                <strong>
                    Note that for this league, {playoffTeams} teams make the
                    playoffs.
                </strong>
                <br />
                <em>
                    All playoff odds are based on simulation results alone.
                    Values of 0% or 100% do not necessarily mean that a team has
                    been mathematically eliminated or clinched a playoff spot.
                </em>
            </p>
        </CopyableContainer>
    );
};

PlayoffOddsTable.propTypes = {
    data: PropTypes.arrayOf(
        PropTypes.shape({
            team: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            projected_wins: PropTypes.number.isRequired,
            projected_losses: PropTypes.number.isRequired,
            projected_ties: PropTypes.number.isRequired,
            projected_points_for: PropTypes.string.isRequired,
            playoff_odds: PropTypes.string.isRequired,
        })
    ),
    playoffTeams: PropTypes.number,
};

export default PlayoffOddsTable;
