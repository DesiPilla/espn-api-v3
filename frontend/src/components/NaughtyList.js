import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { safeFetch } from "../utils/api";
import CopyableContainer from "./CopyableContainer";
import PendingDataNotice from "./PendingDataNotice";
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
        <CopyableContainer
            title={`Naughty List - Week ${week}`}
            fileName={`naughty-list-week-${week}`}
        >
            <PendingDataNotice
                dataType="Naughty List"
                isPending={week > nCompletedWeeks}
            />
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
        </CopyableContainer>
    );
};

export default NaughtyList;
