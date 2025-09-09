import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import DoritoStatsLogo from '../components/DoritoStatsLogo';
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import styles from './UhOhTooEarlyPage.module.css';

const NotFoundPage = () => {
  return (
    <>
      <div className={styles.layout}>
        <Header />
        <div className={styles.container}>
          <div className={styles.logoContainer}>
            <DoritoStatsLogo />
          </div>
          <div className={styles.hero}>
            <h1>
              Page Not Found{' '}
              <span role="img" aria-label="warning">
                ⚠️
              </span>
            </h1>
            <hr />
          </div>

          <div className={styles.messageBox}>
            <p>
              We're sorry, but the page you are looking for does not exist. 
              Please check the URL or return to the homepage.
            </p>
            <p>Thank you for your understanding.</p>
            <div className={styles.buttons}>
              <ReturnToHomePageButton />
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default NotFoundPage;
