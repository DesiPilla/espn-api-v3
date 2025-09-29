import React from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import './styles/tableStyles.css';

const SeedingOutcomesTable = ({ data, playoffTeams, pendingData }) => {
    function formatPercent(val) {
        const percentage = val * 100;
        return `${percentage.toFixed(val < 0.1 ? 1 : 0)}%`;
    }

    return (
        <div className="wrapper-wide">
            <h2>Seeding Outcomes</h2>
            {pendingData && ( // Only display note if week > nCompletedWeeks
                <p>
                    <em>
                        Note that scores have not yet been finalized for this
                        week and the seeding outcomes are likely to change.
                        <br />
                        Please check back on Tuesday morning for the final
                        results.
                    </em>
                </p>
            )}
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th className="team-name-column">Team</th>
                        <th className="team-name-column">Owner</th>
                        <th>First in League</th>
                        <th>First in Division</th>
                        <th>Make Playoffs</th>
                        <th>Last in Division</th>
                        <th>Last in League</th>
                    </tr>
                </thead>
                <tbody>
                    {data === null ? (
                        <LoadingRow
                            text="Calculating seeding outcomes..."
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
                                <td>{formatPercent(team.first_in_league)}</td>
                                <td>{formatPercent(team.first_in_division)}</td>
                                <td>{formatPercent(team.make_playoffs)}</td>
                                <td>{formatPercent(team.last_in_division)}</td>
                                <td>{formatPercent(team.last_in_league)}</td>
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
                    All percentages are based on simulation results alone.
                    Values of 0% or 100% do not necessarily mean that a team has
                    been mathematically eliminated or clinched a playoff spot.
                </em>
            </p>
        </div>
    );
};

SeedingOutcomesTable.propTypes = {
    data: PropTypes.arrayOf(
        PropTypes.shape({
            team: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            first_in_league: PropTypes.string.isRequired,
            first_in_division: PropTypes.string.isRequired,
            make_playoffs: PropTypes.string.isRequired,
            last_in_division: PropTypes.string.isRequired,
            last_in_league: PropTypes.string.isRequired,
        })
    ),
    playoffTeams: PropTypes.number.isRequired, // Add playoffTeams as a required prop
};

export default SeedingOutcomesTable;
