import React from 'react';
import styles from './Footer.module.css';
import GitHubIcon from './GitHubIcon';
import LinkedInIcon from './LinkedInIcon';
import BuyMeACoffeeImage from './BuyMeACoffeeImage';

const Footer = () => (
  <footer className={styles.footer}>
    <div className={styles.container}>
      <div className={styles.footerContent}>
        <div className={styles.footerText}>
          <p>For suggestions or feature requests, please connect with us on GitHub or LinkedIn.</p>
        </div>
        <div className={styles.footerIcons}>
          <GitHubIcon />
          <LinkedInIcon />
        </div>
        <BuyMeACoffeeImage />
      </div>
    </div>
  </footer>
);

export default Footer;
