import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Button.module.css';

const LeagueRecordsButton = ({ leagueYear, leagueId }) => {
    return (
        <Link
            to={`/fantasy_stats/league-records/${leagueYear}/${leagueId}`}
            className={styles.btn}
        >
            View League Records
        </Link>
    );
};

export default LeagueRecordsButton;
