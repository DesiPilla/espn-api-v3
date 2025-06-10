// src/components/WeekSelector.js
import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './WeekSelector.css';

const WeekSelector = ({ currentWeek, onWeekChange }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const selectedWeek = searchParams.get('week');

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
        value={selectedWeek || currentWeek}
      >
        {[...Array(currentWeek).keys()].map((i) => {
          const week = i + 1;
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
