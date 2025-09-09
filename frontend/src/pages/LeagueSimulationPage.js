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
    const [leagueSettings, setLeagueSettings] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    const queryParams = new URLSearchParams(location.search);
    const [nSimulations, setNSimulations] = useState(
        queryParams.get("n_simulations") || null
    );

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
        const checkLeagueStatus = () => {
            safeFetch(`/api/check-league-status/${leagueYear}/${leagueId}/`)
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
            safeFetch(`/api/league-settings/${leagueYear}/${leagueId}/`)
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
        const weekFromUrl = queryParams.get("week");

        console.log("weekFromUrl:", weekFromUrl); // Debugging step

        const validWeekFromUrl =
            weekFromUrl && !isNaN(parseInt(weekFromUrl, 10))
                ? parseInt(weekFromUrl, 10)
                : null;

        if (validWeekFromUrl !== null) {
            console.log("Setting selected week from URL:", validWeekFromUrl);
            setSelectedWeek(validWeekFromUrl);
        }

        const fetchCurrentWeek = () => {
            console.log("Fetching current week...");
            safeFetch(`/api/league/${leagueYear}/${leagueId}/current-week/`)
                .then((data) => {
                    if (data?.redirect) {
                        console.log(`Redirecting to: ${data.redirect}`);
                        navigate(data.redirect);
                        return; // Stop further processing if redirect
                    }

                    console.log("Fetched current week:", data.current_week); // Debugging step

                    const validCurrentWeek = !isNaN(data.current_week)
                        ? data.current_week
                        : null;
                    const validMaxWeek = !isNaN(
                        leagueSettings?.n_regular_season_weeks
                    )
                        ? leagueSettings.n_regular_season_weeks
                        : validCurrentWeek;

                    const adjustedWeek =
                        validCurrentWeek !== null
                            ? Math.min(validMaxWeek, validCurrentWeek)
                            : null;

                    setCurrentWeek(adjustedWeek);

                    if (
                        validWeekFromUrl === null &&
                        validCurrentWeek !== null
                    ) {
                        setSelectedWeek(adjustedWeek); // Only set selectedWeek if not defined by URL
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/league/%s/%s/current-week/",
                        leagueYear,
                        leagueId,
                        err
                    );
                    setFetchError(err);
                });
        };

        if (leagueYear && leagueId) {
            fetchCurrentWeek();
        }

        // Ensure selectedWeek is never undefined
        if (selectedWeek === undefined) {
            console.log(
                "selectedWeek is undefined, setting it to currentWeek:",
                currentWeek
            );
            setSelectedWeek(currentWeek);
        }
    }, [location.search, leagueYear, leagueId, selectedWeek, currentWeek]);

    // Redirect to "uh-oh-too-early" page if selectedWeek or currentWeek is less than 4
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
            if (selectedWeek < 4 || currentWeek < 4) {
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

        safeFetch(endpoint)
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

    console.log("Selected week:", selectedWeek);
    console.log("Current week:", currentWeek);
    console.log("Number of simulations:", nSimulations);

    return (
        <div>
            <h1>League Simulation Results</h1>
            <p>Year: {leagueYear}</p>
            <p>League ID: {leagueId}</p>

            <WeekSelector
                currentWeek={currentWeek ?? 18}
                onWeekChange={handleWeekChange}
                minWeek={4}
                maxWeek={Math.min(
                    leagueSettings?.n_regular_season_weeks,
                    currentWeek
                )}
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
