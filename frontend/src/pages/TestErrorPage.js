import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { safeFetch, handleApiCall } from "../utils/api";

const TestErrorPage = () => {
    const navigate = useNavigate();
    const [shouldThrow, setShouldThrow] = useState(false);
    const [testEmailError, setTestEmailError] = useState(false);
    const [testUhOhTooSoonError, setTestUhOhTooSoonError] = useState(false);
    const [testInvalidLeagueError, setTestInvalidLeagueError] = useState(false);
    const [fetchError, setFetchError] = useState(null);

    if (shouldThrow) {
        // Simulate a React runtime error
        throw new Error("💥 TestErrorPage crashed intentionally!");
    }

    if (fetchError) {
        throw fetchError;
    }

    useEffect(() => {
        const triggerTestError = async () => {
            try {
                if (testEmailError) {
                    safeFetch("/api/test-error-email/")
                        .then((result) => {
                            result?.redirect && navigate(result.redirect);
                        })
                        .catch((err) => {
                            console.error("API call failed:", err);
                            setFetchError(err);
                        });
                    console.log(
                        "/api/test-error-email/ succeeded unexpectedly"
                    );
                    setTestEmailError(false);
                } else if (testUhOhTooSoonError) {
                    safeFetch("/api/test-uh-oh-too-soon-error/")
                        .then((result) => {
                            result?.redirect && navigate(result.redirect);
                        })
                        .catch((err) => {
                            console.error("API call failed:", err);
                            setFetchError(err);
                        });
                        console.log(
                            "/api/test-uh-oh-too-soon-error/ succeeded expectedly"
                        );
                } else if (testInvalidLeagueError) {
                    safeFetch("/api/test-invalid-league-error/")
                        .then((result) => {
                            result?.redirect && navigate(result.redirect);
                        })
                        .catch((err) => {
                            console.error("API call failed:", err);
                            setFetchError(err);
                        });
                    console.log(
                        "/api/test-invalid-league/ succeeded expectedly"
                    );
                }
            } catch (err) {
                console.error("API call failed as expected:", err);
                setFetchError(err);
            } finally {
                setTestEmailError(false);
                setTestUhOhTooSoonError(false);
                setTestInvalidLeagueError(false);
            }
        };

        triggerTestError();
    }, [
        testEmailError,
        testUhOhTooSoonError,
        testInvalidLeagueError,
        navigate,
    ]);

    return (
        <div style={{ padding: "1.5rem" }}>
            <h1
                style={{
                    fontSize: "1.5rem",
                    fontWeight: "bold",
                    marginBottom: "1rem",
                }}
            >
                Test Error Boundary
            </h1>
            <p style={{ marginBottom: "1rem" }}>
                Click the buttons below to simulate different errors. If your
                ErrorBoundary is working, you should see your custom error page
                instead of a green screen.
            </p>

            <div style={{ display: "flex", gap: "1.5rem" }}>
                <button
                    onClick={() => setShouldThrow(true)}
                    style={{
                        padding: "0.5rem 1rem",
                        borderRadius: "0.375rem",
                        borderWidth: "0.1rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                    }}
                >
                    Trigger React Runtime Error
                </button>

                <button
                    onClick={() => setTestEmailError(true)}
                    style={{
                        padding: "0.5rem 1rem",
                        borderRadius: "0.375rem",
                        borderWidth: "0.1rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                    }}
                >
                    Trigger API Error
                </button>

                <button
                    onClick={() => setTestUhOhTooSoonError(true)}
                    style={{
                        padding: "0.5rem 1rem",
                        borderRadius: "0.375rem",
                        borderWidth: "0.1rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                    }}
                >
                    Trigger "Uh Oh Too Soon" Error
                </button>

                <button
                    onClick={() => setTestInvalidLeagueError(true)}
                    style={{
                        padding: "0.5rem 1rem",
                        borderRadius: "0.375rem",
                        borderWidth: "0.1rem",
                        cursor: "pointer",
                        transition: "background-color 0.3s",
                    }}
                >
                    Trigger Invalid League Error
                </button>
            </div>
        </div>
    );
};

export default TestErrorPage;
