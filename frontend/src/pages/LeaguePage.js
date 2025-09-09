import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from "react-router-dom";
import WeekSelector from "../components/WeekSelector";
import ReturnToHomePageButton from "../components/ReturnToHomePageButton";
import BoxScoresTable from "../components/BoxScoresTable";
import WeeklyAwardsTable from "../components/WeeklyAwardsTable";
import PowerRankingsTable from "../components/PowerRankingsTable";
import LuckIndexTable from "../components/LuckIndexTable";
import StandingsTable from "../components/StandingsTable";
import NaughtyList from "../components/NaughtyList";
import Footer from "../components/Footer";
import SimulatePlayoffOddsButton from "../components/SimulatePlayoffOddsButton";
import LeagueRecordsButton from "../components/LeagueRecordsButton";
import { safeFetch } from "../utils/api";

import "../components/styles/league.css";

const LeaguePage = () => {
    const { leagueYear, leagueId } = useParams();
    const location = useLocation(); // Access the current URL
    const [leagueData, setLeagueData] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [leagueSettings, setLeagueSettings] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate(); // Add navigation hook

    if (fetchError) {
        throw fetchError;
    }

    // Preload the league data for faster loading later on
    useEffect(() => {
        safeFetch(`/api/league/${leagueYear}/${leagueId}/`)
            .then((data) => {
                if (data?.redirect) {
                    navigate(data.redirect);
                } else {
                    console.log(
                        `League ${leagueId} is active for the year ${leagueYear}`
                    );
                }
            })
            .catch((err) => {
                console.error(`ERROR: /api/league/${leagueYear}/${leagueId}/`);
                setFetchError(err);
            });
    }, []);

    // Check if the league season has begun
    useEffect(() => {
        const checkLeagueStatus = async () => {
            safeFetch(`/api/check-league-status/${leagueYear}/${leagueId}/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        console.log(
                            `League ${leagueId} is active for the year ${leagueYear}`
                        );
                    }
                })
                .catch((err) => {
                    console.error("ERROR: /api/check-league-status");
                    setFetchError(err);
                });
        };

        checkLeagueStatus();
    }, [leagueId, leagueYear, selectedWeek, navigate]);

    // Fetch the league data from the backend using the leagueId and leagueYear
    useEffect(() => {
        const fetchLeagueData = async () => {
            safeFetch(`/api/league/${leagueYear}/${leagueId}/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setLeagueData(data);
                        console.log("League data fetched:", data);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/league/${leagueYear}/${leagueId}/`,
                        err
                    );
                    setFetchError(err);
                });
        };

        fetchLeagueData();
    }, [leagueYear, leagueId, navigate]);

    // Set the default current week and selected week
    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const weekFromUrl = (() => {
            const week = queryParams.get("week");
            return week && !isNaN(parseInt(week)) ? parseInt(week) : null;
        })();

        if (weekFromUrl) {
            console.log("Setting selected week from URL:", weekFromUrl);
            setSelectedWeek(weekFromUrl);
        }

        const fetchCurrentWeek = async () => {
            safeFetch(`/api/league/${leagueYear}/${leagueId}/current-week/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setCurrentWeek(data.current_week);
                        if (!weekFromUrl) {
                            setSelectedWeek(data.current_week); // Only set selectedWeek if not already defined
                        }
                        console.log("Current week:", currentWeek);
                        console.log("Selected week:", selectedWeek);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/league/${leagueYear}/${leagueId}/current-week/`,
                        err
                    );
                    setFetchError(err);
                });
        };

        fetchCurrentWeek();

        // Ensure selectedWeek is never undefined
        if (selectedWeek === undefined) {
            console.log(
                "selectedWeek is undefined, setting it to currentWeek:",
                currentWeek
            );
            setSelectedWeek(currentWeek);
        }
    }, [location.search, leagueYear, leagueId, selectedWeek, currentWeek]);

    const handleWeekChange = (newWeek) => {
        // Ensure selectedWeek is never undefined
        const validWeek = newWeek ?? currentWeek;
        setSelectedWeek(validWeek);
        const queryParams = new URLSearchParams(location.search);
        queryParams.set("week", validWeek); // Update the URL query parameter with a valid week
        window.history.replaceState(
            null,
            "",
            `${location.pathname}?${queryParams.toString()}`
        );
    };

    // Fetch the number of playoff teams and update the simulation count if the league is complete
    useEffect(() => {
        const fetchLeagueSettings = async () => {
            safeFetch(`/api/league-settings/${leagueYear}/${leagueId}/`)
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        console.log(
                            "Is season complete?",
                            data.regular_season_complete
                        );
                        setLeagueSettings(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        `ERROR: /api/league-settings/${leagueYear}/${leagueId}/`,
                        err
                    );
                    setFetchError(err);
                });
        };

        fetchLeagueSettings();
    }, [leagueYear, leagueId]);

    if (!leagueData || currentWeek === null) {
        return <div>Loading...</div>;
    }

    console.log("Selected week:", selectedWeek);
    console.log("Current week:", currentWeek);

    return (
        <div>
            <div className="league-content">
                <h1>{leagueData.league_name}</h1>
                <p>Year: {leagueData.league_year}</p>
                <p>League ID: {leagueData.league_id}</p>

                <WeekSelector
                    currentWeek={currentWeek} // Always use currentWeek for WeekSelector
                    minWeek={1}
                    maxWeek={currentWeek}
                    onWeekChange={handleWeekChange}
                />

                {/* Add a container for horizontal alignment */}
                <div className="button-container">
                    <ReturnToHomePageButton />
                    <SimulatePlayoffOddsButton
                        leagueYear={leagueYear}
                        leagueId={leagueId}
                        n_simulations={
                            leagueSettings?.regular_season_complete ? 50 : 100
                        }
                    />
                    <LeagueRecordsButton
                        leagueYear={leagueYear}
                        leagueId={leagueId}
                    />
                </div>

                <BoxScoresTable
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />

                <WeeklyAwardsTable
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />

                <PowerRankingsTable
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />

                <LuckIndexTable
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />

                <NaughtyList
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />

                <StandingsTable
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                    week={selectedWeek}
                />
            </div>
            <Footer />
        </div>
    );
};

export default LeaguePage;

