import React, { useEffect, useState } from "react";
import LoadingRow from "./LoadingRow"; // Reuse the LoadingRow component
import "./styles/tableStyles.css"; // Adjust the path as needed

const StandingsTable = ({ leagueYear, leagueId, week }) => {
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStandings = async () => {
      try {
        const res = await fetch(`/api/standings/${leagueYear}/${leagueId}/${week}/`);
        if (!res.ok) {
          throw new Error(`Failed to fetch standings (status ${res.status})`);
        }
        const data = await res.json();
        setStandings(data);
      } catch (err) {
        console.error("Error fetching standings:", err);
      } finally {
        setLoading(false);
      }
    };

    if (leagueYear && leagueId && week) {
      fetchStandings();
    }
  }, [leagueYear, leagueId, week]);

  return (
    <div className="wrapper-wide">
      <h2 className="text-xl font-semibold mb-4">Standings through Week {week}</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Team</th>
            <th>Wins</th>
            <th>Losses</th>
            <th>Ties</th>
            <th>Points For</th>
            <th>Owner</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <LoadingRow text="Loading Standings..." colSpan="6" />
          ) : standings.length === 0 ? (
            <tr>
              <td colSpan="6" style={{ textAlign: "center" }}>
                No standings available.
              </td>
            </tr>
          ) : (
            standings.map((team, index) => (
              <tr
                key={index}
                className={index % 2 === 0 ? "even-row" : "odd-row"}
              >
                <td>{team.team}</td>
                <td>{team.wins}</td>
                <td>{team.losses}</td>
                <td>{team.ties}</td>
                <td>{team.pointsFor}</td>
                <td>{team.owner}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default StandingsTable;
