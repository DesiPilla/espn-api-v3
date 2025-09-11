import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { safeFetch } from "../utils/api";
import "./styles/tableStyles.css";
import "./styles/spinner.css";

const NaughtyList = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
    nCompletedWeeks,
}) => {
    const [naughtyList, setNaughtyList] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false); // Internal loading state
    const navigate = useNavigate();

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const fetchNaughtyList = () => {
            setLoading(true); // Set internal loading to true
            safeFetch(
                `/api/naughty-list/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setNaughtyList(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/naughty-list/%s/%s/%s/",
                        leagueYear,
                        leagueId,
                        week,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => {
                    setLoading(false); // Set internal loading to false
                });
        };

        if (leagueYear && leagueId && week) {
            fetchNaughtyList();
        }
    }, [leagueYear, leagueId, week]);

    return (
        <div className="wrapper-wide">
            <h2 className="text-xl font-semibold mb-4">
                Naughty List - Week {week}
            </h2>
            {week > nCompletedWeeks && ( // Only display note if week > nCompletedWeeks
                <p>
                    <em>
                        Note that scores have not yet been finalized for this
                        week and the Naughty List is likely to change.
                        <br />
                        Please check back on Tuesday morning for the final
                        results.
                    </em>
                </p>
            )}
            {globalLoading || loading ? ( // Show spinner if global or internal loading is true
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
                            ❌ {entry.team} started {entry.player} (
                            {entry.active_status})
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default NaughtyList;
