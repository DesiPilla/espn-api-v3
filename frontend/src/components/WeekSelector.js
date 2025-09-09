// src/components/WeekSelector.js
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './WeekSelector.css';

const WeekSelector = ({ onWeekChange, minWeek, maxWeek, disable = false }) => {
  const navigate = useNavigate();

  const selectedWeek = maxWeek - 1;

  const handleChange = (event) => {
    const newWeek = event.target.value;
    navigate(`?week=${newWeek}`);
    onWeekChange(newWeek); // Notify parent component of the week change
  };

  return (
    <div className="select">
      <select
        name="league-select"
        id="league-select"
        onChange={handleChange}
        value={selectedWeek}
        disabled={disable}
      >
        {Array.from({ length: maxWeek - minWeek + 1 }, (_, i) => {
          const week = minWeek + i;
          return (
            <option key={week} value={week}>
              Week {week}
            </option>
          );
        })}
      </select>
      <span className="focus"></span>
    </div>
  );
};

export default WeekSelector;
