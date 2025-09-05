import React from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import DoritoStatsLogo from '../components/DoritoStatsLogo';
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import styles from "./UhOhTooEarlyPage.module.css";

const InvalidLeaguePage = () => {
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
              League Not Found{' '}
              <span role="img" aria-label="warning">
                ⚠️
              </span>
            </h1>
            <hr />
          </div>

          <div className={styles.messageBox}>
            <p>
              We're sorry, but the league you are trying to access does not exist or is invalid. 
              Please verify the league information and try again.
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

export default InvalidLeaguePage;
