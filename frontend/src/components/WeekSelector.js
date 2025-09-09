// src/components/WeekSelector.js
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './WeekSelector.css';

const WeekSelector = ({
    onWeekChange,
    minWeek,
    maxWeek,
    selectedWeek = null,
    disable = false,
}) => {
    const navigate = useNavigate();

    // Ensure selectedWeek is never null
    selectedWeek = selectedWeek ?? maxWeek - 1;

    const handleChange = (event) => {
        const newWeek = event.target.value;
        navigate(`?week=${newWeek}`);
        onWeekChange(newWeek);
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
