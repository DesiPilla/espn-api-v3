import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import Header from "./Header";
import Footer from "./Footer";
import LeagueSelector from "./LeagueSelector";
import NewLeagueForm from './NewLeagueForm';
import ReturningLeagueSelector from '../components/ReturningLeagueSelector';

const HomePage = () => {;

  useEffect(() => {
    fetch(`${process.env.REACT_APP_API_BASE_URL}/api/get-csrf-token/`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .catch((error) => {
        console.error("Error fetching CSRF token:", error);
      });
  }, []);


  const [leaguesCurrent, setLeaguesCurrent] = useState([]);
  const [leaguesPrevious, setLeaguesPrevious] = useState([]);
  const [season, setSeason] = useState("current");

  const navigate = useNavigate(); // Create navigate function

  useEffect(() => {
    fetch("/api/leagues/")
      .then((res) => res.json())
      .then((data) => {
        setLeaguesCurrent(data.leagues_current_year);
        setLeaguesPrevious(data.leagues_previous_year);
      })
      .catch((error) => console.error("Error fetching leagues:", error));
  }, []);

  const handleLeagueSelect = (event) => {
    const url = event.target.value;
    if (url) {
      console.log("Navigating to:", url); // Debugging line
      navigate(url); // Use navigate for route change
    }
  };

  const dropdownClassName = "league-dropdown"; // Common dropdown class

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <Header />

      <LeagueSelector
        leaguesCurrent={leaguesCurrent}
        leaguesPrevious={leaguesPrevious}
        season={season}
        onSeasonChange={setSeason}
        onLeagueSelect={handleLeagueSelect}
        dropdownClassName={dropdownClassName} // Pass common dropdown class
      />

      <ReturningLeagueSelector
        onLeagueSelect={handleLeagueSelect}
        dropdownClassName={dropdownClassName} // Pass common dropdown class
      />
      <NewLeagueForm />
      <Footer />
    </div>
  );
};

export default HomePage;
