import React, { useState, useEffect } from 'react';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const ScoringSettingsEditor = ({
    leagueId,
    onClose,
    onSave,
    readOnly = false,
}) => {
    const [scoringSettings, setScoringSettings] = useState({});
    const [originalSettings, setOriginalSettings] = useState({});
    const [categorizedData, setCategorizedData] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadScoringSettings();
    }, [leagueId]);

    const loadScoringSettings = async () => {
        try {
            setLoading(true);
            const data = await playoffPoolAPI.getLeagueScoringSettings(
                leagueId
            );

            // Store categorized data for display
            setCategorizedData(data.scoring_settings || {});

            // Convert categorized settings to flat object for easier state management
            const flatSettings = {};
            Object.values(data.scoring_settings || {}).forEach(
                (categoryStats) => {
                    if (Array.isArray(categoryStats)) {
                        categoryStats.forEach((stat) => {
                            flatSettings[stat.stat_name] = stat.multiplier;
                        });
                    }
                }
            );

            setScoringSettings(flatSettings);
            setOriginalSettings(flatSettings);
        } catch (err) {
            setError("Failed to load scoring settings");
            console.error("Error loading scoring settings:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = (statName, value) => {
        setScoringSettings((prev) => ({
            ...prev,
            [statName]: parseFloat(value) || 0,
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setError(null);

            // Prepare scoring settings updates
            const updates = Object.entries(scoringSettings)
                .filter(
                    ([statName, value]) => value !== originalSettings[statName]
                )
                .map(([statName, value]) => ({
                    stat_name: statName,
                    multiplier: value,
                }));

            if (updates.length > 0) {
                await playoffPoolAPI.updateLeagueScoringSettings(
                    leagueId,
                    updates
                );
                setOriginalSettings(scoringSettings);
                onSave && onSave();
            }
        } catch (err) {
            setError("Failed to save scoring settings");
            console.error("Error saving scoring settings:", err);
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        setScoringSettings(originalSettings);
        onClose && onClose();
    };

    const hasChanges =
        JSON.stringify(scoringSettings) !== JSON.stringify(originalSettings);

    if (loading) {
        return (
            <div
                style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: "rgba(0, 0, 0, 0.5)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    zIndex: 1000,
                }}
            >
                <div
                    style={{
                        backgroundColor: "white",
                        padding: "2rem",
                        borderRadius: "0.5rem",
                        boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)",
                    }}
                >
                    Loading scoring settings...
                </div>
            </div>
        );
    }

    return (
        <div
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: "rgba(0, 0, 0, 0.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 1000,
                overflow: "auto",
                padding: "1rem",
            }}
        >
            <div
                style={{
                    backgroundColor: "white",
                    borderRadius: "0.5rem",
                    boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)",
                    maxWidth: "800px",
                    width: "100%",
                    maxHeight: "90vh",
                    overflow: "auto",
                }}
            >
                {/* Header */}
                <div
                    style={{
                        padding: "1.5rem",
                        borderBottom: "1px solid #e5e7eb",
                        background:
                            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        borderRadius: "0.5rem 0.5rem 0 0",
                    }}
                >
                    <h2
                        style={{
                            fontSize: "1.5rem",
                            fontWeight: "bold",
                            color: "white",
                            margin: 0,
                        }}
                    >
                        {readOnly
                            ? "Scoring Settings"
                            : "Edit Scoring Settings"}
                    </h2>
                    <p
                        style={{
                            color: "#e2e8f0",
                            fontSize: "0.875rem",
                            margin: "0.5rem 0 0 0",
                        }}
                    >
                        {readOnly
                            ? "Current point values for each statistical category"
                            : "Customize point values for each statistical category"}
                    </p>
                </div>

                {/* Content */}
                <div style={{ padding: "1.5rem" }}>
                    {error && (
                        <div
                            style={{
                                backgroundColor: "#fee2e2",
                                border: "1px solid #fecaca",
                                borderRadius: "0.375rem",
                                padding: "0.75rem",
                                marginBottom: "1rem",
                            }}
                        >
                            <p style={{ color: "#dc2626", margin: 0 }}>
                                {error}
                            </p>
                        </div>
                    )}

                    {/* Group settings by category */}
                    {Object.keys(categorizedData).length > 0 ? (
                        <div style={{ display: "grid", gap: "1.5rem" }}>
                            {Object.entries(categorizedData).map(
                                ([category, stats]) => (
                                    <div key={category}>
                                        <h4
                                            style={{
                                                fontSize: "1rem",
                                                fontWeight: "600",
                                                color: "#374151",
                                                marginBottom: "0.75rem",
                                                paddingBottom: "0.25rem",
                                                borderBottom:
                                                    "1px solid #e5e7eb",
                                            }}
                                        >
                                            {category}
                                        </h4>
                                        <div
                                            style={{
                                                display: "grid",
                                                gridTemplateColumns:
                                                    "repeat(auto-fit, minmax(280px, 1fr))",
                                                gap: "0.75rem",
                                            }}
                                        >
                                            {stats.map((stat) => (
                                                <div
                                                    key={stat.stat_name}
                                                    style={{
                                                        display: "flex",
                                                        alignItems: "center",
                                                        justifyContent:
                                                            "space-between",
                                                        padding: "0.75rem",
                                                        backgroundColor:
                                                            "#f9fafb",
                                                        border: "1px solid #e5e7eb",
                                                        borderRadius:
                                                            "0.375rem",
                                                    }}
                                                >
                                                    <label
                                                        style={{
                                                            fontSize:
                                                                "0.875rem",
                                                            color: "#374151",
                                                            fontWeight: "500",
                                                            flex: 1,
                                                        }}
                                                    >
                                                        {stat.display_name}
                                                    </label>
                                                    <input
                                                        type="number"
                                                        step="0.01"
                                                        value={
                                                            scoringSettings[
                                                                stat.stat_name
                                                            ] || 0
                                                        }
                                                        onChange={(e) =>
                                                            handleSettingChange(
                                                                stat.stat_name,
                                                                e.target.value
                                                            )
                                                        }
                                                        readOnly={readOnly}
                                                        disabled={readOnly}
                                                        style={{
                                                            width: "80px",
                                                            padding:
                                                                "0.375rem 0.5rem",
                                                            border: "1px solid #d1d5db",
                                                            borderRadius:
                                                                "0.25rem",
                                                            fontSize:
                                                                "0.875rem",
                                                            textAlign: "right",
                                                            marginLeft:
                                                                "0.5rem",
                                                            backgroundColor:
                                                                readOnly
                                                                    ? "#f3f4f6"
                                                                    : "white",
                                                            cursor: readOnly
                                                                ? "not-allowed"
                                                                : "text",
                                                        }}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )
                            )}
                        </div>
                    ) : (
                        <p style={{ textAlign: "center", color: "#6b7280" }}>
                            No scoring settings found for this league.
                        </p>
                    )}
                </div>

                {/* Footer */}
                <div
                    style={{
                        padding: "1.5rem",
                        borderTop: "1px solid #e5e7eb",
                        backgroundColor: "#f9fafb",
                        borderRadius: "0 0 0.5rem 0.5rem",
                        display: "flex",
                        justifyContent: "flex-end",
                        gap: "0.75rem",
                    }}
                >
                    <button
                        onClick={handleCancel}
                        style={{
                            padding: "0.75rem 1.5rem",
                            backgroundColor: "white",
                            border: "1px solid #d1d5db",
                            borderRadius: "0.375rem",
                            fontSize: "0.875rem",
                            fontWeight: "500",
                            color: "#374151",
                            cursor: "pointer",
                        }}
                    >
                        {readOnly ? "Close" : "Cancel"}
                    </button>
                    {!readOnly && (
                        <button
                            onClick={handleSave}
                            disabled={!hasChanges || saving}
                            style={{
                                padding: "0.75rem 1.5rem",
                                backgroundColor: hasChanges
                                    ? "#3b82f6"
                                    : "#9ca3af",
                                border: "none",
                                borderRadius: "0.375rem",
                                fontSize: "0.875rem",
                                fontWeight: "500",
                                color: "white",
                                cursor:
                                    hasChanges && !saving
                                        ? "pointer"
                                        : "not-allowed",
                                opacity: saving ? 0.7 : 1,
                            }}
                        >
                            {saving ? "Saving..." : "Save Changes"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScoringSettingsEditor;