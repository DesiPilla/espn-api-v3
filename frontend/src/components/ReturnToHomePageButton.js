import React from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Button.module.css";

/**
 * Props:
 * - insideErrorBoundary (boolean) — true if used inside an ErrorBoundary
 */
const ReturnToHomePageButton = ({ insideErrorBoundary = false }) => {
    const navigate = useNavigate();

    const handleClick = () => {
        if (insideErrorBoundary) {
            // Force a full page reload through Django
            window.location.assign(window.location.origin + "/");
        } else {
            // Normal client-side navigation
            navigate("/");
        }
    };

    return (
        <div>
            <button className={styles.btn} onClick={handleClick}>
                Return to Homepage
            </button>
        </div>
    );
};

export default ReturnToHomePageButton;
