import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import "./styles/tableStyles.css";

const LuckIndexTable = ({ leagueYear, leagueId, week }) => {
    const [luckIndex, setLuckIndex] = useState([]);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchLuckIndex = () => {
            safeFetch(`/api/luck-index/${leagueYear}/${leagueId}/${week}/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setLuckIndex(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/luck-index/%s/%s/%s/",
                        leagueYear,
                        leagueId,
                        week,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false);
                });
        };

        if (leagueYear && leagueId && week) {
            fetchLuckIndex();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <div className="wrapper-wide">
            <h2 className="text-xl font-semibold mb-4">
                Luck Index - Week {week}
            </h2>
            <p>
                <em>
                    Note that scores have not yet been finalized for this week
                    and the Luck Index is likely to change.
                    <br />
                    Please check back on Tuesday morning for the final results.
                </em>
            </p>
            <table className="table">
                <thead>
                    <tr>
                        <th>Team Name</th>
                        <th>Luck Index</th>
                        <th>Owner</th>
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <LoadingRow
                            text="Calculating Luck Index..."
                            colSpan="3"
                        />
                    ) : luckIndex.length === 0 ? (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>
                                No luck index data available.
                            </td>
                        </tr>
                    ) : (
                        luckIndex.map((team, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{team.team}</td>
                                <td>{team.text}</td>
                                <td>{team.owner}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default LuckIndexTable;
