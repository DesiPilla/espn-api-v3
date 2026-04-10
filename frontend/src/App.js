import React, { useEffect } from 'react';
import { Routes, Route } from "react-router-dom";

import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import AwardsPage from "./components/AwardsReact";
import LeaguePage from "./pages/LeaguePage";
import LeagueSimulationPage from "./pages/LeagueSimulationPage";
import UhOhTooEarlyPage from "./pages/UhOhTooEarlyPage";
import LeagueRecordsPage from "./pages/LeagueRecordsPage";
import InvalidLeaguePage from "./pages/InvalidLeaguePage";
import NotFoundPage from "./pages/NotFoundPage";
import TestErrorPage from "./pages/TestErrorPage";

// Auth
import { AuthProvider } from "./components/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PasswordResetPage from "./pages/PasswordResetPage";
import PasswordResetConfirmPage from "./pages/PasswordResetConfirmPage";
import DashboardPage from "./pages/DashboardPage";

// Playoff Pool imports
import { PlayoffPoolAuthProvider } from "./components/PlayoffPool/AuthContext";
import PlayoffPoolHome from "./pages/PlayoffPool/PlayoffPoolHome";
import LeagueSetup from "./pages/PlayoffPool/LeagueSetup";
import LeagueDetail from "./pages/PlayoffPool/LeagueDetail";
import DraftInterface from "./pages/PlayoffPool/DraftInterface";
import DraftedTeams from "./pages/PlayoffPool/DraftedTeams";
import JoinLeague from "./pages/PlayoffPool/JoinLeague";
import EditTeams from "./pages/PlayoffPool/EditTeams";

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
            <AuthProvider>
                <Layout>
                    <Routes>
                        {/* Public auth routes */}
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                        <Route path="/password-reset" element={<PasswordResetPage />} />
                        <Route
                            path="/password-reset/confirm"
                            element={<PasswordResetConfirmPage />}
                        />

                        {/* Protected main-site routes */}
                        <Route
                            path="/"
                            element={
                                <ProtectedRoute>
                                    <DashboardPage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/league/:leagueYear/:leagueId/"
                            element={
                                <ProtectedRoute>
                                    <LeaguePage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/simulation/:leagueYear/:leagueId/"
                            element={
                                <ProtectedRoute>
                                    <LeagueSimulationPage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/uh-oh-too-early/:page/:leagueYear/:leagueId/"
                            element={
                                <ProtectedRoute>
                                    <UhOhTooEarlyPage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/awards"
                            element={
                                <ProtectedRoute>
                                    <AwardsPage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/league-records/:leagueYear/:leagueId/"
                            element={
                                <ProtectedRoute>
                                    <LeagueRecordsPage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/fantasy_stats/invalid-league/"
                            element={
                                <ProtectedRoute>
                                    <InvalidLeaguePage />
                                </ProtectedRoute>
                            }
                        />

                        {/* Playoff Pool Routes (own auth) */}
                        <Route
                            path="/playoff-pool/*"
                            element={
                                <PlayoffPoolAuthProvider>
                                    <Routes>
                                        <Route
                                            index
                                            element={<PlayoffPoolHome />}
                                        />
                                        <Route
                                            path="join"
                                            element={<JoinLeague />}
                                        />
                                        <Route
                                            path="create-league"
                                            element={<LeagueSetup />}
                                        />
                                        <Route
                                            path="league/:leagueId"
                                            element={<LeagueDetail />}
                                        />
                                        <Route
                                            path="league/:leagueId/edit-teams"
                                            element={<EditTeams />}
                                        />
                                        <Route
                                            path="league/:leagueId/draft"
                                            element={<DraftInterface />}
                                        />
                                        <Route
                                            path="league/:leagueId/teams"
                                            element={<DraftedTeams />}
                                        />
                                    </Routes>
                                </PlayoffPoolAuthProvider>
                            }
                        />

                        <Route path="/test-error" element={<TestErrorPage />} />
                        <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                </Layout>
            </AuthProvider>
        </ErrorBoundary>
    );
};

export default App;
