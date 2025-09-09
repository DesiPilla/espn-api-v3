import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReturnToHomePageButton from "../components/ReturnToHomePageButton";
import ReturnToLeaguePageButton from "../components/ReturnToLeaguePageButton";
import Footer from "../components/Footer";
import styles from "../components/styles/league.css";
import SimulatePlayoffOddsButton from "../components/SimulatePlayoffOddsButton";
import SeasonTeamRecordsTable from "../components/SeasonTeamRecordsTable";
import SeasonPositionalRecordsTable from "../components/SeasonPositionalRecordsTable";
import { safeFetch } from "../utils/api";

const LeagueRecordsPage = () => {
    const { leagueYear, leagueId } = useParams();
    const [records, setRecords] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchRecords = () => {
            const endpoint = `/api/season-records/${leagueYear}/${leagueId}/`;

            safeFetch(endpoint)
                .then((data) => {
                    if (data?.redirect) {
                        console.log(`Redirecting to: ${data.redirect}`);
                        navigate(data.redirect);
                    } else {
                        setRecords(data);
                        console.log("League records fetched:", data);
                    }
                })
                .catch((err) => {
                    console.error(`ERROR: ${endpoint}`, err);
                    setFetchError(err);
                });
        };

        if (leagueYear && leagueId) {
            fetchRecords();
        }
    }, [leagueYear, leagueId]);

    return (
        <div>
            <h1>League Records</h1>
            <p>Year: {leagueYear}</p>
            <p>League ID: {leagueId}</p>

            <div className="button-container">
                <ReturnToHomePageButton />
                <ReturnToLeaguePageButton
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                />
                <SimulatePlayoffOddsButton
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                />
            </div>
            <SeasonTeamRecordsTable
                bestTeamStats={records?.best_team_stats || null}
                worstTeamStats={records?.worst_team_stats || null}
            />
            <SeasonPositionalRecordsTable
                bestPositionalStats={records?.best_position_stats || null}
                worstPositionalStats={records?.worst_position_stats || null}
            />

            <Footer />
        </div>
    );
};

export default LeagueRecordsPage;
