import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import ReturnToLeaguePageButton from '../components/ReturnToLeaguePageButton';
import Footer from '../components/Footer';
import styles from '../components/styles/league.css';
import SimulatePlayoffOddsButton from '../components/SimulatePlayoffOddsButton';
import SeasonTeamRecordsTable from '../components/SeasonTeamRecordsTable';
import SeasonPositionalRecordsTable from '../components/SeasonPositionalRecordsTable';

const LeagueRecordsPage = () => {
    const { leagueYear, leagueId } = useParams();
    const [records, setRecords] = useState(null);

    useEffect(() => {
        const fetchRecords = async () => {
            try {
                const response = await fetch(`/api/season-records/${leagueYear}/${leagueId}/`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch league records (status ${response.status})`);
                }
                const data = await response.json();
                setRecords(data);
                console.log("League records fetched:", data);
            } catch (error) {
                console.error("Error fetching league records:", error);
            }
        };

        fetchRecords();
    }, [leagueYear, leagueId]);

    return (
        <div>
            <h1>League Records</h1>
            <p>Year: {leagueYear}</p>
            <p>League ID: {leagueId}</p>

            <div className="button-container">
                <ReturnToHomePageButton />
                <ReturnToLeaguePageButton leagueYear={leagueYear} leagueId={leagueId} />
                <SimulatePlayoffOddsButton leagueYear={leagueYear} leagueId={leagueId} />
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
