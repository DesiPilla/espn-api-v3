export const initGoogleAnalytics = () => {
  if (
      window.location.hostname != "localhost" &&
      window.location.hostname != "127.0.0.1"
  ) {
      const script1 = document.createElement("script");
      script1.async = true;
      script1.src = "https://www.googletagmanager.com/gtag/js?id=G-45P4BQ6XJR";
      document.head.appendChild(script1);

      const script2 = document.createElement("script");
      script2.innerHTML = `
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-45P4BQ6XJR');
  `;
      document.head.appendChild(script2);
  }

  
}
