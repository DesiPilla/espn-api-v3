import React from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import DoritoStatsLogo from "./components/DoritoStatsLogo";
import ReturnToHomePageButton from "./components/ReturnToHomePageButton";
import styles from "./pages/UhOhTooEarlyPage.module.css";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      apiError: false,
      errorMessage: null,
      errorDetails: null,
      showDetails: false, // Track if the dropdown is expanded
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, errorMessage: error.message };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React error caught by ErrorBoundary:", error, errorInfo);
    this.setState({ errorDetails: errorInfo.componentStack });
  }

  toggleDetails = () => {
    this.setState((prevState) => ({ showDetails: !prevState.showDetails }));
  };

  render() {
    if (this.state.hasError || this.state.apiError) {
      return (
        <>
          <div className="page-container">
            <div className={styles.layout}>
              <Header />
              <div className={styles.container}>
                <div className={styles.logoContainer}>
                  <DoritoStatsLogo />
                </div>
                <div className={styles.hero}>
                  <h1>
                    Something Went Wrong{" "}
                    <span role="img" aria-label="warning">
                      ⚠️
                    </span>
                  </h1>
                  <hr />
                </div>
                <div className={styles.messageBox}>
                  <p>
                    We're sorry, but an unexpected error occurred. Please try
                    again later.
                  </p>
                  <p>Thank you for your understanding.</p>
                  <div className={styles.buttons}>
                    <ReturnToHomePageButton insideErrorBoundary={true} />
                  </div>
                  <div>
                    <button
                      onClick={this.toggleDetails}
                      style={{
                        marginTop: "1rem",
                        backgroundColor: "#007bff",
                        color: "#fff",
                        padding: "0.5rem 1rem",
                        border: "none",
                        borderRadius: "5px",
                        cursor: "pointer",
                      }}
                    >
                      {this.state.showDetails ? "Hide Details" : "Show More"}
                    </button>
                    {this.state.showDetails && (
                      <div
                        style={{
                          marginTop: "1rem",
                          padding: "1rem",
                          backgroundColor: "#f8f9fa",
                          borderRadius: "5px",
                          boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
                          textAlign: "left",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        <strong>Error Message:</strong> {this.state.errorMessage}
                        <br />
                        <strong>Details:</strong> {this.state.errorDetails}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <Footer />
        </>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
