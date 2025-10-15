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
import "./LeagueRecordsPage.css";

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

            safeFetch(endpoint, {}, false, 2)
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
                    console.error("ERROR: %s", endpoint, err);
                    setFetchError(err);
                });
        };

        if (leagueYear && leagueId) {
            fetchRecords();
        }
    }, [leagueYear, leagueId]);

    return (
        <div className="league-records-page">
            <h1>League Records</h1>
            <div className="league-info">
                <p>Year: {leagueYear}</p>
                <p>League ID: {leagueId}</p>
            </div>

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

            <div className="records-tables-container">
                <SeasonTeamRecordsTable
                    bestTeamStats={records?.best_team_stats || null}
                    worstTeamStats={records?.worst_team_stats || null}
                />

                <div className="table-spacer"></div>

                <SeasonPositionalRecordsTable
                    bestPositionalStats={records?.best_position_stats || null}
                    worstPositionalStats={records?.worst_position_stats || null}
                />
            </div>

            <Footer />
        </div>
    );
};

export default LeagueRecordsPage;
