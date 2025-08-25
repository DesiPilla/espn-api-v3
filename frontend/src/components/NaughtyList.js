import React, { useEffect, useState } from "react";
import "./styles/tableStyles.css"; // Adjust the path as needed
import "./styles/spinner.css"; // Import spinner styles

const NaughtyList = ({ leagueYear, leagueId, week }) => {
  const [naughtyList, setNaughtyList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNaughtyList = async () => {
      try {
        const res = await fetch(
          `/api/naughty-list/${leagueYear}/${leagueId}/${week}/`
        );
        if (!res.ok) {
          throw new Error(`Failed to fetch naughty list (status ${res.status})`);
        }
        const data = await res.json();
        setNaughtyList(data);
      } catch (err) {
        console.error("Error fetching naughty list:", err);
      } finally {
        setLoading(false);
      }
    };

    if (leagueYear && leagueId && week) {
      fetchNaughtyList();
    }
  }, [leagueYear, leagueId, week]);

  return (
    <div className="wrapper-wide">
      <h2 className="text-xl font-semibold mb-4">Naughty List - Week {week}</h2>
      <p>
        <em>
          Note that scores have not yet been finalized for this week and the
          Naughty List is likely to change.
          <br />
          Please check back on Tuesday morning for the final results.
        </em>
      </p>
      {loading ? (
        <div className="spinner-container">
          <div className="spinner"></div>
          <p>Loading Naughty List...</p>
        </div>
      ) : naughtyList.length === 0 ? (
        <p>🎉 No teams started any inactive players!</p>
      ) : (
        <ul>
          {naughtyList.map((entry, index) => (
            <li key={index}>
              ❌ {entry.team} started {entry.player} ({entry.active_status})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default NaughtyList;
