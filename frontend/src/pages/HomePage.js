import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";
import LeagueSelector from "../components/LeagueSelector";
import NewLeagueForm from "../components/NewLeagueForm";
import ReturningLeagueSelector from "../components/ReturningLeagueSelector";
import CookiesInstructionsBox from "../components/CookiesInstructionsBox";
import { safeFetch, handleApiCall } from "../utils/api";
import "../components/styles/league.css";

const HomePage = () => {
    const [leaguesCurrent, setLeaguesCurrent] = useState([]);
    const [leaguesPrevious, setLeaguesPrevious] = useState([]);
    const [season, setSeason] = useState("current");
    const [fetchError, setFetchError] = useState(null);
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

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

    useEffect(() => {
        safeFetch("/api/leagues/", {}, false, 2)
            .then((data) => {
                setLeaguesCurrent(data.leagues_current_year);
                setLeaguesPrevious(data.leagues_previous_year);
            })
            .catch((error) => {
                console.error("Error fetching leagues:", error);
                setFetchError(error);
            });
    }, []);

    const handleLeagueSelect = (event) => {
        const url = event.target.value;
        if (url) {
            console.log("Navigating to:", url);
            navigate(url);
        }
    };

    const dropdownClassName = "league-dropdown";

    return (
        <div>
            <div className="league-content">
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
                <CookiesInstructionsBox />
                <br></br>
            </div>
            <Footer />
        </div>
    );
};

export default HomePage;
