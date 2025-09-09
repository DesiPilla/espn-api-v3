import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import AwardsPage from "./components/AwardsReact";
import HomePage from "./pages/HomePage";
import LeaguePage from "./pages/LeaguePage";
import LeagueSimulationPage from "./pages/LeagueSimulationPage";
import UhOhTooEarlyPage from "./pages/UhOhTooEarlyPage";
import LeagueRecordsPage from "./pages/LeagueRecordsPage";
import InvalidLeaguePage from "./pages/InvalidLeaguePage";
import NotFoundPage from "./pages/NotFoundPage";
import TestErrorPage from "./pages/TestErrorPage";
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
        <ErrorBoundary>
            <Layout>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route
                        path="/fantasy_stats/league/:leagueYear/:leagueId/"
                        element={<LeaguePage />}
                    />
                    <Route
                        path="/fantasy_stats/simulation/:leagueYear/:leagueId/"
                        element={<LeagueSimulationPage />}
                    />
                    <Route
                        path="/fantasy_stats/uh-oh-too-early/:page/:leagueYear/:leagueId/"
                        element={<UhOhTooEarlyPage />}
                    />
                    <Route
                        path="/fantasy_stats/awards"
                        element={<AwardsPage />}
                    />
                    <Route
                        path="/fantasy_stats/league-records/:leagueYear/:leagueId/"
                        element={<LeagueRecordsPage />}
                    />
                    <Route
                        path="/fantasy_stats/invalid-league/"
                        element={<InvalidLeaguePage />}
                    />
                    <Route path="/test-error" element={<TestErrorPage />} />
                    <Route path="*" element={<NotFoundPage />} />
                </Routes>
            </Layout>
        </ErrorBoundary>
    );
};

export default App;
