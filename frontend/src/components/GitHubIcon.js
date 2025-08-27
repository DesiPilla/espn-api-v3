import React from 'react';
import githubIcon from '../assets/img/github-icon.svg';
import styles from './Footer.module.css';

const GitHubIcon = () => (
  <a
    href="https://github.com/DesiPilla/espn-api-v3"
    target="_blank"
    rel="noopener noreferrer"
    className={styles.iconLink}
  >
    <img
      src={githubIcon}
      alt="GitHub"
      className={styles.icon}
    />
  </a>
);

export default GitHubIcon;
