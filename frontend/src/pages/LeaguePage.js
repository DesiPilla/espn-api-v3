import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import WeekSelector from '../components/WeekSelector'; // Adjust path as needed
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import BoxScoresTable from '../components/BoxScoresTable'; // Adjust path as needed
import WeeklyAwardsTable from '../components/WeeklyAwardsTable'; // Adjust path as needed
import PowerRankingsTable from '../components/PowerRankingsTable'; // Import the new table
import LuckIndexTable from '../components/LuckIndexTable'; // Import the new table
import StandingsTable from '../components/StandingsTable'; // Import the StandingsTable component
import NaughtyList from "../components/NaughtyList"; // Update import to NaughtyList
import Footer from '../components/Footer'; // Import the Footer component

import '../components/styles/league.css';

const LeaguePage = () => {
  const { leagueYear, leagueId } = useParams();
  const location = useLocation(); // Access the current URL
  const navigate = useNavigate(); // Add navigation hook
  const [leagueData, setLeagueData] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(null); // Track the current week separately
  const [retry, setRetry] = useState(false); // Track if a retry is needed

  // Preload the league data for faster loading later on
  useEffect(() => {
    fetch(`/api/league/${leagueYear}/${leagueId}/`);
  }, []);

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
  }, [leagueId, leagueYear, selectedWeek, navigate]);

  // Fetch the league data from the backend using the leagueId and leagueYear
  useEffect(() => {
    const fetchLeagueData = async () => {
      try {
        const response = await fetch(`/api/league/${leagueYear}/${leagueId}/`);
        if (!response.ok) {
          throw new Error(`Failed to fetch league data (status ${response.status})`);
        }
        const data = await response.json();
        setLeagueData(data);
        console.log("League data fetched:", data);
      } catch (error) {
        console.error("Error fetching league data:", error);
        if (!retry) {
          console.log("Retrying league data fetch...");
          setRetry(true); // Trigger a retry
        }
      }
    };

    fetchLeagueData();
  }, [leagueYear, leagueId, retry, navigate]); // Re-fetch if the URL parameters or retry state changes

  // Set the default current week and selected week
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const weekFromUrl = queryParams.get('week');
    if (weekFromUrl) {
      console.log("Setting selected week from URL:", weekFromUrl);
      setSelectedWeek(parseInt(weekFromUrl, 10)); // Initialize selectedWeek from the URL
    }

    const fetchCurrentWeek = async () => {
      try {
        console.log("Fetching current week...");
        const result = await fetch(`/api/league/${leagueYear}/${leagueId}/current-week/`);
        if (!result.ok) {
          throw new Error(`Failed to fetch current week (status ${result.status})`);
        }
        const data = await result.json();
        setCurrentWeek(data.current_week); // Always set the current week
        if (!weekFromUrl) {
          setSelectedWeek(data.current_week); // Only set selectedWeek if not already defined
        }
        console.log("Current week set to:", data.current_week);
      } catch (error) {
        console.error("Error fetching current week:", error);
        if (!retry) {
          console.log("Retrying current week fetch...");
          setRetry(true); // Trigger a retry
        }
      }
    };

    fetchCurrentWeek(); // Call the async function
  }, [location.search, leagueYear, leagueId, retry]);

  const handleWeekChange = (newWeek) => {
    setSelectedWeek(newWeek); // Update the selected week
    const queryParams = new URLSearchParams(location.search);
    queryParams.set('week', newWeek); // Update the URL query parameter
    window.history.replaceState(null, '', `${location.pathname}?${queryParams.toString()}`);
  };

  if (!leagueData || currentWeek === null) {
    return <div>Loading...</div>;
  }
  console.log("Selected week:", selectedWeek);
  console.log("Current week:", currentWeek);

  return (
    <div>
      <h1>{leagueData.league_name}</h1>
      <p>Year: {leagueData.league_year}</p>
      <p>League ID: {leagueData.league_id}</p>

      <WeekSelector
        currentWeek={currentWeek} // Always use currentWeek for WeekSelector
        onWeekChange={handleWeekChange} // Pass the handler to WeekSelector
      />
      <ReturnToHomePageButton />

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

      <Footer />
    </div>
  );
};

export default LeaguePage;
