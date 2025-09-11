import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCookie } from "../utils/csrf";
import "./styles/league.css";

const NewLeagueForm = () => {
  const [formData, setFormData] = useState({
    league_id: '',
    league_year: 2025,
    swid: '',
    espn_s2: '',
  });
  const navigate = useNavigate();

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const fetchWithRetry = async (url, options, retries) => {
        for (let i = 0; i <= retries; i++) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response;
            } catch (err) {
                if (i === retries) {
                    throw err;
                }
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        const maxRetries = 2;

        try {
            // Don't need to use safeFetch here because errors are handled differently
            const csrftoken = getCookie("csrftoken");
            const response = await fetchWithRetry(
                "/api/league-input/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrftoken,
                    },
                    credentials: "include",
                    body: JSON.stringify(formData),
                },
                maxRetries
            );

            const data = await response.json();

            console.log("Response status:", data.status);
            console.log("Response type:", data.code);
            console.log("Data:", data);

            if (response.status === 409 && data.code === "too_soon_league") {
                navigate(
                    `/fantasy_stats/uh-oh-too-early/league-homepage/${formData.league_year}/${formData.league_id}`
                );
            } else if (response.ok && data.redirect_url) {
                navigate(data.redirect_url);
            } else {
                setError(data.error || "Failed to create league.");
            }
        } catch (err) {
            setError("An unexpected error occurred.");
            console.error("Submission error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <h3>
                Don't see your league? Add it manually by entering your league's
                details below.
            </h3>
            <form onSubmit={handleSubmit}>
                <label>League ID: </label>
                <br />
                <input
                    type="text"
                    name="league_id"
                    value={formData.league_id}
                    onChange={handleChange}
                />
                <br />

                <label>League year: </label>
                <br />
                <input
                    type="number"
                    min="2017"
                    name="league_year"
                    value={formData.league_year}
                    onChange={handleChange}
                />
                <br />

                <label>SWID: </label>
                <br />
                <input
                    type="password"
                    name="swid"
                    value={formData.swid}
                    onChange={handleChange}
                />
                <br />

                <label>ESPN s2: </label>
                <br />
                <input
                    type="password"
                    name="espn_s2"
                    value={formData.espn_s2}
                    onChange={handleChange}
                />

                {error && <p className="error-message">{error}</p>}
                <div className="button-container">
                    <button type="submit" disabled={loading}>
                        {loading ? "Submitting..." : "Submit"}
                    </button>
                </div>
            </form>
        </>
    );
};

export default NewLeagueForm;
