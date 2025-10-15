import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import CopyableContainer from "./CopyableContainer";
import "./styles/tableStyles.css";

const StandingsTable = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
}) => {
    const [standings, setStandings] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false); // Internal loading state
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchStandings = () => {
            setLoading(true); // Set internal loading to true
            safeFetch(
                `/api/standings/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setStandings(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/standings/${leagueYear}/${leagueId}/${week}/`,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false); // Set internal loading to false
                });
        };

        if (leagueYear && leagueId && week) {
            fetchStandings();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <CopyableContainer
            title={`Standings through Week ${week}`}
            fileName={`standings-week-${week}`}
        >
            <table className="table">
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Wins</th>
                        <th>Losses</th>
                        <th>Ties</th>
                        <th>Points For</th>
                        <th>Owner</th>
                    </tr>
                </thead>
                <tbody>
                    {globalLoading || loading ? ( // Show spinner if global or internal loading is true
                        <LoadingRow text="Loading Standings..." colSpan="6" />
                    ) : standings.length === 0 ? (
                        <tr>
                            <td colSpan="6" style={{ textAlign: "center" }}>
                                No standings available.
                            </td>
                        </tr>
                    ) : (
                        standings.map((team, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{team.team}</td>
                                <td>{team.wins}</td>
                                <td>{team.losses}</td>
                                <td>{team.ties}</td>
                                <td>{team.pointsFor}</td>
                                <td>{team.owner}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </CopyableContainer>
    );
};

export default StandingsTable;
