import React from 'react';
import styles from './Footer.module.css'; // Assuming you're using a CSS module

const Footer = () => (
  <footer className={styles.footer}>
    <div className={styles.container}>
      <div className={styles.footerContent}>
        <div className={styles.footerText}>
          <p>For suggestions or feature requests, please connect with us on GitHub or LinkedIn.</p>
        </div>
        <div className={styles.footerIcons}>
          <a
            href="https://github.com/DesiPilla/espn-api-v3"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.iconLink}
          >
            <img
              src={`/img/github-icon.svg`}
              alt="GitHub"
              className={styles.icon}
            />
          </a>
          <a
            href="https://www.linkedin.com/in/desipilla/"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.iconLink}
          >
            <img
              src={`/img/linkedin-icon.svg`}
              alt="LinkedIn"
              className={styles.icon}
            />
          </a>
        </div>
        <a
          href="https://www.buymeacoffee.com/desipilla"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.buyMeACoffee}
        >
          <img
            src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png"
            alt="Buy Me A Coffee"
            className={styles.buyMeACoffeeImage}
          />
        </a>
      </div>
    </div>
  </footer>
);

export default Footer;
