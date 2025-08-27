import React from 'react';
import linkedinIcon from '../assets/img/linkedin-icon.svg';
import styles from './Footer.module.css';

const LinkedInIcon = () => (
  <a
    href="https://www.linkedin.com/in/desipilla/"
    target="_blank"
    rel="noopener noreferrer"
    className={styles.iconLink}
  >
    <img
      src={linkedinIcon}
      alt="LinkedIn"
      className={styles.icon}
    />
  </a>
);

export default LinkedInIcon;
