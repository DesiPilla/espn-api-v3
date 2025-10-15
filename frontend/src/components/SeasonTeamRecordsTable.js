import React from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import CopyableContainer from "./CopyableContainer";
import PendingDataNotice from "./PendingDataNotice";
import "./styles/tableStyles.css";

const SeasonTeamRecordsTable = ({ bestTeamStats, worstTeamStats }) => {
    const isPending = !bestTeamStats || !worstTeamStats;

    return (
        <CopyableContainer
            title="Season Team Records"
            fileName="season-team-records"
        >
            <PendingDataNotice dataType="team records" isPending={isPending} />
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th>Award</th>
                        <th>Winner</th>
                        <th>Record</th>
                    </tr>
                </thead>
                <tbody>
                    {!bestTeamStats || !worstTeamStats ? (
                        <LoadingRow
                            text="Loading team records..."
                            colSpan="3"
                        />
                    ) : (
                        <>
                            {bestTeamStats.map((stat, index) => (
                                <tr
                                    key={`best-${index}`}
                                    className={
                                        index % 2 === 0 ? "even-row" : "odd-row"
                                    }
                                >
                                    <td>{stat.label}</td>
                                    <td>{stat.owner}</td>
                                    <td>{stat.value}</td>
                                </tr>
                            ))}
                            {worstTeamStats.map((stat, index) => (
                                <tr
                                    key={`worst-${index}`}
                                    className={`${
                                        index === 0 ? "thick-border-top" : ""
                                    } ${
                                        index % 2 === 0 ? "even-row" : "odd-row"
                                    }`}
                                >
                                    <td>{stat.label}</td>
                                    <td>{stat.owner}</td>
                                    <td>{stat.value}</td>
                                </tr>
                            ))}
                        </>
                    )}
                </tbody>
            </table>
        </CopyableContainer>
    );
};

SeasonTeamRecordsTable.propTypes = {
    bestTeamStats: PropTypes.arrayOf(
        PropTypes.shape({
            label: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            value: PropTypes.string.isRequired,
        })
    ),
    worstTeamStats: PropTypes.arrayOf(
        PropTypes.shape({
            label: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            value: PropTypes.string.isRequired,
        })
    ),
};

export default SeasonTeamRecordsTable;
