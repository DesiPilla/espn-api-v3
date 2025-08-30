import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import WeekSelector from '../components/WeekSelector';
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import Footer from '../components/Footer';
import SimulationSelector from '../components/SimulationSelector';
import PlayoffOddsTable from '../components/PlayoffOddsTable';
import RankDistributionTable from '../components/RankDistributionTable';
import SeedingOutcomesTable from '../components/SeedingOutcomesTable';
import RemainingStrengthOfScheduleTable from '../components/RemainingStrengthOfScheduleTable';
import '../components/styles/league.css';
import ReturnToLeaguePageButton from '../components/ReturnToLeaguePageButton'; // Import the new component
import LeagueRecordsButton from '../components/LeagueRecordsButton';

const LeagueSimulationPage = () => {
    const { leagueYear, leagueId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const [simulationData, setSimulationData] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [leagueSettings, setLeagueSettings] = useState(null);

    const queryParams = new URLSearchParams(location.search);
    const [nSimulations, setNSimulations] = useState(queryParams.get('n_simulations') || null);

    // Preload the league data for faster loading later on
    useEffect(() => {
        fetch(`/api/league/${leagueYear}/${leagueId}/`);
    }, [leagueYear, leagueId]);

    // Check if the league season has begun
    useEffect(() => {
        const checkLeagueStatus = async () => {
            try {
                const response = await fetch(`/api/check-league-status/${leagueYear}/${leagueId}`);
                const data = await response.json();
                if (response.status === 400 && data.status === "too_soon") {
                    navigate(`/fantasy_stats/uh-oh-too-early/league-homepage/${leagueYear}/${leagueId}`);
                }
            } catch (error) {
                console.error("Error checking league status:", error);
            }
        };

        checkLeagueStatus();
    }, [leagueYear, leagueId, navigate]);

    // Set the default current week and selected week
    useEffect(() => {
        const weekFromUrl = queryParams.get('week');
        const fetchCurrentWeek = async () => {
            try {
                console.log("Fetching current week...");
                const result = await fetch(`/api/league/${leagueYear}/${leagueId}/current-week/`);
                if (!result.ok) {
                    throw new Error(`Failed to fetch current week (status ${result.status})`);
                }
                const data = await result.json();
                setCurrentWeek(data.current_week);
                if (weekFromUrl) {
                    console.log("Setting selected week from URL:", weekFromUrl);
                    setSelectedWeek(parseInt(weekFromUrl, null));
                } else {
                    setSelectedWeek(data.current_week);
                }
                console.log("Current week set to:", data.current_week);
            } catch (error) {
                console.error("Error fetching current week:", error);
            }
        };

        fetchCurrentWeek();
    }, [leagueYear, leagueId, queryParams]);

    // Redirect to "uh-oh-too-early" page if selectedWeek or currentWeek is less than 4
    useEffect(() => {
        if (selectedWeek !== null && currentWeek !== null) {
            if (selectedWeek < 4 || currentWeek < 4) {
                navigate(`/fantasy_stats/uh-oh-too-early/league-homepage/${leagueYear}/${leagueId}`);
            }
        }
    }, [selectedWeek, currentWeek, leagueYear, leagueId, navigate]);

    // Fetch the number of playoff teams
    useEffect(() => {
        const fetchLeagueSettings = async () => {
            try {
                const response = await fetch(`/api/league-settings/${leagueYear}/${leagueId}/`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch league settings (status ${response.status})`);
                }
                const data = await response.json();
                console.log("Number of playoff teams fetched:", data.playoff_teams);
                setLeagueSettings(data);
            } catch (error) {
                console.error("Error fetching playoff teams:", error);
            }
        };

        fetchLeagueSettings();
    }, [leagueYear, leagueId]);

    // Fetch simulation data
    const fetchSimulationData = async (week, simulations) => {
        const queryParams = new URLSearchParams();
        if (simulations !== null) {
            queryParams.set("n_simulations", simulations);
        }
        if (week !== null) {
            queryParams.set("week", week);
        }

        try {
            const response = await fetch(
                `/api/simulate-playoff-odds/${leagueYear}/${leagueId}/?${queryParams.toString()}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 400 && errorData.status === "too_soon") {
                    navigate(`/fantasy_stats/uh-oh-too-early/playoff-simulations/${leagueYear}/${leagueId}`);
                }
                console.error("Backend error:", errorData);
                throw new Error(`Failed to fetch simulation data (status ${response.status})`);
            }

            const data = await response.json();
            setSimulationData(data);
            console.log("Simulation data fetched:", data);
        } catch (error) {
            console.error("Error fetching simulation data:", error);
        }
    };

    // Fetch simulation data on initial load and when dependencies change
    useEffect(() => {
        if (selectedWeek !== null) {
            fetchSimulationData(selectedWeek, nSimulations);
        }
    }, [selectedWeek, nSimulations, leagueYear, leagueId, navigate]);

    const handleWeekChange = (newWeek) => {
        setSelectedWeek(newWeek);
        setSimulationData(null); // Reset simulationData to show the spinner
        const queryParams = new URLSearchParams(location.search);
        queryParams.set('week', newWeek);
        window.history.replaceState(null, '', `${location.pathname}?${queryParams.toString()}`);
    };

    const handleSimulationsChange = (newSimulations) => {
        setNSimulations(newSimulations);
        setSimulationData(null); // Reset simulationData to show the spinner
        const queryParams = new URLSearchParams(location.search);
        queryParams.set('n_simulations', newSimulations);
        window.history.replaceState(null, '', `${location.pathname}?${queryParams.toString()}`);
    };

    console.log("Selected week:", selectedWeek);
    console.log("Current week:", currentWeek);
    console.log("Number of simulations:", nSimulations);

    return (
        <div>
            <h1>League Simulation Results</h1>
            <p>Year: {leagueYear}</p>
            <p>League ID: {leagueId}</p>

            <WeekSelector
                currentWeek={currentWeek?? 18}
                onWeekChange={handleWeekChange}
                minWeek={4}
                maxWeek={leagueSettings?.n_regular_season_weeks}
                disable={leagueSettings?.season_complete}
            />

            <div className="button-container">
                <ReturnToHomePageButton />
                <ReturnToLeaguePageButton leagueYear={leagueYear} leagueId={leagueId} />
                <LeagueRecordsButton leagueYear={leagueYear} leagueId={leagueId} />
            </div>

            <SimulationSelector 
                nSimulations={nSimulations} 
                setNSimulations={handleSimulationsChange} 
            />

            <PlayoffOddsTable 
                data={simulationData?.playoff_odds || null} 
                playoffTeams={leagueSettings?.n_playoff_spots}
                selectedWeek={selectedWeek}
            />

            <RankDistributionTable
                data={simulationData?.rank_distribution || null}
                numColumns={leagueSettings?.n_teams}
                playoffTeams={leagueSettings?.n_playoff_spots}
            />

            <SeedingOutcomesTable 
                data={simulationData?.seeding_outcomes || null}
                playoffTeams={leagueSettings?.n_playoff_spots}
            />

            <RemainingStrengthOfScheduleTable
                leagueYear={leagueYear}
                leagueId={leagueId}
                week={selectedWeek}
            />

            <Footer />
        </div>
    );
};

export default LeagueSimulationPage;
