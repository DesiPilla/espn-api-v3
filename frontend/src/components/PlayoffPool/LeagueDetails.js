import React from 'react';

const LeagueDetails = ({ 
    league, 
    members,
    isAdmin,
    draftInProgress,
    draftComplete,
    handleStartDraft,
    handleViewDraftedTeams,
    handleEditTeams,
    handleOpenScoringEditor,
    handleResetDraft,
}) => {
    const containerStyle = {
        backgroundColor: "white",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        overflow: "hidden",
    };

    return (
        <div style={containerStyle}>
            {/* Enhanced Header with League Information */}
            <div
                style={{
                    backgroundColor: "#f8fafc",
                    borderBottom: "1px solid #e2e8f0",
                    padding: "24px",
                }}
            >
                {/* Main Header */}
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        marginBottom: "20px",
                    }}
                >
                    <div>
                        <h2
                            style={{
                                fontSize: "24px",
                                fontWeight: "700",
                                color: "#1f2937",
                                margin: 0,
                                marginBottom: "8px",
                            }}
                        >
                            {league?.name || "League Details"}
                        </h2>
                        <p
                            style={{
                                fontSize: "14px",
                                color: "#6b7280",
                                margin: 0,
                            }}
                        >
                            Created{" "}
                            {league?.created_at_est
                                ? new Date(
                                      league.created_at_est
                                  ).toLocaleDateString("en-US", {
                                      timeZone: "America/New_York",
                                      month: "short",
                                      day: "numeric",
                                      year: "numeric",
                                  }) +
                                  " by " +
                                  (league?.created_by?.username || "Unknown")
                                : league?.created_at
                                ? new Date(
                                      league.created_at
                                  ).toLocaleDateString("en-US", {
                                      month: "short",
                                      day: "numeric",
                                      year: "numeric",
                                  }) +
                                  " by " +
                                  (league?.created_by?.username || "Unknown")
                                : "by " +
                                  (league?.created_by?.username || "Unknown")}
                        </p>
                    </div>
                    <span
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            padding: "8px 12px",
                            borderRadius: "12px",
                            fontSize: "12px",
                            fontWeight: "600",
                            backgroundColor: league?.is_draft_complete
                                ? "#dcfce7"
                                : league?.draft_started_at
                                ? "#fef3c7"
                                : "#f1f5f9",
                            color: league?.is_draft_complete
                                ? "#166534"
                                : league?.draft_started_at
                                ? "#92400e"
                                : "#64748b",
                        }}
                    >
                        {league?.is_draft_complete
                            ? "Draft Complete"
                            : league?.draft_started_at
                            ? "Draft In Progress"
                            : "Draft Not Started"}
                    </span>
                </div>

                {/* League Stats Grid */}
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns:
                            "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "16px",
                        marginBottom: "16px",
                    }}
                >
                    {/* Teams Count */}
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "12px",
                            padding: "12px 16px",
                            backgroundColor: "#ffffff",
                            borderRadius: "8px",
                            border: "1px solid #e2e8f0",
                        }}
                    >
                        <div
                            style={{
                                width: "40px",
                                height: "40px",
                                backgroundColor: "#3b82f6",
                                borderRadius: "8px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            <span
                                style={{
                                    color: "white",
                                    fontSize: "18px",
                                    fontWeight: "bold",
                                }}
                            >
                                👥
                            </span>
                        </div>
                        <div>
                            <div
                                style={{
                                    fontSize: "18px",
                                    fontWeight: "700",
                                    color: "#1f2937",
                                }}
                            >
                                {members?.length || 0} /{" "}
                                {league?.num_teams || 0}
                            </div>
                            <div style={{ fontSize: "12px", color: "#6b7280" }}>
                                Teams
                            </div>
                        </div>
                    </div>

                    {/* Roster Size */}
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "12px",
                            padding: "12px 16px",
                            backgroundColor: "#ffffff",
                            borderRadius: "8px",
                            border: "1px solid #e2e8f0",
                        }}
                    >
                        <div
                            style={{
                                width: "40px",
                                height: "40px",
                                backgroundColor: "#10b981",
                                borderRadius: "8px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            <span
                                style={{
                                    color: "white",
                                    fontSize: "18px",
                                    fontWeight: "bold",
                                }}
                            >
                                🏈
                            </span>
                        </div>
                        <div>
                            <div
                                style={{
                                    fontSize: "18px",
                                    fontWeight: "700",
                                    color: "#1f2937",
                                }}
                            >
                                {league?.total_roster_size || 0}
                            </div>
                            <div style={{ fontSize: "12px", color: "#6b7280" }}>
                                Roster Size
                            </div>
                        </div>
                    </div>

                    {/* NFL Season */}
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "12px",
                            padding: "12px 16px",
                            backgroundColor: "#ffffff",
                            borderRadius: "8px",
                            border: "1px solid #e2e8f0",
                        }}
                    >
                        <div
                            style={{
                                width: "40px",
                                height: "40px",
                                backgroundColor: "#8b5cf6",
                                borderRadius: "8px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            <span
                                style={{
                                    color: "white",
                                    fontSize: "18px",
                                    fontWeight: "bold",
                                }}
                            >
                                📅
                            </span>
                        </div>
                        <div>
                            <div
                                style={{
                                    fontSize: "14px",
                                    fontWeight: "600",
                                    color: "#1f2937",
                                }}
                            >
                                {league?.league_year || "Unknown"}
                            </div>
                            <div style={{ fontSize: "12px", color: "#6b7280" }}>
                                NFL Season
                            </div>
                        </div>
                    </div>
                </div>

                {/* Roster Configuration Details */}
                {league?.roster_config && (
                    <div
                        style={{
                            backgroundColor: "#ffffff",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                            padding: "12px 16px",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "13px",
                                fontWeight: "600",
                                color: "#1f2937",
                                marginBottom: "8px",
                            }}
                        >
                            📋 Roster Configuration
                        </div>
                        <div
                            style={{
                                fontSize: "12px",
                                color: "#374151",
                                display: "flex",
                                flexWrap: "wrap",
                                gap: "12px",
                            }}
                        >
                            {(() => {
                                const positionOrder = [
                                    "qb",
                                    "rb",
                                    "wr",
                                    "te",
                                    "flex",
                                    "dst",
                                    "k",
                                ];
                                const entries = Object.entries(
                                    league.roster_config
                                );

                                // Sort entries based on position order
                                const sortedEntries = entries.sort((a, b) => {
                                    const posA = a[0].toLowerCase();
                                    const posB = b[0].toLowerCase();
                                    const indexA = positionOrder.indexOf(posA);
                                    const indexB = positionOrder.indexOf(posB);

                                    // If position not in order list, put it at the end
                                    if (indexA === -1) return 1;
                                    if (indexB === -1) return -1;
                                    return indexA - indexB;
                                });

                                return sortedEntries
                                    .filter(([position, value]) => {
                                        // For flex, check if it's an object with count
                                        if (position.toLowerCase() === "flex") {
                                            return typeof value === "object"
                                                ? value.count > 0
                                                : value > 0;
                                        }
                                        return value > 0;
                                    })
                                    .map(([position, value]) => {
                                        const count =
                                            typeof value === "object"
                                                ? value.count
                                                : value;
                                        const displayPos =
                                            position.toUpperCase();

                                        return (
                                            <span
                                                key={position}
                                                style={{
                                                    display: "inline-flex",
                                                    alignItems: "center",
                                                    padding: "4px 8px",
                                                    backgroundColor: "#f8fafc",
                                                    borderRadius: "4px",
                                                    fontWeight: "500",
                                                    border: "1px solid #e2e8f0",
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        fontWeight: "700",
                                                    }}
                                                >
                                                    {count}
                                                </span>
                                                &nbsp;
                                                {displayPos}
                                            </span>
                                        );
                                    });
                            })()}
                        </div>
                    </div>
                )}
            </div>

            {/* Action Buttons - Show when draft is started or complete */}
            {(draftInProgress || draftComplete) && (
                <div
                    style={{
                        backgroundColor: "#ffffff",
                        borderTop: "1px solid #e2e8f0",
                        padding: "16px 24px",
                        display: "flex",
                        justifyContent: "flex-end",
                        alignItems: "center",
                        gap: "12px",
                        flexWrap: "wrap",
                    }}
                >
                    {draftInProgress && isAdmin && (
                        <button
                            onClick={handleStartDraft}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                padding: "12px 20px",
                                backgroundColor: "#3b82f6",
                                color: "white",
                                fontWeight: "600",
                                fontSize: "14px",
                                borderRadius: "8px",
                                border: "none",
                                cursor: "pointer",
                                transition: "background-color 0.15s",
                                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                            }}
                            onMouseEnter={(e) =>
                                (e.target.style.backgroundColor = "#2563eb")
                            }
                            onMouseLeave={(e) =>
                                (e.target.style.backgroundColor = "#3b82f6")
                            }
                        >
                            Manage Draft
                        </button>
                    )}

                    {draftComplete && (
                        <button
                            onClick={handleViewDraftedTeams}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                padding: "12px 20px",
                                backgroundColor: "#8b5cf6",
                                color: "white",
                                fontWeight: "600",
                                fontSize: "14px",
                                borderRadius: "8px",
                                border: "none",
                                cursor: "pointer",
                                transition: "background-color 0.15s",
                                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                            }}
                            onMouseEnter={(e) =>
                                (e.target.style.backgroundColor = "#7c3aed")
                            }
                            onMouseLeave={(e) =>
                                (e.target.style.backgroundColor = "#8b5cf6")
                            }
                        >
                            View Drafted Teams
                        </button>
                    )}

                    {isAdmin && (
                        <button
                            onClick={handleEditTeams}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                padding: "12px 20px",
                                backgroundColor: "#0891b2",
                                color: "white",
                                fontWeight: "600",
                                fontSize: "14px",
                                borderRadius: "8px",
                                border: "none",
                                cursor: "pointer",
                                transition: "background-color 0.15s",
                                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                            }}
                            onMouseEnter={(e) =>
                                (e.target.style.backgroundColor = "#0e7490")
                            }
                            onMouseLeave={(e) =>
                                (e.target.style.backgroundColor = "#0891b2")
                            }
                        >
                            Edit Teams
                        </button>
                    )}

                    <button
                        onClick={handleOpenScoringEditor}
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            padding: "12px 20px",
                            backgroundColor: "#7c3aed",
                            color: "white",
                            fontWeight: "600",
                            fontSize: "14px",
                            borderRadius: "8px",
                            border: "none",
                            cursor: "pointer",
                            transition: "background-color 0.15s",
                            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                        }}
                        onMouseEnter={(e) =>
                            (e.target.style.backgroundColor = "#6d28d9")
                        }
                        onMouseLeave={(e) =>
                            (e.target.style.backgroundColor = "#7c3aed")
                        }
                    >
                        {draftInProgress || draftComplete
                            ? "Show Scoring Settings"
                            : isAdmin
                            ? "Edit Scoring Settings"
                            : "Show Scoring Settings"}
                    </button>

                    {isAdmin && (draftInProgress || draftComplete) && (
                        <button
                            onClick={handleResetDraft}
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                padding: "12px 20px",
                                backgroundColor: "#dc2626",
                                color: "white",
                                fontWeight: "600",
                                fontSize: "14px",
                                borderRadius: "8px",
                                border: "none",
                                cursor: "pointer",
                                transition: "background-color 0.15s",
                                boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                            }}
                            onMouseEnter={(e) =>
                                (e.target.style.backgroundColor = "#b91c1c")
                            }
                            onMouseLeave={(e) =>
                                (e.target.style.backgroundColor = "#dc2626")
                            }
                        >
                            Reset Draft
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default LeagueDetails;
