import React from 'react';
import { Link } from 'react-router-dom';
import styles from './ReturnToHomePageButton.module.css'; // Import your CSS module

const ReturnToHomePageButton = () => {
    
    return (
        <div>
            <Link to="/" className={styles.btn}>
              Return to Homepage
            </Link>
        </div>
    )
};

export default ReturnToHomePageButton;