// src/components/WeekSelector.js
import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './WeekSelector.css';

const WeekSelector = ({ currentWeek, onWeekChange, minWeek = 1, maxWeek = null, disable = false }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const selectedWeek = searchParams.get('week');

  const handleChange = (event) => {
    const newWeek = event.target.value;
    navigate(`?week=${newWeek}`);
    onWeekChange(newWeek); // Notify parent component of the week change
  };

  const effectiveMaxWeek = maxWeek !== null ? Math.min(maxWeek, currentWeek) : currentWeek; // Calculate effective max week

  console.log("currentWeek:", currentWeek);
  console.log("minWeek:", minWeek);
  console.log("effectiveMaxWeek:", effectiveMaxWeek);

  return (
    <div className="select">
      <select
        name="league-select"
        id="league-select"
        onChange={handleChange}
        value={disable ? effectiveMaxWeek : selectedWeek || currentWeek} // Set value to effectiveMaxWeek if disabled
        disabled={disable} // Disable the dropdown if disable is true
      >
        {disable ? (
          <option value={effectiveMaxWeek}>Week {effectiveMaxWeek}</option> // Show only effectiveMaxWeek if disabled
        ) : (
          (() => {
            try {
              return [...Array(effectiveMaxWeek - minWeek + 1).keys()].map((i) => {
                const week = minWeek + i;
                return (
                  <option key={week} value={week}>
                    Week {week}
                  </option>
                );
              });
            } catch (error) {
              console.error("Error generating week options:", error);
              return [1].map((week) => (
                <option key={week} value={week}>
                  Week {week}
                </option>
              ));
            }
          })()
        )}
      </select>
      <span className="focus"></span>
    </div>
  );
};

export default WeekSelector;
