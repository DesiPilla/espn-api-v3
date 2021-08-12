import requests

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidArgumentException


def get_credentials(user=None):
    '''
    This function identifies the SWID and ESPN_S2 for a user using Selenium.
    
    The function will identify the default Chrome profile for a user on the
    machine, and open up a browser using this account.
    
    The user will be prompted to sign in to their ESPN account if they are
    not auto-signed in by their browser.
    
    The swid and espn_s2 cookies are identified and returned.
    '''
    # Get list of users on computer
    users = os.listdir('C://Users')
    for i in ['All Users', 'Default', 'Default User', 'desktop.ini', 'Public']:
        users.remove(i)
    print("[FETCHING CREDENTIALS] All users: ", users)
    
    if user is None:
        # Select first user
        user = users[0]
        print("[FETCHING CREDENTIALS] Using user: {}".format(users[0]))
    
    # Locate and use the default Chrome profile for the user
    print("[FETCHING CREDENTIALS] Locating default Chrome profile...")
    options = webdriver.ChromeOptions() 
    options.add_argument(r'--user-data-dir=C:/Users/{}/AppData/Local/Google/Chrome/User Data'.format(user))
    options.add_argument('--profile-directory=Default')

    # Instantiate Chrome instance using Selenium and the default Chrome profile
    print("[FETCHING CREDENTIALS] Instantiating Chrome browser...")
    DRIVER_PATH = 'C://chromedriver.exe'
    try: 
        driver = webdriver.Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    except InvalidArgumentException as e:
        if "user data directory is already in use" in str(e):
            #driver.close()  # Close window
            raise Exception("Chrome is already open in another window. Please close all other Chrome windows and re-launch.")
    
    # Navigate to ESPN website for league and login
    driver.get('https://fantasy.espn.com/')

    # Check if user is logged in automatically by browser
    cookies = [cookie["name"] for cookie in driver.get_cookies()] # Get list of cookie names
    if ("SWID" not in cookies) or ("espn_s2" not in cookies):
        # Wait for user to log in maunally
        print("[FETCHING CREDENTIALS] Login to ESPN account in browser.")
        driver.find_element_by_xpath('//*[@id="global-user-trigger"]').click()
        #driver.find_element_by_xpath('//*[@id="global-viewport"]/div[3]/div/ul[1]/li[7]/a').click()
        while True:
            time.sleep(5)
            cookies = [cookie["name"] for cookie in driver.get_cookies()] # Get updated list of cookie names
            if ("SWID" in cookies) and ("espn_s2" in cookies):
                print("[FETCHING CREDENTIALS] Login detected.")
                break;            
            print("[FETCHING CREDENTIALS] Login not detected... waiting 5 seconds...")
    else:
        print("[FETCHING CREDENTIALS] Login detected.")
        pass
           
    # Identify cookies for user
    swid, espn_s2 = None, None
    cookies = driver.get_cookies()
    for cookie in cookies:
        if cookie['name'] == 'SWID':
            swid = cookie['value'][1:-1]
        if cookie['name'] == 'espn_s2':
            espn_s2 = cookie['value']
    
    #return driver
    if swid is None:
        raise Exception("[FETCHING CREDENTIALS] ERROR: SWID cookie not found.")
    if espn_s2 is None:
        raise Exception("[FETCHING CREDENTIALS] ERROR: SWID cookie not found.")    
    
    # Close the browser        
    driver.close()
    
    print("[FETCHING CREDENTIALS] ESPN Credenitals:\n[FETCHING CREDENTIALS] ---------------------")
    print("[FETCHING CREDENTIALS] swid: {}\n[FETCHING CREDENTIALS] espn_s2: {}".format(swid, espn_s2))
    return swid, espn_s2

class Authorize():
    '''
    This is the old way of authenticating a private league. 
    This class is no longer supported.
    '''    
    def __init__(self, username=None, password=None, swid=None, espn_s2=None):
        self.username = username
        self.password = password
        self.swid = swid
        self.espn_s2 = espn_s2
        
        if (self.swid is None) and (self.espn_s2 is None):
            self.swid, self.espn_s2 = self.get_credentials(league_id)
        
        self.authorize()
    
 
    def authorize(self):
        headers = {'Content-Type': 'application/json'}
        siteInfo = requests.post('https://registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/api-key?langPref=en-US', headers=headers
        )
        if siteInfo.status_code != 200 or 'api-key' not in siteInfo.headers:
            raise AuthorizationError('failed to get API key')        
        api_key = siteInfo.headers['api-key']
        headers['authorization'] = 'APIKEY ' + api_key

        payload = {'loginValue': self.username, 'password': self.password}

        siteInfo = requests.post(
            'https://ha.registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/guest/login?langPref=en-US', headers=headers, json=payload
        )
        
        if siteInfo.status_code != 200:
            raise AuthorizationError('unable to authorize')

        data = siteInfo.json()

        if data['error'] is not None:
            raise AuthorizationError('unable to obtain autorization')

        self.swid = data['data']['profile']['swid'][1:-1]
        self.espn_s2 = data['data']['s2']


    def get_league(self, league_id, year):
        return League(league_id, year, self.espn_s2, self.swid)
    
    def get_credentials(league_id, user=None):
        return get_credentials(league_id, user=user)