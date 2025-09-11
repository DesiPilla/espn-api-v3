import React from "react";

const CookiesInstructionsBox = () => {
  return (
    <div>
      <h3><em>Don't know your SWID or espn_s2? (instructions for Mac / PC)</em></h3>
      <ol>
        <li>Log into your espn fantasy football account at <a href='https://www.espn.com/fantasy/football/'>https://www.espn.com/fantasy/football/</a>.</li>
        <li>Right click anywhere on the screen (Chrome browser only) and click <em>Inspect</em>.</li>
        <li>In the window that appears on the right, click <em>Application</em> on the top bar (you may have to click the dropdown arrow next to <em>Elements, Console, Sources...</em>).</li>
        <li>On the left, navigate to <em>Storage &gt; Cookies &gt; http://fantasy.espn.com</em>.</li>
        <li>Scroll down in the table to the right until you find <strong>SWID</strong>. Copy & paste the alphanumeric string in the <em>Value</em> column (without the curly brackets).<br />It should look something like: <em>43B70875-0C4B-428L-B608-759A4BB28FA1</em></li>
        <li>Next, keep scrolling until you find <strong>espn_s2</strong>. Again, copy and paste the alphanumeric string in the <em>Value</em> column. This code will be much longer and won't have curly brackets in it.</li>
      </ol>
    </div>
  );
};

export default CookiesInstructionsBox;
