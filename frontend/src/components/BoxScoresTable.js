import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import CopyableContainer from "./CopyableContainer";
import "./styles/tableStyles.css";

const BoxScoresTable = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
}) => {
    const [boxScores, setBoxScores] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    if (fetchError) throw fetchError;

    useEffect(() => {
        const fetchBoxScores = async () => {
            setLoading(true);
            safeFetch(
                `/api/box-scores/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setBoxScores(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/box-scores/%s/%s/%s/",
                        leagueYear,
                        leagueId,
                        week,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => setLoading(false));
        };

        if (leagueYear && leagueId && week) {
            fetchBoxScores();
        }
    }, [leagueYear, leagueId, week]);

    // Box scores fetching logic is kept, removed the copy-to-image logic which is now in CopyableContainer

    return (
        <CopyableContainer
            title={`Box Scores - Week ${week}`}
            fileName={`boxscores-week-${week}`}
        >
            <table className="table">
                <thead>
                    <tr>
                        <th>Home Team</th>
                        <th>Score</th>
                        <th>Away Team</th>
                    </tr>
                </thead>
                <tbody>
                    {globalLoading || loading ? (
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
        </CopyableContainer>
    );
};

export default BoxScoresTable;
