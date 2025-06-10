import React from "react";
import "./styles/loadingRow.css"; // Create this CSS file for spinner styles

const LoadingRow = ({ text, colSpan }) => {
  return (
    <tr style={{ backgroundColor: "white" }}>
      <td colSpan={colSpan} style={{ textAlign: "center" }}>
        <div className="loading-container">
          <div className="spinner"></div>
          <span>{text}</span>
        </div>
      </td>
    </tr>
  );
};

export default LoadingRow;
