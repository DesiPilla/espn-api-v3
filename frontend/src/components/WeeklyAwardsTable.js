import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import CopyableContainer from "./CopyableContainer";
import PendingDataNotice from "./PendingDataNotice";
import "./styles/tableStyles.css";

const WeeklyAwardsTable = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
    nCompletedWeeks,
}) => {
    const [weeklyAwards, setWeeklyAwards] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false); // Internal loading state
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchWeeklyAwards = async () => {
            setLoading(true); // Set internal loading to true
            safeFetch(
                `/api/weekly-awards/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setWeeklyAwards(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/weekly-awards/${leagueYear}/${leagueId}/${week}/`,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false); // Set internal loading to false
                });
        };

        if (leagueYear && leagueId && week) {
            fetchWeeklyAwards();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <CopyableContainer
            title={`Weekly Awards - Week ${week}`}
            fileName={`weekly-awards-week-${week}`}
        >
            <PendingDataNotice
                dataType="award winners"
                isPending={week > nCompletedWeeks}
            />
            <table className="table">
                <thead>
                    <tr>
                        <th>Award</th>
                        <th>Winner</th>
                        <th>Award</th>
                        <th>Loser</th>
                    </tr>
                </thead>
                <tbody>
                    {globalLoading || loading ? ( // Show spinner if global or internal loading is true
                        <LoadingRow
                            text="Loading Weekly Awards..."
                            colSpan="4"
                        />
                    ) : !weeklyAwards ||
                      weeklyAwards.bestAwards.length === 0 ? (
                        <tr>
                            <td colSpan="4" style={{ textAlign: "center" }}>
                                No weekly awards available.
                            </td>
                        </tr>
                    ) : (
                        weeklyAwards.bestAwards.map((bestAward, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{bestAward[0]}</td>
                                <td>{bestAward[1]}</td>
                                <td>{weeklyAwards.worstAwards[index][0]}</td>
                                <td>{weeklyAwards.worstAwards[index][1]}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </CopyableContainer>
    );
};

export default WeeklyAwardsTable;
