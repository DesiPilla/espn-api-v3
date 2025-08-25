import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Button.module.css';

const SimulatePlayoffOddsButton = ({ leagueYear, leagueId, n_simulations = 250 }) => {
  return (
    <div>
      <Link
        to={`/fantasy_stats/simulation/${leagueYear}/${leagueId}?n_simulations=${n_simulations}`}
        className={styles.btn}
      >
        Simulate Playoff Odds
      </Link>
    </div>
  );
};

export default SimulatePlayoffOddsButton;
