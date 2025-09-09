import axios from "axios";

const api = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL,
});

export const safeFetch = async (endpoint, options, verbose = false) => {
    if (verbose) {
        console.log("=====================================");
        console.log(`[safeFetch] Starting fetch for endpoint: ${endpoint}`);
        console.log("[safeFetch] Options:", options);
    }

    let response;
    let data;

    try {
        response = await fetch(endpoint, options);
        if (verbose) {
            console.log(`[safeFetch] Received response:`, response);
        }

        // Attempt to parse JSON
        try {
            data = await response.json();
            if (verbose) {
                console.log("[safeFetch] Parsed JSON data:", data);
            }
        } catch (jsonErr) {
            if (verbose) {
                console.error("[safeFetch] Failed to parse JSON:", jsonErr);
            }
            throw new Error("Failed to parse JSON response");
        }

        if (verbose) {
            console.log(`Data code: ${data?.code}`);
        }
        if (response.status === 409 && data.code === "too_soon_league") {
            return {
                redirect: `/fantasy_stats/uh-oh-too-early/league-homepage/${data.leagueYear}/${data.leagueId}`,
            };
        } else if (response.status === 409 && data.code === "too_soon_simulations") {
            return {
                redirect: `/fantasy_stats/uh-oh-too-early/playoff-simulations/${data.leagueYear}/${data.leagueId}`,
            };
        } else if (response.status === 400 && data.code === "invalid_league") {
            return { redirect: "/fantasy_stats/invalid-league" };
        }

        if (!response.ok) {
            if (verbose) {
                console.error(
                    `[safeFetch] Unexpected response status: ${response.status}`,
                    data
                );
            }
            throw new Error(
                `Unexpected API response: ${response.status} ${
                    data?.message || ""
                }`
            );
        }

        if (verbose) {
            console.log("[safeFetch] Successful response, returning data.");
        }
        return data;
    } catch (err) {
        if (verbose) {
            console.error("[safeFetch] Caught error:", err);
        }
        throw err; // Let ErrorBoundary or caller handle
    } finally {
        if (verbose) {
            console.log(`[safeFetch] Finished fetch for endpoint: ${endpoint}`);
            console.log("=====================================");
        }
    }
};
