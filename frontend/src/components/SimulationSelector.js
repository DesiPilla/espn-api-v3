import React from 'react';

const SimulationSelector = ({ nSimulations, setNSimulations }) => {
  const handleChange = (event) => {
    const value = event.target.value;
    setNSimulations(value === "--" ? null : parseInt(value, 10)); // Set to null if "--" is selected
  };

  return (
    <div className="wrapper-wide">
    Playoff odds are calculated by generating {nSimulations || "--"} Monte Carlo simulations and comparing the results.
    <br />
    You can choose a different <em>n</em> by selecting one of these options:
      <select
        name="simulation-select"
        id="simulation-select"
        value={nSimulations || "--"}
        onChange={handleChange}
        style={{ marginLeft: '8px' }}
      >
        <option value="--"> -- </option>
        <option value="100">100</option>
        <option value="250">250</option>
        <option value="500">500</option>
      </select>
      <br />
        You can also edit the <em>n_simulations=</em> value in the URL. However, the more simulations that are run, the longer the page will take to load.
    </div>
  );
};

export default SimulationSelector;
