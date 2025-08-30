import React from 'react';

const LeagueSelector = ({ leaguesCurrent, leaguesPrevious, season, onSeasonChange, onLeagueSelect, dropdownClassName }) => {
  // Handle radio button change to update the selected season (current or previous)
  const handleSeasonChange = (event) => {
    onSeasonChange(event.target.value);  // Update season in the parent component
  };

  // Get the leagues to display based on the selected season
  const leaguesToDisplay =
    season === "current" ? leaguesCurrent : leaguesPrevious;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Select your league</h2>
      <div>
        {/* Radio buttons for selecting the season */}
        <label>
          <input
            type="radio"
            name="season"
            value="current"
            checked={season === "current"}
            onChange={handleSeasonChange}
          />
          Current season
        </label>
        <label>
          <input
            type="radio"
            name="season"
            value="previous"
            checked={season === "previous"}
            onChange={handleSeasonChange}
          />
          Previous season
        </label>
      </div>

      <div className="select">
        <select className={dropdownClassName} onChange={onLeagueSelect}>
          <option value="">- Select your league -</option>
          {leaguesToDisplay.map((league) => (
            <option key={league.league_id} value={`/fantasy_stats/league/${league.league_year}/${league.league_id}/`}>
              {league.league_year} - {league.league_name} ({league.league_id})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default LeagueSelector;
