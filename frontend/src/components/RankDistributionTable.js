import React from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import CopyableContainer from "./CopyableContainer";
import PendingDataNotice from "./PendingDataNotice";
import './styles/tableStyles.css';

const RankDistributionTable = ({
    data,
    numColumns,
    playoffTeams,
    selectedWeek,
    pendingData,
}) => {
    const ordinalSuffix = (num) => {
        const suffixes = ["th", "st", "nd", "rd"];
        const value = num % 100;
        return (
            num +
            (suffixes[(value - 20) % 10] || suffixes[value] || suffixes[0])
        );
    };

    function formatPercent(val) {
        const percentage = val * 100;
        return `${percentage.toFixed(val < 0.1 ? 1 : 0)}%`;
    }

    return (
        <CopyableContainer
            title={`Final position distribution odds (prior to Week ${selectedWeek} matchups)`}
            fileName={`rank-distribution-week-${selectedWeek}`}
        >
            <PendingDataNotice
                dataType="final position distributions"
                isPending={pendingData}
            />
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th className="team-name-column">Team</th>
                        <th className="team-name-column">Owner</th>
                        {Array.from({ length: numColumns }, (_, i) => (
                            <th key={i}>{ordinalSuffix(i + 1)} place</th>
                        ))}
                        <th>Playoff Odds</th>
                    </tr>
                </thead>
                <tbody>
                    {data === null ? (
                        <LoadingRow
                            text="Calculating rank distribution..."
                            colSpan={numColumns + 3}
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
                                {team.position_odds
                                    .slice(0, numColumns)
                                    .map((odds, i) => (
                                        <td key={i}>{formatPercent(odds)}</td>
                                    ))}
                                <td>{formatPercent(team.playoff_odds)}</td>
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
        </CopyableContainer>
    );
};

RankDistributionTable.propTypes = {
    data: PropTypes.arrayOf(
        PropTypes.shape({
            team: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            position_odds: PropTypes.arrayOf(PropTypes.string).isRequired,
            playoff_odds: PropTypes.string.isRequired,
        })
    ),
    numColumns: PropTypes.number.isRequired,
    playoffTeams: PropTypes.number.isRequired,
};

export default RankDistributionTable;
