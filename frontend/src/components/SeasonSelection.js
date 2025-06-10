import React from 'react';

const SeasonSelection = () => (
  <div>
    <h2>Select your league</h2>
    <div>
      <label>
        Search for leagues in the
        <label>
          <input type="radio" name="current-or-previous-season" value="select-from-current-year" defaultChecked />
          Current season
        </label>
        <label>
          <input type="radio" name="current-or-previous-season" value="select-from-previous-year" />
          Previous season
        </label>
      </label>
    </div>
  </div>
);

export default SeasonSelection;
