import React from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import DoritoStatsLogo from '../components/DoritoStatsLogo';
import ReturnToHomePageButton from '../components/ReturnToHomePageButton';
import styles from './UhOhTooEarlyPage.module.css';

const UhOhTooEarlyPage = () => {
  const { page, leagueYear, leagueId } = useParams();

  const renderMessage = () => {
    if (page === 'league-homepage') {
      return (
        <p>
          We're sorry, but league homepages are not accessible until Week 1 has
          begun. Please check back later for the information you're looking for.
        </p>
      );
    } else if (page === "playoff-simulations") {
        return (
            <p>
                We're sorry, but playoff simulations are not accessible until
                Week 4 has completed. Please check back later for the
                information you're looking for.
            </p>
        );
    } else {
        return <p>This page is not available yet. Please check back later.</p>;
    }
  };

  const returnToLeaguePage = () => {
    if (page !== 'league-homepage' && leagueYear && leagueId) {
      return (
              <Link
                to={`/fantasy_stats/league/${leagueYear}/${leagueId}`}
                className={styles.btn}
              >
                Return to Your League
              </Link>
      );
    }
    return null;
  };
  
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
            You're a bit early!{' '}
            <span role="img" aria-label="stopwatch">
              ⏱️
            </span>
          </h1>
          <hr />
        </div>

        <div className={styles.messageBox}>
          {renderMessage()}
          <p>Thank you for your understanding.</p>
          <div className={styles.buttons}>
            <ReturnToHomePageButton />
            {returnToLeaguePage()}
          </div>
        </div>
      </div>
    </div>
    <Footer />
    </>
  );
};

export default UhOhTooEarlyPage;
