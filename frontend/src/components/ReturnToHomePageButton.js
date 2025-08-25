import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Button.module.css';

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