import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCookie } from "../utils/csrf";


const ReturningLeagueSelector = ({ dropdownClassName }) => {
  const [leaguesPreviousDistinct , setLeaguesPreviousDistinct] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
      fetch("/api/distinct-leagues-previous/")
      .then((res) => res.json())
      .then((data) => {
        setLeaguesPreviousDistinct(data);
      })
      .catch((error) => console.error("Error fetching distinct leagues:", error));
  }
  , []);

  const handleSelect = async (e) => {
    const leagueId = e.target.value;
    if (!leagueId) return;

    setLoading(true);
    setError('');

    try {
      const csrftoken = getCookie("csrftoken");

      const response = await fetch(`/api/copy-old-league/${leagueId}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok && data.redirect_url) {
        navigate(data.redirect_url);
      } else {
        setError(data.error || 'Failed to copy league.');
      }
    } catch (err) {
      console.error('Error copying league:', err);
      setError('An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h3>Returning for the new season? Select your old league and easily add it for the 2025-26 season.</h3>
      <div className="select" style={{ display: 'inline-block' }}>
        <select className={dropdownClassName} defaultValue="" onChange={handleSelect}>
          <option value=""> - Select your historical league - </option>
          {leaguesPreviousDistinct.map((league) => (
            <option key={league.league_id} value={league.league_id}>
              {league.league_year} - {league.league_name} ({league.league_id})
            </option>
          ))}
        </select>
      </div>
      {loading && <p>Copying league...</p>}
      {error && (
        <div className="error-message">
          <em>{error}</em>
        </div>
      )}
    </>
  );
};

export default ReturningLeagueSelector;
