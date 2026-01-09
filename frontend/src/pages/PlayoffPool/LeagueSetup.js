import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayoffPoolAuth } from '../../components/PlayoffPool/AuthContext';
import playoffPoolAPI from '../../utils/PlayoffPool/api';

const LeagueSetup = () => {
  const [formData, setFormData] = useState({
      name: "",
      num_teams: 8,
      positions_included: ["QB", "RB", "WR", "TE", "K", "DST"],
      roster_config: {
          QB: 1,
          RB: 2,
          WR: 2,
          TE: 1,
          K: 1,
          DST: 1,
      },
      flex: {
          enabled: false,
          count: 0,
          eligible_positions: ["RB", "WR", "TE"],
      },
      scoring_settings: {},
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [positionOptions, setPositionOptions] = useState([]);
  const [scoringCategories, setScoringCategories] = useState({});

  const { user } = usePlayoffPoolAuth();
  const navigate = useNavigate();

  useEffect(() => {
      loadScoringSettings();
  }, []);

  const loadScoringSettings = async () => {
      try {
          const data = await playoffPoolAPI.getScoringSettings();
          const positions = data.position_choices || [
              { value: "QB", label: "Quarterback" },
              { value: "RB", label: "Running Back" },
              { value: "WR", label: "Wide Receiver" },
              { value: "TE", label: "Tight End" },
              { value: "K", label: "Kicker" },
              { value: "DST", label: "Defense/Special Teams" },
          ];

          // Reorder positions: QB, RB, WR, TE, DST, K (FLEX will be added separately in table)
          const positionOrder = ["QB", "RB", "WR", "TE", "DST", "K"];
          const orderedPositions = positionOrder
              .map((pos) => positions.find((p) => p.value === pos))
              .filter(Boolean);

          setPositionOptions(orderedPositions);

          // Set scoring categories and initialize default scoring settings
          if (data.scoring_categories) {
              setScoringCategories(data.scoring_categories);

              // Initialize default scoring settings in formData
              const defaultScoringSettings = {};
              Object.values(data.scoring_categories).forEach(
                  (categoryStats) => {
                      categoryStats.forEach((stat) => {
                          defaultScoringSettings[stat.stat_name] =
                              stat.default_value;
                      });
                  }
              );

              setFormData((prev) => ({
                  ...prev,
                  scoring_settings: defaultScoringSettings,
              }));
          }
      } catch (err) {
          console.error("Error loading scoring settings:", err);
          // Fallback to default positions in correct order
          setPositionOptions([
              { value: "QB", label: "Quarterback" },
              { value: "RB", label: "Running Back" },
              { value: "WR", label: "Wide Receiver" },
              { value: "TE", label: "Tight End" },
              { value: "DST", label: "Defense/Special Teams" },
              { value: "K", label: "Kicker" },
          ]);
      }
  };

  const handleChange = (e) => {
      const { name, value } = e.target;
      setFormData({
          ...formData,
          [name]: name === "num_teams" ? parseInt(value) : value,
      });
      if (error) setError(null);
  };

  const handlePositionChange = (position) => {
      const updatedPositions = formData.positions_included.includes(position)
          ? formData.positions_included.filter((p) => p !== position)
          : [...formData.positions_included, position];

      // Update roster config when positions change
      const updatedRosterConfig = { ...formData.roster_config };

      if (
          updatedPositions.includes(position) &&
          !formData.roster_config[position]
      ) {
          // Add position with default count
          updatedRosterConfig[position] = 1;
      } else if (
          !updatedPositions.includes(position) &&
          formData.roster_config[position]
      ) {
          // Remove position from roster config
          delete updatedRosterConfig[position];
      }

      setFormData({
          ...formData,
          positions_included: updatedPositions,
          roster_config: updatedRosterConfig,
      });
  };

  const handleRosterCountChange = (position, count) => {
      setFormData({
          ...formData,
          roster_config: {
              ...formData.roster_config,
              [position]: parseInt(count) || 0,
          },
      });
  };

  const handleFlexChange = (field, value) => {
      const updatedFlex = {
          ...formData.flex,
          [field]: value,
      };

      // When enabling flex, set default count to 1 if it's currently 0
      if (field === "enabled" && value === true && formData.flex.count === 0) {
          updatedFlex.count = 1;
      }

      setFormData({
          ...formData,
          flex: updatedFlex,
      });
  };

  const handleFlexPositionToggle = (position) => {
      const updatedPositions = formData.flex.eligible_positions.includes(
          position
      )
          ? formData.flex.eligible_positions.filter((p) => p !== position)
          : [...formData.flex.eligible_positions, position];

      handleFlexChange("eligible_positions", updatedPositions);
  };

  const handleScoringChange = (statName, value) => {
      setFormData({
          ...formData,
          scoring_settings: {
              ...formData.scoring_settings,
              [statName]: parseFloat(value) || 0,
          },
      });
  };

  const handleSubmit = async (e) => {
      e.preventDefault();

      if (!formData.name.trim()) {
          setError("League name is required");
          return;
      }

      if (formData.positions_included.length === 0) {
          setError("At least one position must be selected");
          return;
      }

      // Validate roster counts
      const hasInvalidCounts = Object.values(formData.roster_config).some(
          (count) => count < 1
      );
      if (hasInvalidCounts) {
          setError("All position counts must be at least 1");
          return;
      }

      try {
          setLoading(true);
          setError(null);

          // Prepare data for submission
          const submissionData = {
              name: formData.name.trim(),
              num_teams: formData.num_teams,
              positions_included: formData.positions_included,
              roster_config: {
                  ...formData.roster_config,
                  ...(formData.flex.enabled && formData.flex.count > 0
                      ? {
                            flex: {
                                count: formData.flex.count,
                                eligible_positions:
                                    formData.flex.eligible_positions,
                            },
                        }
                      : {}),
              },
              scoring_settings: formData.scoring_settings,
          };

          const league = await playoffPoolAPI.createLeague(submissionData);
          navigate(`/playoff-pool/league/${league.id}`);
      } catch (err) {
          setError(err.response?.data?.detail || "Failed to create league");
          console.error("Error creating league:", err);
      } finally {
          setLoading(false);
      }
  };

  const handleCancel = () => {
      navigate("/playoff-pool");
  };

  return (
      <div
          style={{
              minHeight: "100vh",
              backgroundColor: "#f3f4f6",
              padding: "2rem 0",
          }}
      >
          <div
              style={{ maxWidth: "80rem", margin: "0 auto", padding: "0 1rem" }}
          >
              {/* ESPN-Style Header Card */}
              <div
                  style={{
                      backgroundColor: "white",
                      border: "1px solid #d1d5db",
                      overflow: "hidden",
                      marginBottom: "2rem",
                      borderRadius: "0.5rem",
                  }}
              >
                  {/* Header Section */}
                  <div
                      style={{
                          background:
                              "linear-gradient(to right, #2563eb, #1e40af)",
                          color: "white",
                      }}
                  >
                      <div style={{ padding: "1.5rem 2rem" }}>
                          <div
                              style={{
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "space-between",
                              }}
                          >
                              <div>
                                  <h1
                                      style={{
                                          fontSize: "1.875rem",
                                          fontWeight: "bold",
                                          margin: 0,
                                          letterSpacing: "-0.025em",
                                      }}
                                  >
                                      🏈 Create New League
                                  </h1>
                                  <p
                                      style={{
                                          color: "#dbeafe",
                                          marginTop: "0.5rem",
                                          fontSize: "1.125rem",
                                          margin: "0.5rem 0 0 0",
                                      }}
                                  >
                                      Set up your playoff pool with custom
                                      roster configurations
                                  </p>
                              </div>
                              <div
                                  style={{
                                      backgroundColor:
                                          "rgba(255, 255, 255, 0.2)",
                                      borderRadius: "0.5rem",
                                      padding: "1rem",
                                      textAlign: "center",
                                  }}
                              >
                                  <div
                                      style={{
                                          fontSize: "1.125rem",
                                          fontWeight: "600",
                                          color: "#dbeafe",
                                      }}
                                  >
                                      League Setup
                                  </div>
                              </div>
                          </div>
                      </div>
                  </div>

                  {/* Content Section */}
                  <div style={{ padding: "2rem" }}>
                      {error && (
                          <div
                              style={{
                                  marginBottom: "2rem",
                                  backgroundColor: "#fef2f2",
                                  border: "1px solid #fecaca",
                                  color: "#dc2626",
                                  padding: "1rem",
                                  borderRadius: "0.5rem",
                              }}
                          >
                              <div
                                  style={{
                                      display: "flex",
                                      alignItems: "center",
                                  }}
                              >
                                  <svg
                                      style={{
                                          width: "1.25rem",
                                          height: "1.25rem",
                                          marginRight: "0.5rem",
                                      }}
                                      fill="currentColor"
                                      viewBox="0 0 20 20"
                                  >
                                      <path
                                          fillRule="evenodd"
                                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                          clipRule="evenodd"
                                      />
                                  </svg>
                                  {error}
                              </div>
                          </div>
                      )}

                      <form
                          onSubmit={handleSubmit}
                          style={{
                              display: "flex",
                              flexDirection: "column",
                              gap: "2rem",
                          }}
                      >
                          {/* Basic Information Card */}
                          <div
                              style={{
                                  backgroundColor: "#f9fafb",
                                  border: "1px solid #e5e7eb",
                                  borderRadius: "0.5rem",
                                  padding: "1.5rem",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "1.25rem",
                                      fontWeight: "bold",
                                      color: "#1f2937",
                                      marginBottom: "1rem",
                                      borderBottom: "1px solid #d1d5db",
                                      paddingBottom: "0.5rem",
                                  }}
                              >
                                  Basic Information
                              </h3>

                              <div
                                  style={{
                                      display: "grid",
                                      gridTemplateColumns: "2fr 1fr",
                                      gap: "3rem",
                                      alignItems: "start",
                                  }}
                              >
                                  {/* League Name */}
                                  <div>
                                      <label
                                          style={{
                                              display: "block",
                                              fontSize: "0.875rem",
                                              fontWeight: "600",
                                              color: "#374151",
                                              marginBottom: "0.5rem",
                                          }}
                                          htmlFor="name"
                                      >
                                          League Name *
                                      </label>
                                      <input
                                          type="text"
                                          id="name"
                                          name="name"
                                          value={formData.name}
                                          onChange={handleChange}
                                          required
                                          style={{
                                              width: "100%",
                                              padding: "0.75rem 1rem",
                                              border: "1px solid #d1d5db",
                                              borderRadius: "0.5rem",
                                              fontSize: "1rem",
                                              outline: "none",
                                              transition: "border-color 0.2s",
                                          }}
                                          placeholder="Enter league name"
                                          onFocus={(e) =>
                                              (e.target.style.borderColor =
                                                  "#3b82f6")
                                          }
                                          onBlur={(e) =>
                                              (e.target.style.borderColor =
                                                  "#d1d5db")
                                          }
                                      />
                                  </div>

                                  {/* Number of Teams */}
                                  <div>
                                      <label
                                          style={{
                                              display: "block",
                                              fontSize: "0.875rem",
                                              fontWeight: "600",
                                              color: "#374151",
                                              marginBottom: "0.5rem",
                                          }}
                                          htmlFor="num_teams"
                                      >
                                          Number of Teams
                                      </label>
                                      <select
                                          id="num_teams"
                                          name="num_teams"
                                          value={formData.num_teams}
                                          onChange={handleChange}
                                          style={{
                                              width: "100%",
                                              padding: "0.75rem 1rem",
                                              border: "1px solid #d1d5db",
                                              borderRadius: "0.5rem",
                                              fontSize: "1rem",
                                              outline: "none",
                                              backgroundColor: "white",
                                          }}
                                      >
                                          {Array.from(
                                              { length: 15 },
                                              (_, i) => i + 2
                                          ).map((num) => (
                                              <option key={num} value={num}>
                                                  {num} teams
                                              </option>
                                          ))}
                                      </select>
                                      <p
                                          style={{
                                              color: "#6b7280",
                                              fontSize: "0.875rem",
                                              marginTop: "0.25rem",
                                          }}
                                      >
                                          Number of users/teams that can
                                          participate in this league
                                      </p>
                                  </div>
                              </div>
                          </div>

                          {/* Roster Configuration Card */}
                          <div
                              style={{
                                  backgroundColor: "#f9fafb",
                                  border: "1px solid #e5e7eb",
                                  borderRadius: "0.5rem",
                                  padding: "1.5rem",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "1.25rem",
                                      fontWeight: "bold",
                                      color: "#1f2937",
                                      marginBottom: "1rem",
                                      borderBottom: "1px solid #d1d5db",
                                      paddingBottom: "0.5rem",
                                  }}
                              >
                                  Roster Configuration *
                              </h3>
                              <p
                                  style={{
                                      color: "#6b7280",
                                      fontSize: "0.875rem",
                                      marginBottom: "1.5rem",
                                  }}
                              >
                                  Select positions and specify how many of each
                                  position teams must draft
                              </p>

                              <div
                                  style={{
                                      backgroundColor: "white",
                                      border: "1px solid #e5e7eb",
                                      borderRadius: "0.5rem",
                                      overflow: "hidden",
                                  }}
                              >
                                  <table
                                      style={{
                                          width: "100%",
                                          borderCollapse: "collapse",
                                      }}
                                  >
                                      <thead>
                                          <tr
                                              style={{
                                                  backgroundColor: "#f8fafc",
                                              }}
                                          >
                                              <th
                                                  style={{
                                                      padding: "0.75rem 1rem",
                                                      textAlign: "left",
                                                      fontWeight: "600",
                                                      color: "#374151",
                                                      borderBottom:
                                                          "1px solid #e5e7eb",
                                                  }}
                                              >
                                                  Position
                                              </th>
                                              <th
                                                  style={{
                                                      padding: "0.75rem 1rem",
                                                      textAlign: "center",
                                                      fontWeight: "600",
                                                      color: "#374151",
                                                      borderBottom:
                                                          "1px solid #e5e7eb",
                                                      width: "120px",
                                                  }}
                                              >
                                                  Count
                                              </th>
                                          </tr>
                                      </thead>
                                      <tbody>
                                          {/* Show QB, RB, WR, TE first */}
                                          {positionOptions
                                              .filter((p) =>
                                                  [
                                                      "QB",
                                                      "RB",
                                                      "WR",
                                                      "TE",
                                                  ].includes(p.value)
                                              )
                                              .map((position) => (
                                                  <tr
                                                      key={position.value}
                                                      style={{
                                                          borderBottom:
                                                              "1px solid #f3f4f6",
                                                      }}
                                                  >
                                                      <td
                                                          style={{
                                                              padding:
                                                                  "0.75rem 1rem",
                                                          }}
                                                      >
                                                          <div
                                                              style={{
                                                                  display:
                                                                      "flex",
                                                                  alignItems:
                                                                      "center",
                                                              }}
                                                          >
                                                              <input
                                                                  type="checkbox"
                                                                  id={`position_${position.value}`}
                                                                  checked={formData.positions_included.includes(
                                                                      position.value
                                                                  )}
                                                                  onChange={() =>
                                                                      handlePositionChange(
                                                                          position.value
                                                                      )
                                                                  }
                                                                  style={{
                                                                      marginRight:
                                                                          "0.75rem",
                                                                      width: "1rem",
                                                                      height: "1rem",
                                                                  }}
                                                              />
                                                              <label
                                                                  htmlFor={`position_${position.value}`}
                                                                  style={{
                                                                      color: "#1f2937",
                                                                      fontWeight:
                                                                          "500",
                                                                      cursor: "pointer",
                                                                  }}
                                                              >
                                                                  <span
                                                                      style={{
                                                                          color: "#2563eb",
                                                                          fontWeight:
                                                                              "600",
                                                                      }}
                                                                  >
                                                                      {
                                                                          position.value
                                                                      }
                                                                  </span>
                                                                  {" - "}
                                                                  {
                                                                      position.label
                                                                  }
                                                              </label>
                                                          </div>
                                                      </td>
                                                      <td
                                                          style={{
                                                              padding:
                                                                  "0.75rem 1rem",
                                                              textAlign:
                                                                  "center",
                                                          }}
                                                      >
                                                          {formData.positions_included.includes(
                                                              position.value
                                                          ) ? (
                                                              <input
                                                                  type="number"
                                                                  min="1"
                                                                  max="5"
                                                                  value={
                                                                      formData
                                                                          .roster_config[
                                                                          position
                                                                              .value
                                                                      ] || 1
                                                                  }
                                                                  onChange={(
                                                                      e
                                                                  ) =>
                                                                      handleRosterCountChange(
                                                                          position.value,
                                                                          e
                                                                              .target
                                                                              .value
                                                                      )
                                                                  }
                                                                  style={{
                                                                      width: "4rem",
                                                                      padding:
                                                                          "0.5rem",
                                                                      border: "1px solid #d1d5db",
                                                                      borderRadius:
                                                                          "0.375rem",
                                                                      textAlign:
                                                                          "center",
                                                                      fontWeight:
                                                                          "500",
                                                                  }}
                                                              />
                                                          ) : (
                                                              <span
                                                                  style={{
                                                                      color: "#9ca3af",
                                                                      fontSize:
                                                                          "0.875rem",
                                                                  }}
                                                              >
                                                                  -
                                                              </span>
                                                          )}
                                                      </td>
                                                  </tr>
                                              ))}

                                          {/* Flex Position Row */}
                                          <tr
                                              style={{
                                                  borderBottom:
                                                      "1px solid #f3f4f6",
                                              }}
                                          >
                                              <td
                                                  style={{
                                                      padding: "0.75rem 1rem",
                                                  }}
                                              >
                                                  <div
                                                      style={{
                                                          display: "flex",
                                                          alignItems: "center",
                                                      }}
                                                  >
                                                      <input
                                                          type="checkbox"
                                                          id="flex_enabled"
                                                          checked={
                                                              formData.flex
                                                                  .enabled
                                                          }
                                                          onChange={(e) =>
                                                              handleFlexChange(
                                                                  "enabled",
                                                                  e.target
                                                                      .checked
                                                              )
                                                          }
                                                          style={{
                                                              marginRight:
                                                                  "0.75rem",
                                                              width: "1rem",
                                                              height: "1rem",
                                                          }}
                                                      />
                                                      <label
                                                          htmlFor="flex_enabled"
                                                          style={{
                                                              color: "#1f2937",
                                                              fontWeight: "500",
                                                              cursor: "pointer",
                                                          }}
                                                      >
                                                          <span
                                                              style={{
                                                                  color: "#2563eb",
                                                                  fontWeight:
                                                                      "600",
                                                              }}
                                                          >
                                                              FLEX
                                                          </span>
                                                          {" - "}
                                                          Flexible Position (
                                                          {formData.flex.eligible_positions.join(
                                                              ", "
                                                          )}
                                                          )
                                                      </label>
                                                  </div>
                                                  {formData.flex.enabled && (
                                                      <div
                                                          style={{
                                                              marginTop:
                                                                  "0.5rem",
                                                              marginLeft:
                                                                  "1.75rem",
                                                              fontSize:
                                                                  "0.75rem",
                                                              color: "#6b7280",
                                                          }}
                                                      >
                                                          Eligible:{" "}
                                                          {[
                                                              "RB",
                                                              "WR",
                                                              "TE",
                                                          ].map((pos, i) => (
                                                              <label
                                                                  key={pos}
                                                                  style={{
                                                                      marginRight:
                                                                          "1rem",
                                                                      display:
                                                                          "inline-flex",
                                                                      alignItems:
                                                                          "center",
                                                                  }}
                                                              >
                                                                  <input
                                                                      type="checkbox"
                                                                      checked={formData.flex.eligible_positions.includes(
                                                                          pos
                                                                      )}
                                                                      onChange={() =>
                                                                          handleFlexPositionToggle(
                                                                              pos
                                                                          )
                                                                      }
                                                                      style={{
                                                                          marginRight:
                                                                              "0.25rem",
                                                                          width: "0.75rem",
                                                                          height: "0.75rem",
                                                                      }}
                                                                  />
                                                                  {pos}
                                                              </label>
                                                          ))}
                                                      </div>
                                                  )}
                                              </td>
                                              <td
                                                  style={{
                                                      padding: "0.75rem 1rem",
                                                      textAlign: "center",
                                                  }}
                                              >
                                                  {formData.flex.enabled ? (
                                                      <input
                                                          type="number"
                                                          min="0"
                                                          max="3"
                                                          value={
                                                              formData.flex
                                                                  .count
                                                          }
                                                          onChange={(e) =>
                                                              handleFlexChange(
                                                                  "count",
                                                                  parseInt(
                                                                      e.target
                                                                          .value
                                                                  ) || 0
                                                              )
                                                          }
                                                          style={{
                                                              width: "4rem",
                                                              padding: "0.5rem",
                                                              border: "1px solid #d1d5db",
                                                              borderRadius:
                                                                  "0.375rem",
                                                              textAlign:
                                                                  "center",
                                                              fontWeight: "500",
                                                          }}
                                                      />
                                                  ) : (
                                                      <span
                                                          style={{
                                                              color: "#9ca3af",
                                                              fontSize:
                                                                  "0.875rem",
                                                          }}
                                                      >
                                                          -
                                                      </span>
                                                  )}
                                              </td>
                                          </tr>

                                          {/* Show DST and K last */}
                                          {positionOptions
                                              .filter((p) =>
                                                  ["DST", "K"].includes(p.value)
                                              )
                                              .map((position, index) => (
                                                  <tr
                                                      key={position.value}
                                                      style={{
                                                          borderBottom:
                                                              index < 1
                                                                  ? "1px solid #f3f4f6"
                                                                  : "none",
                                                      }}
                                                  >
                                                      <td
                                                          style={{
                                                              padding:
                                                                  "0.75rem 1rem",
                                                          }}
                                                      >
                                                          <div
                                                              style={{
                                                                  display:
                                                                      "flex",
                                                                  alignItems:
                                                                      "center",
                                                              }}
                                                          >
                                                              <input
                                                                  type="checkbox"
                                                                  id={`position_${position.value}`}
                                                                  checked={formData.positions_included.includes(
                                                                      position.value
                                                                  )}
                                                                  onChange={() =>
                                                                      handlePositionChange(
                                                                          position.value
                                                                      )
                                                                  }
                                                                  style={{
                                                                      marginRight:
                                                                          "0.75rem",
                                                                      width: "1rem",
                                                                      height: "1rem",
                                                                  }}
                                                              />
                                                              <label
                                                                  htmlFor={`position_${position.value}`}
                                                                  style={{
                                                                      color: "#1f2937",
                                                                      fontWeight:
                                                                          "500",
                                                                      cursor: "pointer",
                                                                  }}
                                                              >
                                                                  <span
                                                                      style={{
                                                                          color: "#2563eb",
                                                                          fontWeight:
                                                                              "600",
                                                                      }}
                                                                  >
                                                                      {
                                                                          position.value
                                                                      }
                                                                  </span>
                                                                  {" - "}
                                                                  {
                                                                      position.label
                                                                  }
                                                              </label>
                                                          </div>
                                                      </td>
                                                      <td
                                                          style={{
                                                              padding:
                                                                  "0.75rem 1rem",
                                                              textAlign:
                                                                  "center",
                                                          }}
                                                      >
                                                          {formData.positions_included.includes(
                                                              position.value
                                                          ) ? (
                                                              <input
                                                                  type="number"
                                                                  min="1"
                                                                  max="5"
                                                                  value={
                                                                      formData
                                                                          .roster_config[
                                                                          position
                                                                              .value
                                                                      ] || 1
                                                                  }
                                                                  onChange={(
                                                                      e
                                                                  ) =>
                                                                      handleRosterCountChange(
                                                                          position.value,
                                                                          e
                                                                              .target
                                                                              .value
                                                                      )
                                                                  }
                                                                  style={{
                                                                      width: "4rem",
                                                                      padding:
                                                                          "0.5rem",
                                                                      border: "1px solid #d1d5db",
                                                                      borderRadius:
                                                                          "0.375rem",
                                                                      textAlign:
                                                                          "center",
                                                                      fontWeight:
                                                                          "500",
                                                                  }}
                                                              />
                                                          ) : (
                                                              <span
                                                                  style={{
                                                                      color: "#9ca3af",
                                                                      fontSize:
                                                                          "0.875rem",
                                                                  }}
                                                              >
                                                                  -
                                                              </span>
                                                          )}
                                                      </td>
                                                  </tr>
                                              ))}
                                      </tbody>
                                  </table>
                              </div>
                          </div>

                          {/* Scoring Settings Card */}
                          <div
                              style={{
                                  backgroundColor: "#f0f9ff",
                                  border: "1px solid #e0f2fe",
                                  borderRadius: "0.5rem",
                                  padding: "1.5rem",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "1.25rem",
                                      fontWeight: "bold",
                                      color: "#1f2937",
                                      marginBottom: "1rem",
                                      borderBottom: "1px solid #d1d5db",
                                      paddingBottom: "0.5rem",
                                  }}
                              >
                                  Scoring Settings
                              </h3>
                              <p
                                  style={{
                                      color: "#6b7280",
                                      fontSize: "0.875rem",
                                      marginBottom: "1.5rem",
                                  }}
                              >
                                  Customize point values for each statistical
                                  category. Default values are shown.
                              </p>

                              <div
                                  style={{
                                      display: "grid",
                                      gap: "1.5rem",
                                  }}
                              >
                                  {Object.entries(scoringCategories).map(
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
                                                              alignItems:
                                                                  "center",
                                                              justifyContent:
                                                                  "space-between",
                                                              padding:
                                                                  "0.5rem 0.75rem",
                                                              backgroundColor:
                                                                  "#ffffff",
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
                                                                  fontWeight:
                                                                      "500",
                                                                  flex: 1,
                                                              }}
                                                          >
                                                              {
                                                                  stat.display_name
                                                              }
                                                          </label>
                                                          <input
                                                              type="number"
                                                              step="0.01"
                                                              value={
                                                                  formData
                                                                      .scoring_settings[
                                                                      stat
                                                                          .stat_name
                                                                  ] ||
                                                                  stat.default_value
                                                              }
                                                              onChange={(e) =>
                                                                  handleScoringChange(
                                                                      stat.stat_name,
                                                                      e.target
                                                                          .value
                                                                  )
                                                              }
                                                              style={{
                                                                  width: "80px",
                                                                  padding:
                                                                      "0.375rem 0.5rem",
                                                                  border: "1px solid #d1d5db",
                                                                  borderRadius:
                                                                      "0.25rem",
                                                                  fontSize:
                                                                      "0.875rem",
                                                                  textAlign:
                                                                      "right",
                                                                  marginLeft:
                                                                      "0.5rem",
                                                              }}
                                                          />
                                                      </div>
                                                  ))}
                                              </div>
                                          </div>
                                      )
                                  )}
                              </div>
                          </div>

                          {/* League Summary Card */}
                          <div
                              style={{
                                  backgroundColor: "#eff6ff",
                                  border: "1px solid #bfdbfe",
                                  borderRadius: "0.5rem",
                                  padding: "1.5rem",
                              }}
                          >
                              <h3
                                  style={{
                                      fontSize: "1.25rem",
                                      fontWeight: "bold",
                                      color: "#1e40af",
                                      marginBottom: "1rem",
                                      borderBottom: "2px solid #3b82f6",
                                      paddingBottom: "0.5rem",
                                  }}
                              >
                                  League Summary
                              </h3>

                              <div
                                  style={{
                                      display: "grid",
                                      gridTemplateColumns:
                                          "repeat(auto-fit, minmax(280px, 1fr))",
                                      gap: "1.5rem",
                                  }}
                              >
                                  {/* Basic Info Card */}
                                  <div
                                      style={{
                                          backgroundColor: "white",
                                          border: "1px solid #e5e7eb",
                                          borderRadius: "0.5rem",
                                          padding: "1rem",
                                      }}
                                  >
                                      <h4
                                          style={{
                                              fontSize: "1rem",
                                              fontWeight: "600",
                                              color: "#1f2937",
                                              marginBottom: "0.75rem",
                                              borderBottom: "1px solid #e5e7eb",
                                              paddingBottom: "0.5rem",
                                          }}
                                      >
                                          League Details
                                      </h4>
                                      <div
                                          style={{
                                              display: "flex",
                                              flexDirection: "column",
                                              gap: "0.5rem",
                                          }}
                                      >
                                          <div
                                              style={{
                                                  display: "flex",
                                                  justifyContent:
                                                      "space-between",
                                                  alignItems: "center",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      color: "#6b7280",
                                                      fontSize: "0.875rem",
                                                  }}
                                              >
                                                  Name:
                                              </span>
                                              <span
                                                  style={{
                                                      fontWeight: "500",
                                                      color: "#1f2937",
                                                  }}
                                              >
                                                  {formData.name || "Not set"}
                                              </span>
                                          </div>
                                          <div
                                              style={{
                                                  display: "flex",
                                                  justifyContent:
                                                      "space-between",
                                                  alignItems: "center",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      color: "#6b7280",
                                                      fontSize: "0.875rem",
                                                  }}
                                              >
                                                  Teams:
                                              </span>
                                              <span
                                                  style={{
                                                      fontWeight: "500",
                                                      color: "#1f2937",
                                                  }}
                                              >
                                                  {formData.num_teams}
                                              </span>
                                          </div>
                                          <div
                                              style={{
                                                  display: "flex",
                                                  justifyContent:
                                                      "space-between",
                                                  alignItems: "center",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      color: "#6b7280",
                                                      fontSize: "0.875rem",
                                                  }}
                                              >
                                                  Admin:
                                              </span>
                                              <span
                                                  style={{
                                                      fontWeight: "500",
                                                      color: "#1f2937",
                                                  }}
                                              >
                                                  {user?.display_name ||
                                                      user?.username}
                                              </span>
                                          </div>
                                          <div
                                              style={{
                                                  display: "flex",
                                                  justifyContent:
                                                      "space-between",
                                                  alignItems: "center",
                                                  marginTop: "0.5rem",
                                                  paddingTop: "0.5rem",
                                                  borderTop:
                                                      "1px solid #e5e7eb",
                                              }}
                                          >
                                              <span
                                                  style={{
                                                      color: "#1f2937",
                                                      fontSize: "0.875rem",
                                                      fontWeight: "600",
                                                  }}
                                              >
                                                  Total Roster Size:
                                              </span>
                                              <span
                                                  style={{
                                                      fontWeight: "700",
                                                      fontSize: "1.125rem",
                                                      color: "#059669",
                                                      backgroundColor:
                                                          "#d1fae5",
                                                      padding: "0.25rem 0.5rem",
                                                      borderRadius: "0.375rem",
                                                  }}
                                              >
                                                  {Object.values(
                                                      formData.roster_config
                                                  ).reduce(
                                                      (sum, count) =>
                                                          sum + count,
                                                      0
                                                  ) +
                                                      (formData.flex.enabled
                                                          ? formData.flex.count
                                                          : 0)}{" "}
                                                  players
                                              </span>
                                          </div>
                                      </div>
                                  </div>

                                  {/* Roster Configuration Card */}
                                  <div
                                      style={{
                                          backgroundColor: "white",
                                          border: "1px solid #e5e7eb",
                                          borderRadius: "0.5rem",
                                          padding: "1rem",
                                      }}
                                  >
                                      <h4
                                          style={{
                                              fontSize: "1rem",
                                              fontWeight: "600",
                                              color: "#1f2937",
                                              marginBottom: "0.75rem",
                                              borderBottom: "1px solid #e5e7eb",
                                              paddingBottom: "0.5rem",
                                          }}
                                      >
                                          Roster Breakdown
                                      </h4>
                                      <div
                                          style={{
                                              display: "flex",
                                              flexDirection: "column",
                                              gap: "0.375rem",
                                          }}
                                      >
                                          {/* Show positions in the correct order: QB, RB, WR, TE, FLEX, DST, K */}
                                          {["QB", "RB", "WR", "TE"].map(
                                              (position) => {
                                                  const count =
                                                      formData.roster_config[
                                                          position
                                                      ];
                                                  return count ? (
                                                      <div
                                                          key={position}
                                                          style={{
                                                              display: "flex",
                                                              justifyContent:
                                                                  "space-between",
                                                              alignItems:
                                                                  "center",
                                                              padding:
                                                                  "0.375rem 0.75rem",
                                                              backgroundColor:
                                                                  "#f8fafc",
                                                              borderRadius:
                                                                  "0.375rem",
                                                              border: "1px solid #e2e8f0",
                                                          }}
                                                      >
                                                          <span
                                                              style={{
                                                                  fontWeight:
                                                                      "600",
                                                                  color: "#2563eb",
                                                                  fontSize:
                                                                      "0.875rem",
                                                              }}
                                                          >
                                                              {position}
                                                          </span>
                                                          <span
                                                              style={{
                                                                  color: "#4b5563",
                                                                  fontSize:
                                                                      "0.875rem",
                                                              }}
                                                          >
                                                              {count}{" "}
                                                              {count === 1
                                                                  ? "player"
                                                                  : "players"}
                                                          </span>
                                                      </div>
                                                  ) : null;
                                              }
                                          )}

                                          {/* Show FLEX if enabled */}
                                          {formData.flex.enabled &&
                                              formData.flex.count > 0 && (
                                                  <div
                                                      style={{
                                                          display: "flex",
                                                          justifyContent:
                                                              "space-between",
                                                          alignItems: "center",
                                                          padding:
                                                              "0.375rem 0.75rem",
                                                          backgroundColor:
                                                              "#f8fafc",
                                                          borderRadius:
                                                              "0.375rem",
                                                          border: "1px solid #e2e8f0",
                                                      }}
                                                  >
                                                      <span
                                                          style={{
                                                              fontWeight: "600",
                                                              color: "#2563eb",
                                                              fontSize:
                                                                  "0.875rem",
                                                          }}
                                                      >
                                                          FLEX (
                                                          {formData.flex.eligible_positions.join(
                                                              ", "
                                                          )}
                                                          )
                                                      </span>
                                                      <span
                                                          style={{
                                                              color: "#4b5563",
                                                              fontSize:
                                                                  "0.875rem",
                                                          }}
                                                      >
                                                          {formData.flex.count}{" "}
                                                          {formData.flex
                                                              .count === 1
                                                              ? "player"
                                                              : "players"}
                                                      </span>
                                                  </div>
                                              )}

                                          {/* Show DST and K last */}
                                          {["DST", "K"].map((position) => {
                                              const count =
                                                  formData.roster_config[
                                                      position
                                                  ];
                                              return count ? (
                                                  <div
                                                      key={position}
                                                      style={{
                                                          display: "flex",
                                                          justifyContent:
                                                              "space-between",
                                                          alignItems: "center",
                                                          padding:
                                                              "0.375rem 0.75rem",
                                                          backgroundColor:
                                                              "#f8fafc",
                                                          borderRadius:
                                                              "0.375rem",
                                                          border: "1px solid #e2e8f0",
                                                      }}
                                                  >
                                                      <span
                                                          style={{
                                                              fontWeight: "600",
                                                              color: "#2563eb",
                                                              fontSize:
                                                                  "0.875rem",
                                                          }}
                                                      >
                                                          {position}
                                                      </span>
                                                      <span
                                                          style={{
                                                              color: "#4b5563",
                                                              fontSize:
                                                                  "0.875rem",
                                                          }}
                                                      >
                                                          {count}{" "}
                                                          {count === 1
                                                              ? "player"
                                                              : "players"}
                                                      </span>
                                                  </div>
                                              ) : null;
                                          })}
                                      </div>
                                  </div>
                              </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                              <button
                                  type="button"
                                  onClick={handleCancel}
                                  className="px-6 py-3 bg-gray-500 text-white font-semibold rounded-lg hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                              >
                                  Cancel
                              </button>
                              <button
                                  type="submit"
                                  disabled={loading}
                                  className={`px-8 py-3 font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                                      loading
                                          ? "bg-gray-400 text-gray-600 cursor-not-allowed"
                                          : "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500"
                                  }`}
                              >
                                  {loading ? (
                                      <div className="flex items-center">
                                          <svg
                                              className="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-600"
                                              xmlns="http://www.w3.org/2000/svg"
                                              fill="none"
                                              viewBox="0 0 24 24"
                                          >
                                              <circle
                                                  className="opacity-25"
                                                  cx="12"
                                                  cy="12"
                                                  r="10"
                                                  stroke="currentColor"
                                                  strokeWidth="4"
                                              ></circle>
                                              <path
                                                  className="opacity-75"
                                                  fill="currentColor"
                                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                              ></path>
                                          </svg>
                                          Creating League...
                                      </div>
                                  ) : (
                                      "Create League"
                                  )}
                              </button>
                          </div>
                      </form>
                  </div>
              </div>
          </div>
      </div>
  );
};

export default LeagueSetup;