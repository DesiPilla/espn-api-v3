import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import "./App.css";
import AwardsPage from "./components/AwardsReact";
import HomePage from "./components/HomePage";
import LeaguePage from "./pages/LeaguePage";
import LeagueSimulationPage from "./pages/LeagueSimulationPage";
import UhOhTooEarlyPage from "./pages/UhOhTooEarlyPage";
import LeagueRecordsPage from "./pages/LeagueRecordsPage";
import InvalidLeaguePage from "./pages/InvalidLeaguePage";
import { initGoogleAnalytics } from "./utils/google_analytics";
import Layout from "./components/Layout";
import favicon from "./assets/img/favicon.png";

const App = () => {
    useEffect(() => {
        initGoogleAnalytics();

        // Dynamically set the favicon
        const link = document.createElement("link");
        link.rel = "icon";
        link.href = favicon;
        document.head.appendChild(link);
    }, []);

    return (
        <Layout>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route
                    path="/fantasy_stats/league/:leagueYear/:leagueId"
                    element={<LeaguePage />}
                />
                <Route
                    path="/fantasy_stats/simulation/:leagueYear/:leagueId"
                    element={<LeagueSimulationPage />}
                />
                <Route
                    path="/fantasy_stats/uh-oh-too-early/:page/:leagueYear/:leagueId"
                    element={<UhOhTooEarlyPage />}
                />
                <Route path="/fantasy_stats/awards" element={<AwardsPage />} />
                <Route
                    path="/fantasy_stats/league-records/:leagueYear/:leagueId"
                    element={<LeagueRecordsPage />}
                />
                <Route
                    path="/fantasy_stats/invalid-league"
                    element={<InvalidLeaguePage />}
                />
            </Routes>
        </Layout>
    );
};

export default App;
