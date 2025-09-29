import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import WeekSelector from "../components/WeekSelector";
import ReturnToHomePageButton from "../components/ReturnToHomePageButton";
import Footer from "../components/Footer";
import SimulationSelector from "../components/SimulationSelector";
import PlayoffOddsTable from "../components/PlayoffOddsTable";
import RankDistributionTable from "../components/RankDistributionTable";
import SeedingOutcomesTable from "../components/SeedingOutcomesTable";
import RemainingStrengthOfScheduleTable from "../components/RemainingStrengthOfScheduleTable";
import ReturnToLeaguePageButton from "../components/ReturnToLeaguePageButton";
import LeagueRecordsButton from "../components/LeagueRecordsButton";
import { safeFetch } from "../utils/api";
import "../components/styles/league.css";

const LeagueSimulationPage = () => {
    const { leagueYear, leagueId } = useParams();
    const location = useLocation();
    const [simulationData, setSimulationData] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [nCompletedWeeks, setNCompletedWeeks] = useState(null);
    const [leagueSettings, setLeagueSettings] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false); // Add loading state
    const navigate = useNavigate();

    const MIN_WEEK_TO_SIMULATE = 4; // Minimum week required to run simulations

    if (fetchError) {
        throw fetchError;
    }

    const queryParams = new URLSearchParams(location.search);
    const [nSimulations, setNSimulations] = useState(
        queryParams.get("n_simulations") || null
    );

    // Preload the league data for faster loading later on
    useEffect(() => {
        safeFetch(`/api/league/${leagueYear}/${leagueId}/`, {}, false, 2)
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
        const checkLeagueStatus = () => {
            safeFetch(
                `/api/check-league-status/${leagueYear}/${leagueId}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        console.log(`Redirecting to: ${data.redirect}`);
                        navigate(data.redirect);
                    } else {
                        console.log("League status data:", data);
                        // Optionally set state here if you need any data from the response
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/check-league-status/%s/%s/",
                        leagueYear,
                        leagueId,
                        err
                    );
                    setFetchError(err);
                });
        };

        if (leagueYear && leagueId) {
            checkLeagueStatus();
        }
    }, [leagueYear, leagueId, navigate]);

    // Fetch the number of playoff teams
    useEffect(() => {
        const fetchLeagueSettings = () => {
            safeFetch(
                `/api/league-settings/${leagueYear}/${leagueId}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        console.log(`Redirecting to: ${data.redirect}`);
                        navigate(data.redirect);
                    } else {
                        console.log(
                            "Number of playoff teams fetched:",
                            data.playoff_teams
                        );
                        setLeagueSettings(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/league-settings/%s/%s/",
                        leagueYear,
                        leagueId,
                        err
                    );
                    setFetchError(err);
                });
        };

        if (leagueYear && leagueId) {
            fetchLeagueSettings();
        }
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
            safeFetch(
                `/api/league/${leagueYear}/${leagueId}/current-week/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setCurrentWeek(data.current_week);
                        setNCompletedWeeks(data.n_completed_weeks);
                        if (!weekFromUrl) {
                            setSelectedWeek(data.current_week - 1); // Only set selectedWeek if not already defined
                        }
                        console.log("Current week:", currentWeek);
                        console.log("Selected week:", selectedWeek);
                        console.log(
                            "Number of completed weeks:",
                            data.n_completed_weeks
                        );
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/league/%s/%s/current-week/", leagueYear, leagueId, err
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
            setSelectedWeek(currentWeek - 1);
        }
    }, [location.search, leagueYear, leagueId, selectedWeek, currentWeek]);

    // Redirect to "uh-oh-too-early" page if selectedWeek or currentWeek is less than MIN_WEEK_TO_SIMULATE
    useEffect(() => {
        console.log("selectedWeek:", selectedWeek, "currentWeek:", currentWeek);

        // Ensure selectedWeek is defined
        if (selectedWeek === undefined) {
            console.log(
                "selectedWeek is undefined, setting it to currentWeek:",
                currentWeek
            );
            setSelectedWeek(currentWeek);
        }

        // Perform redirect if both weeks are valid
        if (selectedWeek !== null && currentWeek !== null) {
            if (
                selectedWeek < MIN_WEEK_TO_SIMULATE ||
                currentWeek < MIN_WEEK_TO_SIMULATE
            ) {
                const redirectUrl = `/fantasy_stats/uh-oh-too-early/league-homepage/${leagueYear}/${leagueId}`;
                console.log(`Redirecting to: ${redirectUrl}`);
                navigate(redirectUrl);
            } else {
                console.log("No redirect needed, weeks are valid");
            }
        }
    }, [selectedWeek, currentWeek, leagueYear, leagueId, navigate]);

    // Fetch simulation data
    const fetchSimulationData = (week, simulations) => {
        const queryParams = new URLSearchParams();
        if (simulations !== null) {
            queryParams.set("n_simulations", simulations);
        }
        if (week !== null) {
            queryParams.set("week", week);
        }

        const endpoint = `/api/simulate-playoff-odds/${leagueYear}/${leagueId}/?${queryParams.toString()}`;

        safeFetch(endpoint, {}, false, 2)
            .then((data) => {
                if (data?.redirect) {
                    console.log(`Redirecting to: ${data.redirect}`);
                    navigate(data.redirect);
                } else {
                    setSimulationData(data);
                    console.log("Simulation data fetched:", data);
                }
            })
            .catch((err) => {
                console.error("ERROR: %s", endpoint, err);

                setFetchError(err);
            });
    };

    // Fetch simulation data on initial load and when dependencies change
    useEffect(() => {
        if (selectedWeek !== null) {
            fetchSimulationData(selectedWeek, nSimulations);
        }
    }, [selectedWeek, nSimulations, leagueYear, leagueId, navigate]);

    const handleWeekChange = (newWeek) => {
        console.log("handleWeekChange called with newWeek:", newWeek); // Debugging step
        // Ensure selectedWeek is never undefined
        const validWeek = newWeek && !isNaN(newWeek) ? newWeek : currentWeek;
        console.log("Valid week determined in handleWeekChange:", validWeek); // Debugging step

        if (validWeek !== undefined && !isNaN(validWeek)) {
            setSelectedWeek(validWeek);
            setSimulationData(null); // Reset simulationData to show the spinner
            const queryParams = new URLSearchParams(location.search);
            queryParams.set("week", validWeek); // Update the URL query parameter with a valid week
            window.history.replaceState(
                null,
                "",
                `${location.pathname}?${queryParams.toString()}`
            );
        }
    };

    const handleSimulationsChange = (newSimulations) => {
        setNSimulations(newSimulations);
        setSimulationData(null); // Reset simulationData to show the spinner
        const queryParams = new URLSearchParams(location.search);
        queryParams.set("n_simulations", newSimulations);
        window.history.replaceState(
            null,
            "",
            `${location.pathname}?${queryParams.toString()}`
        );
    };

    useEffect(() => {
        if (selectedWeek !== null) {
            // Simulate data fetching for the new week
            setLoading(true);
            const fetchData = async () => {
                try {
                    // Simulate a delay for fetching data
                    await new Promise((resolve) => setTimeout(resolve, 1000));
                } finally {
                    setLoading(false); // Set loading to false after data is fetched
                }
            };
            fetchData();
        }
    }, [selectedWeek]);

    console.log("Selected week:", selectedWeek);
    console.log("Current week:", currentWeek);
    console.log("Number of simulations:", nSimulations);

    if (!leagueSettings || currentWeek === null) {
        return (
            <div className="loading-container">
                <div className="loading-spinner"></div>
                <span className="loading-text">Loading league data...</span>
            </div>
        );
    }

    return (
        <div>
            <h1>League Simulation Results</h1>
            <p>Year: {leagueYear}</p>
            <p>League ID: {leagueId}</p>

            <WeekSelector
                currentWeek={currentWeek}
                selectedWeek={selectedWeek}
                minWeek={MIN_WEEK_TO_SIMULATE}
                maxWeek={Math.min(
                    leagueSettings?.n_regular_season_weeks,
                    currentWeek
                )}
                onWeekChange={handleWeekChange}
                disable={leagueSettings?.regular_season_complete}
            />

            <div className="button-container">
                <ReturnToHomePageButton />
                <ReturnToLeaguePageButton
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                />
                <LeagueRecordsButton
                    leagueYear={leagueYear}
                    leagueId={leagueId}
                />
            </div>

            <SimulationSelector
                nSimulations={nSimulations}
                setNSimulations={handleSimulationsChange}
            />

            <PlayoffOddsTable
                data={simulationData?.playoff_odds || null}
                playoffTeams={leagueSettings?.n_playoff_spots}
                selectedWeek={selectedWeek}
                pendingData={selectedWeek >= nCompletedWeeks}
            />

            <RankDistributionTable
                data={simulationData?.rank_distribution || null}
                numColumns={leagueSettings?.n_teams}
                playoffTeams={leagueSettings?.n_playoff_spots}
                pendingData={selectedWeek >= nCompletedWeeks}
            />

            <SeedingOutcomesTable
                data={simulationData?.seeding_outcomes || null}
                playoffTeams={leagueSettings?.n_playoff_spots}
                pendingData={selectedWeek >= nCompletedWeeks}
            />

            <RemainingStrengthOfScheduleTable
                leagueYear={leagueYear}
                leagueId={leagueId}
                week={selectedWeek}
                nCompletedWeeks={nCompletedWeeks}
            />

            <Footer />
        </div>
    );
};

export default LeagueSimulationPage;
