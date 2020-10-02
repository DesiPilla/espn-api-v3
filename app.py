from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color
from kivy.core.window import Window

from league import League
from authorize import Authorize
from team import Team
from player import Player

import pandas as pd

# Get login credentials for leagues
login = pd.read_csv('login.csv')
year = 2020


class MainApp(App):
    
    def build(self):
        self.title = 'ESPN Fantasy Football Stats'
        '''
        screenManager = ScreenManager()
        
        Login = LoginScreen(name = 'Login Screen')
        screenManager.add_widget(Login)
        #loginScreen.add_widget(LoginDisplay)
        
        Stats = StatsScreen(name = 'Stats Screen')
        screenManager.add_widget(Stats)
        #statsScreen.add_widget(StatsDisplay)
        return LoginScreen()
        '''
        return LoginDisplay()


class LoginDisplay(GridLayout):
    
    def __init__(self, **kwargs):
        super(LoginDisplay, self).__init__(**kwargs)
        self.cols = 1
        
        self.login = GridLayout()               # Create login grid
        self.login.cols = 2                     # Login grid will have two columns (labels and text inputs)
        self.login.row_default_height = 30      # Login rows will have a size of 30 px
        self.login.row_force_default = True     # Force login rows to be 30 px
        
        # Add league id label and text box
        self.login.add_widget(Label(text = "League ID:"))
        self.leagueId = TextInput(multiline = False, write_tab = False)
        self.login.add_widget(self.leagueId)
        
        # Add username label and text box
        self.login.add_widget(Label(text = "Username (email):"))
        self.username = TextInput(multiline = False, write_tab = False)
        self.login.add_widget(self.username)
        
        # Add password label and text box
        passwordInput = Label(text = "Password:")
        self.login.add_widget(passwordInput)
        self.password = TextInput(multiline = False, write_tab = False, password = True, on_text_validate = self.fetch_league)
        self.login.add_widget(self.password)
        
        # Add pre-authenticated dropdown menu
        self.login.add_widget(Label(text = "Select a pre-authenticated league:"))        
        #dropdown = DropDown()
        #for user in login.id:  
            #btn = Button(text=user, size_hint_y=None, height=44) 
            #btn.bind(on_release = lambda btn: dropdown.select(btn.text))
            #dropdown.add_widget(btn)  
        #mainButton = Button(text="Select...")
        #mainButton.bind(on_release=dropdown.open)
        #dropdown.bind(on_select= lambda instance, x: setattr(mainButton, 'text', x))
        #dropdown.auto_dismiss = False
        #self.login.add_widget(dropdown)
        
        self.preauthenticated = TextInput(multiline=False, write_tab=False, on_text_validate = self.fetch_league)
        self.login.add_widget(self.preauthenticated)
        
        self.add_widget(self.login)             # Add login grid to the main page
        
        # Add the button to fetch the league
        fetchLeagueButton = Button(text="Fetch League")
        self.fetchLeagueButton = fetchLeagueButton
        self.add_widget(self.fetchLeagueButton)
        self.fetchLeagueButton.bind(on_release=self.fetch_league)     # When pressed, run fetch_league function
        
               
    def fetch_league(self, instance):
        # 1086064
        # TODO: What if league fetch fails
        
        if self.preauthenticated.text:
            _, username, password, league_id, swid, espn_s2 = login[login['id'] == self.preauthenticated.text].values[0]
            self.league = League(league_id, year, username, password, swid, espn_s2)    # Fetch league from input information            
        else: # self.username.text:
                print(self.username.text)
                league_id = int(self.leagueId.text)
                username = self.username.text
                password = self.password.text
                self.league = League(league_id, year, username, password)    # Fetch league from input information        
        
        self.fetchLeagueButton.text = "League Fetched!"
        
        self.remove_widget(self.login)                      # Remove the login information from the screen
        self.remove_widget(self.fetchLeagueButton)          # Remove the fetchLeagueButton
        
        # Create the league info and stats buttons widget
        self.infoAndStats = GridLayout()
        self.infoAndStats.cols = 1
        leagueName = Label(text = "League Name: " + self.league.settings['name'])
        self.infoAndStats.add_widget(leagueName)                         # Add the league name as a label to the (now) top of the screen
        self.add_widget(self.infoAndStats)
        
        self.add_stats()
        return
    
    def add_stats(self):      
        # Create the widget where the buttons for generating stats will be
        statButtons = GridLayout()
        statButtons.rows = 3
        statButtons.cols = 3
        
        # Create the printPowerRankings button
        self.printPowerRankingsButton = Button(text = "View Power Rankings")
        statButtons.add_widget(self.printPowerRankingsButton)
        self.printPowerRankingsButton.bind(on_release = self.printPowerRankings)
        
        # Create the printLuckIndex button
        self.printLuckIndexButton = Button(text = "View Luck Index")
        statButtons.add_widget(self.printLuckIndexButton)
        self.printLuckIndexButton.bind(on_release = self.printLuckIndex)
        
        # Create the printExpectedStandings button
        self.printExpectedStandingsButton = Button(text = "View Expected Standings")
        statButtons.add_widget(self.printExpectedStandingsButton)
        self.printExpectedStandingsButton.bind(on_release = self.printExpectedStandings)
        
        # Create the printWeeklyStats button
        self.printWeeklyStatsButton = Button(text = "View Weekly Awards")
        statButtons.add_widget(self.printWeeklyStatsButton)
        self.printWeeklyStatsButton.bind(on_release = self.printWeeklyStats)   
        
        # Create the printCurrentStandings button
        self.printCurrentStandingsButton = Button(text = "View Current Standnigs")
        statButtons.add_widget(self.printCurrentStandingsButton)
        self.printCurrentStandingsButton.bind(on_release = self.printCurrentStandings)           
        
        self.infoAndStats.add_widget(statButtons)
        
        # Create a location for stats to be stored later
        self.statsTable = GridLayout()
        self.add_widget(self.statsTable)
        self.statsTable.row_default_height = 20                 # Set the default height of each row to 20 px 
        self.statsTable.row_force_default = True
        return
        
    def printPowerRankings(self, instance):
        # Fetch the most recent power rankings for the league
        powerRankings = self.league.printPowerRankings(self.league.currentWeek - 1)
        
        self.statsTable.clear_widgets()                         # Clear the stats table
        self.statsTable.cols = 3                                # Add 3 columns
        self.statsTable.rows = self.league.numTeams + 1         # Create enough rows for every team plus a header  
        
        # Add headers to the power rankings table
        self.statsTable.add_widget(Label(text = "Team"))        
        self.statsTable.add_widget(Label(text = "Power Rank"))
        self.statsTable.add_widget(Label(text = "Owner"))
        
        # Add the power rankings for each team
        for i in range(self.league.numTeams):
            self.statsTable.add_widget(Label(text = powerRankings[i][0]))
            self.statsTable.add_widget(Label(text = str(round(powerRankings[i][1], 2))))
            self.statsTable.add_widget(Label(text = powerRankings[i][2]))        
        return
    
    def printLuckIndex(self, instance):
        # Fetch the most recent luck index for the league
        luckIndex = self.league.printLuckIndex(self.league.currentWeek - 1)
        
        self.statsTable.clear_widgets()                         # Clear the stats table
        self.statsTable.cols = 3                                # Add 3 columns
        self.statsTable.rows = self.league.numTeams + 1         # Create enough rows for every team plus a header  
        
        # Add headers to the luck index table
        self.statsTable.add_widget(Label(text = "Team"))
        self.statsTable.add_widget(Label(text = "Luck Index"))
        self.statsTable.add_widget(Label(text = "Owner"))
        
        # Add the luck index for each team
        for i in range(self.league.numTeams):
            self.statsTable.add_widget(Label(text = luckIndex[i][0]))
            self.statsTable.add_widget(Label(text = str(round(luckIndex[i][1], 2))))
            self.statsTable.add_widget(Label(text = luckIndex[i][2]))        
        return    
    
    def printCurrentStandings(self, instance):
        # Fetch the most recent standings for the league
        currentStandings = self.league.printCurrentStandings()
        
        self.statsTable.clear_widgets()                     # Clear the stats table
        self.statsTable.cols = 6                            # Add 6 columns
        self.statsTable.rows = self.league.numTeams + 1     # Create enough rows for every team plus a header  
        
        # Add headers to the expected standings table
        self.statsTable.add_widget(Label(text = "Team"))
        self.statsTable.add_widget(Label(text = "Wins"))
        self.statsTable.add_widget(Label(text = "Losses"))
        self.statsTable.add_widget(Label(text = "Ties"))
        self.statsTable.add_widget(Label(text = "Points Scored"))
        self.statsTable.add_widget(Label(text = "Owner"))
        
        # Add the current standings for each team
        for i in range(self.league.numTeams):
            self.statsTable.add_widget(Label(text = currentStandings[i][0]))
            self.statsTable.add_widget(Label(text = str(currentStandings[i][1])))
            self.statsTable.add_widget(Label(text = str(currentStandings[i][2])))  
            self.statsTable.add_widget(Label(text = str(currentStandings[i][3])))
            self.statsTable.add_widget(Label(text = str(round(currentStandings[i][4], 2))))
            self.statsTable.add_widget(Label(text = currentStandings[i][5]))
        return        
    
    
    def printExpectedStandings(self, instance):
        # Fetch the most recent expected standings for the league
        expectedStandings = self.league.printExpectedStandings(self.league.currentWeek - 1)
        
        self.statsTable.clear_widgets()                     # Clear the stats table
        self.statsTable.cols = 5                            # Add 5 columns
        self.statsTable.rows = self.league.numTeams + 1     # Create enough rows for every team plus a header  
        
        # Add headers to the expected standings table
        self.statsTable.add_widget(Label(text = "Team"))
        self.statsTable.add_widget(Label(text = "Wins"))
        self.statsTable.add_widget(Label(text = "Losses"))
        self.statsTable.add_widget(Label(text = "Ties"))
        self.statsTable.add_widget(Label(text = "Owner"))
        
        # Add the expected standings for each team
        for i in range(self.league.numTeams):
            self.statsTable.add_widget(Label(text = expectedStandings[i][0]))
            self.statsTable.add_widget(Label(text = str(expectedStandings[i][1])))
            self.statsTable.add_widget(Label(text = str(expectedStandings[i][2])))  
            self.statsTable.add_widget(Label(text = str(expectedStandings[i][3])))
            self.statsTable.add_widget(Label(text = expectedStandings[i][4]))
        return        

    def printWeeklyStats(self, instance):
        # Fetch the most recent weekly stats for the league
        weeklyStats = self.league.printWeeklyStats(self.league.currentWeek - 1)
        
        self.statsTable.clear_widgets()                     # Clear the stats table
        self.statsTable.cols = 5                            # Add 5 columns
        self.statsTable.rows = 20                           # Create enough rows for every team plus a header  
        self.statsTable.do_scroll_y = True
              
        # Add the weekly stats for each team
        self.statsTable.add_widget(Label(text = weeklyStats[0][0]))  
        self.statsTable.add_widget(Label(text = str(weeklyStats[0][1])))
        self.statsTable.add_widget(Label(text = "|")) 
        self.statsTable.add_widget(Label(text = weeklyStats[1][0]))  
        self.statsTable.add_widget(Label(text = str(weeklyStats[1][1])))
        self.statsTable.add_widget(Label(text = weeklyStats[2][0]))  
        self.statsTable.add_widget(Label(text = str(weeklyStats[2][1])))  
        self.statsTable.add_widget(Label(text = "|")) 
        self.statsTable.add_widget(Label(text = "----------------"))
        self.statsTable.add_widget(Label(text = "----------------"))
        
        for i in [3, 5]:
            self.statsTable.add_widget(Label(text = weeklyStats[i][0]))  
            self.statsTable.add_widget(Label(text = str(weeklyStats[i][1])))
            self.statsTable.add_widget(Label(text = "|")) 
            self.statsTable.add_widget(Label(text = weeklyStats[i + 1][0]))  
            self.statsTable.add_widget(Label(text = str(weeklyStats[i + 1][1])))            
        
        for i in range(8, 16):
            self.statsTable.add_widget(Label(text = weeklyStats[i][0]))
            self.statsTable.add_widget(Label(text = str(weeklyStats[i][1])))
            self.statsTable.add_widget(Label(text = "|"))  
            self.statsTable.add_widget(Label(text = weeklyStats[i + 9][0])) 
            self.statsTable.add_widget(Label(text = str(weeklyStats[i + 9][1])))          
        return        

app = MainApp()
app.run()