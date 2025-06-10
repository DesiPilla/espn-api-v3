import React, { useEffect } from 'react';
import { Routes, Route } from "react-router-dom";

import './App.css';
import AwardsPage from './components/AwardsReact';
import HomePage from './components/HomePage';
import LeaguePage from './pages/LeaguePage';
import UhOhTooEarlyPage from './pages/UhOhTooEarlyPage';
import { initGoogleAnalytics } from './utils/google_analytics';
import Layout from './components/Layout';


const App = () => {
  useEffect(() => {
    initGoogleAnalytics();
  }, []);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/fantasy_stats/league/:leagueYear/:leagueId" element={<LeaguePage />} />
        <Route path="/fantasy_stats/uh-oh-too-early/:page/:leagueYear/:leagueId" element={<UhOhTooEarlyPage />} />
        <Route path="/fantasy_stats/awards" element={<AwardsPage />} />
      </Routes>
    </Layout>
  );
};

export default App;
