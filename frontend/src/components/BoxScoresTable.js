import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import "./styles/tableStyles.css";

const BoxScoresTable = ({ leagueYear, leagueId, week }) => {
    const [boxScores, setBoxScores] = useState([]);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchBoxScores = async () => {
            safeFetch(`/api/box-scores/${leagueYear}/${leagueId}/${week}/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setBoxScores(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/box-scores/${leagueYear}/${leagueId}/${week}/`,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false);
                });
        };

        if (leagueYear && leagueId && week) {
            fetchBoxScores();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <div className="wrapper-wide">
            <h2 className="text-xl font-semibold mb-4">
                Box Scores - Week {week}
            </h2>
            <table className="table">
                <thead>
                    <tr>
                        <th>Home Team</th>
                        <th>Score</th>
                        <th>Away Team</th>
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <LoadingRow text="Loading Box Scores..." colSpan="3" />
                    ) : boxScores.length === 0 ? (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>
                                No box scores available.
                            </td>
                        </tr>
                    ) : (
                        boxScores.map((game, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{game.home_team}</td>
                                <td>
                                    {game.home_score} - {game.away_score}
                                </td>
                                <td>{game.away_team}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default BoxScoresTable;
