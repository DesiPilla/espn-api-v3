import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Button.module.css';

const ReturnToLeaguePageButton = ({ leagueYear, leagueId }) => {
    return (
        <Link
            to={`/fantasy_stats/league/${leagueYear}/${leagueId}`}
            className={styles.btn}
        >
            Return to Your League
        </Link>
    );
};

export default ReturnToLeaguePageButton;
