import React, { useEffect, useState } from "react";
import LoadingRow from "./LoadingRow"; // Import the LoadingRow component
import "./styles/tableStyles.css"; // Adjust the path as needed

const PowerRankingsTable = ({ leagueYear, leagueId, week }) => {
  const [powerRankings, setPowerRankings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPowerRankings = async () => {
      try {
        const res = await fetch(
          `/api/power-rankings/${leagueYear}/${leagueId}/${week}/`
        );
        if (!res.ok) {
          throw new Error(`Failed to fetch power rankings (status ${res.status})`);
        }
        const data = await res.json();
        setPowerRankings(data);
      } catch (err) {
        console.error("Error fetching power rankings:", err);
      } finally {
        setLoading(false);
      }
    };

    if (leagueYear && leagueId && week) {
      fetchPowerRankings();
    }
  }, [leagueYear, leagueId, week]);

  return (
    <div className="wrapper-wide">
      <h2 className="text-xl font-semibold mb-4">Power Rankings - Week {week}</h2>
      <p>
        <em>
          Note that scores have not yet been finalized for this week and the
          Power Rankings are likely to change.
          <br />
          Please check back on Tuesday morning for the final results.
        </em>
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Team Name</th>
            <th>Owner</th>
            <th>Power Rank</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <LoadingRow text="Loading Power Rankings..." colSpan="3" />
          ) : powerRankings.length === 0 ? (
            <tr>
              <td colSpan="3" style={{ textAlign: "center" }}>
                No power rankings available.
              </td>
            </tr>
          ) : (
            powerRankings.map((team, index) => (
              <tr
                key={index}
                className={index % 2 === 0 ? "even-row" : "odd-row"}
              >
                <td>{team.team}</td>
                <td>{team.owner}</td>
                <td>{team.value}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default PowerRankingsTable;
