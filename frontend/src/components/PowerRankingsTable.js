import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import "./styles/tableStyles.css";

const PowerRankingsTable = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
}) => {
    const [powerRankings, setPowerRankings] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false); // Internal loading state
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchPowerRankings = () => {
            setLoading(true); // Set internal loading to true
            safeFetch(
                `/api/power-rankings/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setPowerRankings(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/power-rankings/%s/%s/%s/",
                        leagueYear,
                        leagueId,
                        week,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false); // Set internal loading to false
                });
        };

        if (leagueYear && leagueId && week) {
            fetchPowerRankings();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <div className="wrapper-wide">
            <h2 className="text-xl font-semibold mb-4">
                Power Rankings - Week {week}
            </h2>
            <p>
                <em>
                    Note that scores have not yet been finalized for this week
                    and the Power Rankings are likely to change.
                    <br />
                    Please check back on Tuesday morning for the final results.
                </em>
            </p>
            <table className="table">
                <thead>
                    <tr>
                        <th>Team Name</th>
                        <th>Owner</th>
                        <th>Power Rank</th>
                    </tr>
                </thead>
                <tbody>
                    {globalLoading || loading ? ( // Show spinner if global or internal loading is true
                        <LoadingRow
                            text="Loading Power Rankings..."
                            colSpan="3"
                        />
                    ) : powerRankings.length === 0 ? (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>
                                No power rankings available.
                            </td>
                        </tr>
                    ) : (
                        powerRankings.map((team, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{team.team}</td>
                                <td>{team.owner}</td>
                                <td>
                                    {typeof team.value === "number"
                                        ? team.value.toFixed(2)
                                        : team.value}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default PowerRankingsTable;
