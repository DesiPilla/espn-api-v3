import React from 'react';
import PropTypes from 'prop-types';
import LoadingRow from "./LoadingRow";
import CopyableContainer from "./CopyableContainer";
import PendingDataNotice from "./PendingDataNotice";
import "./styles/tableStyles.css";

const SeasonPositionalRecordsTable = ({
    bestPositionalStats,
    worstPositionalStats,
}) => {
    const isPending = !bestPositionalStats || !worstPositionalStats;

    return (
        <CopyableContainer
            title="Season Positional Records"
            fileName="season-positional-records"
        >
            <PendingDataNotice
                dataType="positional records"
                isPending={isPending}
            />
            <table className="table-with-bottom-caption">
                <thead>
                    <tr>
                        <th>Award</th>
                        <th>Winner</th>
                        <th>Record</th>
                    </tr>
                </thead>
                <tbody>
                    {!bestPositionalStats || !worstPositionalStats ? (
                        <LoadingRow
                            text="Loading positional records..."
                            colSpan="3"
                        />
                    ) : (
                        <>
                            {bestPositionalStats.map((stat, index) => (
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
                            {worstPositionalStats.map((stat, index) => (
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

SeasonPositionalRecordsTable.propTypes = {
    bestPositionalStats: PropTypes.arrayOf(
        PropTypes.shape({
            label: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            value: PropTypes.string.isRequired,
        })
    ),
    worstPositionalStats: PropTypes.arrayOf(
        PropTypes.shape({
            label: PropTypes.string.isRequired,
            owner: PropTypes.string.isRequired,
            value: PropTypes.string.isRequired,
        })
    ),
};

export default SeasonPositionalRecordsTable;
