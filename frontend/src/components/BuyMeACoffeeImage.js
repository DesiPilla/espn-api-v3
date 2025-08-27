import React from 'react';
import styles from './Footer.module.css';

const BuyMeACoffeeImage = () => (
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
);

export default BuyMeACoffeeImage;
