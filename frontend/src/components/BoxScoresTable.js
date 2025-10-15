import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import LoadingRow from "./LoadingRow";
import { safeFetch } from "../utils/api";
import "./styles/tableStyles.css";
import * as htmlToImage from "html-to-image";

const BoxScoresTable = ({
    leagueYear,
    leagueId,
    week,
    loading: globalLoading,
}) => {
    const [boxScores, setBoxScores] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false); // Add state for copy success indicator
    const navigate = useNavigate();

    // ✅ Reference to the table wrapper for capturing
    const tableRef = useRef(null);
    const [copying, setCopying] = useState(false);

    if (fetchError) throw fetchError;

    useEffect(() => {
        const fetchBoxScores = async () => {
            setLoading(true);
            safeFetch(
                `/api/box-scores/${leagueYear}/${leagueId}/${week}/`,
                {},
                false,
                2
            )
                .then((data) => {
                    if (data?.redirect) {
                        navigate(data.redirect);
                    } else {
                        setBoxScores(data);
                    }
                })
                .catch((err) => {
                    console.error(
                        "ERROR: /api/box-scores/%s/%s/%s/",
                        leagueYear,
                        leagueId,
                        week,
                        err
                    );
                    setFetchError(err);
                })
                .finally(() => setLoading(false));
        };

        if (leagueYear && leagueId && week) {
            fetchBoxScores();
        }
    }, [leagueYear, leagueId, week]);

    // Reset success indicator after 3 seconds
    useEffect(() => {
        let timer;
        if (copySuccess) {
            timer = setTimeout(() => {
                setCopySuccess(false);
            }, 3000);
        }
        return () => clearTimeout(timer);
    }, [copySuccess]);

    const handleCopyAsImage = async () => {
        if (!tableRef.current) return;
        try {
            setCopying(true);

            // Get reference to the copy button element
            const copyBtn = document.querySelector(".copy-btn");
            // Hide button during capture
            const originalDisplay = copyBtn ? copyBtn.style.display : null;
            if (copyBtn) {
                copyBtn.style.display = "none";
            }

            // create PNG data URL from the element
            const dataUrl = await htmlToImage.toPng(tableRef.current);

            // Restore the button display
            if (copyBtn) {
                copyBtn.style.display = originalDisplay || "";
            }

            // convert data URL -> Blob
            const resp = await fetch(dataUrl);
            const blob = await resp.blob();

            // Preferred: write image to clipboard (modern Chrome/Edge)
            if (
                navigator.clipboard &&
                typeof window !== "undefined" &&
                typeof window.ClipboardItem !== "undefined"
            ) {
                try {
                    const item = new window.ClipboardItem({
                        "image/png": blob,
                    });
                    await navigator.clipboard.write([item]);
                    setCopySuccess(true); // Show success indicator instead of alert
                    return;
                } catch (err) {
                    console.warn(
                        "Navigator.clipboard.write failed, falling back to download:",
                        err
                    );
                    // fallthrough to fallback download
                }
            }

            // Fallback: download the image so the user can manually copy/share it
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `boxscores-week-${week}.png`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            setCopySuccess(true); // Show success indicator instead of alert
        } catch (err) {
            console.error("Error copying table as image:", err);
            // Don't show alert, let the button state indicate failure
        } finally {
            setCopying(false);
        }
    };

    return (
        <div className="wrapper-wide relative" ref={tableRef}>
            <div className="header-controls-row">
                <h2 className="text-xl font-semibold mb-4">
                    Box Scores - Week {week}
                </h2>

                {/* Copy button with success indicator */}
                <button
                    onClick={handleCopyAsImage}
                    className={`copy-btn ${copySuccess ? "copy-success" : ""}`}
                    disabled={copying}
                    title={copySuccess ? "Copied!" : "Copy table as image"}
                >
                    {copying
                        ? "⏳ Copying..."
                        : copySuccess
                        ? "✅ Copied!"
                        : "📋 Copy as Image"}
                </button>
            </div>

            <table className="table">
                <thead>
                    <tr>
                        <th>Home Team</th>
                        <th>Score</th>
                        <th>Away Team</th>
                    </tr>
                </thead>
                <tbody>
                    {globalLoading || loading ? (
                        <LoadingRow text="Loading Box Scores..." colSpan="3" />
                    ) : boxScores.length === 0 ? (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>
                                No box scores available.
                            </td>
                        </tr>
                    ) : (
                        boxScores.map((game, index) => (
                            <tr
                                key={index}
                                className={
                                    index % 2 === 0 ? "even-row" : "odd-row"
                                }
                            >
                                <td>{game.home_team}</td>
                                <td>
                                    {game.home_score} - {game.away_score}
                                </td>
                                <td>{game.away_team}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default BoxScoresTable;
