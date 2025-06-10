import React, { useEffect, useState } from "react";
import LoadingRow from "./LoadingRow"; // Import the LoadingRow component
import "./styles/tableStyles.css"; // Adjust the path as needed

const WeeklyAwardsTable = ({ leagueYear, leagueId, week }) => {
  const [weeklyAwards, setWeeklyAwards] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWeeklyAwards = async () => {
      try {
        const res = await fetch(
          `/api/weekly-awards/${leagueYear}/${leagueId}/${week}/`
        );
        if (!res.ok) {
          throw new Error(`Failed to fetch weekly awards (status ${res.status})`);
        }
        const data = await res.json();
        setWeeklyAwards(data);
      } catch (err) {
        console.error("Error fetching weekly awards:", err);
      } finally {
        setLoading(false);
      }
    };

    if (leagueYear && leagueId && week) {
      fetchWeeklyAwards();
    }
  }, [leagueYear, leagueId, week]);

  return (
    <div className="wrapper-wide">
      <h2 className="text-xl font-semibold mb-4">Weekly Awards - Week {week}</h2>
      <p>
        <em>
          Note that scores have not yet been finalized for this week and award winners are likely to change.
          <br />
          Please check back on Tuesday morning for the final results.
        </em>
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Award</th>
            <th>Winner</th>
            <th>Award</th>
            <th>Loser</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <LoadingRow text="Loading Weekly Awards..." colSpan="4" />
          ) : !weeklyAwards || weeklyAwards.bestAwards.length === 0 ? (
            <tr>
              <td colSpan="4" style={{ textAlign: "center" }}>
                No weekly awards available.
              </td>
            </tr>
          ) : (
            weeklyAwards.bestAwards.map((bestAward, index) => (
              <tr
                key={index}
                className={index % 2 === 0 ? "even-row" : "odd-row"}
              >
                <td>{bestAward[0]}</td>
                <td>{bestAward[1]}</td>
                <td>{weeklyAwards.worstAwards[index][0]}</td>
                <td>{weeklyAwards.worstAwards[index][1]}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default WeeklyAwardsTable;
