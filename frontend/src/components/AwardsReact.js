import React from 'react';
import {allAwardsData} from './Awards';



function MakeRow(awardRow){
  return (
    <tr>
      <td>{awardRow.description}</td>
      <td>{awardRow.value}</td>
      <td>{awardRow.owner}</td>
    </tr>
  )
}

function AwardsTable() {
  return (
    <table>
      <thead>
        <tr>
          <th>Description</th>
          <th>Value</th>
          <th>Owner</th>
        </tr>
      </thead>
      <tbody>
        {allAwardsData["bestMatchAwards"].map(MakeRow)}
        {allAwardsData["worstMatchAwards"].map(MakeRow)}
        {allAwardsData["bestSeasonAwards"].map(MakeRow)}
        {allAwardsData["worstSeasonAwards"].map(MakeRow)}
      </tbody>
    </table>
  )
}

function Tabs() {
  return (
    <div class="tab">
      <button id="bestMatchBtn" class="tablinks">Best - single game</button>
      <button id="worstMatchBtn" class="tablinks">Worst - single game </button>
      <button id="bestSeasonBtn" class="tablinks">Best - season</button>
      <button id="worstSeasonBtn" class="tablinks">Worst - season</button>
    </div>
  )
}

export default function AwardsPage() {
  return (
    <div>
      <h1>Awards</h1>
      <Tabs />
      <AwardsTable />
    </div>
  );
}