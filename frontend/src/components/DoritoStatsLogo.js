import React from 'react';
import doritoStatsLogo from '../assets/img/logo2.png';
import styles from './styles/logo.css';

const DoritoStatsLogo = () => (
  <img
    src={doritoStatsLogo}
    alt="Dorito Stats Logo"
    className={styles.logo}
  />
);

export default DoritoStatsLogo;
