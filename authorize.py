import requests

class Authorize():
    
    def __init__(self, username = None, password = None):
        self.username = username
        self.password = password
        self.swid = None
        self.espn_s2 = None  
        #self.authorize()
 
    def authorize(self):
        headers = {'Content-Type': 'application/json'}
        siteInfo = requests.post('https://registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/api-key?langPref=en-US', headers = headers)
        
        if siteInfo.status_code != 200 or 'api-key' not in siteInfo.headers:
            raise Exception('Authorization Error: failed to get API key')        
        
        print(siteInfo.status_code, siteInfo.text, siteInfo.headers)
        api_key = siteInfo.headers['api-key']
        headers['authorization'] = 'APIKEY ' + api_key

        payload = {'loginValue': self.username, 'password': self.password}

        siteInfo = requests.post(
            'https://ha.registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/guest/login?langPref=en-US', headers = headers, json = payload
        )
        
        print(siteInfo.status_code, siteInfo.text)
        if siteInfo.status_code != 200:
            raise Exception('Authorization Error: unable to authorize')

        data = siteInfo.json()

        if data['error'] is not None:
            raise Exception('Authorization Error: unable to obtain autorization')

        self.swid = data['data']['profile']['swid'][1:-1]
        self.espn_s2 = data['data']['s2']

    def get_league(self, league_id, year):
        return League(league_id, year, self.espn_s2, self.swid)
        
        
#c = Authorize('desidezdez@gmail.com', 'Italy100@')
#api_key = 'S7p7yOB/wq6QP4hWNTww4XfMNVaSDMrfyiCL/ULHduV8NIfN3o9Q6IW/Nz6690QlgCMKEdA5tjgniLW9lbu2cfK1WA=='

#headers = {'Content-Type': 'application/json'}
#siteInfo = requests.post('https://registerdisney.go.com/jgc/v6/client/ESPN-FANTASYLM-PROD/api-key?langPref=en-US', headers = headers)

#headers['authorization'] = 'APIKEY ' + api_key
payload = {'loginValue': 'desidezdez@gmail.com', 'password': 'Italy100@'}


#siteInfo = requests.post(
    #'https://ha.registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/guest/login?langPref=en-US', headers = headers, json = payload
#)

url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(2020) + "/segments/0/leagues/" + str(1086064)
payload = {'loginValue': 'desidezdez@gmail.com', 'password': 'Italy100@'}

url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(2020) + "/segments/0/leagues/" + str(293050)
login = {'loginValue': 'mattricupero@gmail.com', 'password': 'mar627'}

url = 'https://www.espn.com'
url = 'http://fantasy.espn.com'
print(url)
s = requests.Session()
r = s.get(url)
swid = s.cookies.get_dict()['SWID']
print(s.cookies.get_dict())



from selenium import webdriver

driver = webdriver.Chrome(executable_path='utils/chromedriver')
driver.get(url)