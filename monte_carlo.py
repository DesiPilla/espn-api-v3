#number of random season's to simulate
simulations = 1000000 
#weeks in the regular season
league_weeks = 13 
#number of teams to playoffs
teams_to_play_off = 4 


#team_names:: list of team names. list order is used to 
#index home_teams and away_teams

#home_teams, away_teams: list of remaining matchups in the regular season.
#Indexes are based on order from team_names

#current_wins: Integer value represents each team's win count.
#The decimal is used to further order teams based on points for eg 644.8 points would be 0.006448.
#Order needs to be the same as team_names

team_names = ['Kingsland Tough Bruddas','Schroedingers Cats','The Killer Brees','Deez Nuts 4 Prez','Oakeridge Overlords','College Hillbilly','Norwood Knuckles','West City Possums','Crazy Monkeys','Mount Thunderbolts','Southeast Bulls','Te Puke Thunder']
home_teams = [3,4,6,8,9,10,1,2,5,7,11,12,3,4,6,8,9,10,3,4,6,8,9,10,1,2,5,7,11,12]
away_teams = [5,12,1,11,2,7,8,10,9,6,4,3,11,1,2,7,12,5,1,7,5,2,11,12,9,4,8,3,10,6]
current_wins = [3.007153,6.008344,5.007673,2.006870,3.006512,4.007109,6.007020,4.007222,3.007082,4.007003,4.007539,4.007405]

###ONLY CONFIGURE THE VALUES ABOVE


teams = [int(x) for x in range(1,len(team_names)+1)]
weeks_played = (league_weeks)-((len(home_teams))/(len(teams)/2))


last_playoff_wins = [0] * (league_weeks)
first_playoff_miss = [0] * (league_weeks)

import datetime

begin = datetime.datetime.now()
import random


league_size = len(teams)


games_per_week = int(league_size/2)
weeks_to_play = int(league_weeks-weeks_played)
total_games = int(league_weeks * games_per_week)
games_left = int(weeks_to_play * games_per_week)

stats_teams = [0] * (league_size)


play_off_matrix = [[0 for x in range(teams_to_play_off)] for x in range(league_size)] 

pad = int(games_left)

avg_wins = [0.0] * teams_to_play_off


for sims in range(1,simulations+1):
    #create random binary array representing a single season's results
    val = [int(random.getrandbits(1)) for x in range(1,(games_left+1))]

    empty_teams = [0.0] * league_size
        
    i = 0
    #assign wins based on 1 or 0 to home or away team
    for x in val:
        if (val[i] == 1):
            empty_teams[home_teams[i]-1] = empty_teams[home_teams[i]-1]+1
        else:
            empty_teams[away_teams[i]-1] = empty_teams[away_teams[i]-1]+1
        i=i+1

    #add the current wins to the rest of season's results
    empty_teams = [sum(x) for x in zip(empty_teams,current_wins)]
    
    #sort the teams    
    sorted_teams = sorted(empty_teams)
    
    
    
    last_playoff_wins[int(round(sorted_teams[(league_size-teams_to_play_off)],0))-1] = last_playoff_wins[int(round(sorted_teams[(league_size-teams_to_play_off)],0))-1] + 1
    first_playoff_miss[int(round(sorted_teams[league_size-(teams_to_play_off+1)],0))-1] = first_playoff_miss[int(round(sorted_teams[league_size-(teams_to_play_off+1)],0))-1] + 1
    
    
    
    #pick the teams making the playoffs
    for x in range(1,teams_to_play_off+1):        
        stats_teams[empty_teams.index(sorted_teams[league_size-x])] = stats_teams[empty_teams.index(sorted_teams[league_size-x])] + 1
        avg_wins[x-1] = avg_wins[x-1] + round(sorted_teams[league_size-x],0)
        play_off_matrix[empty_teams.index(sorted_teams[league_size-x])][x-1] = play_off_matrix[empty_teams.index(sorted_teams[league_size-x])][x-1] + 1
    

for x in range(1,len(stats_teams)+1):
    vals = ''
    for y in range(1,teams_to_play_off+1):
        vals = vals +'\t'+str(round((play_off_matrix[x-1][y-1])/simulations*100.0,2))        
    print(team_names[x-1]+'\t'+str(round((stats_teams[x-1])/simulations*100.0,2))+vals)
    
print('')

print('Average # of wins for playoff spot')
for x in range(1,teams_to_play_off+1):
    print(str(x)+'\t'+str(round((avg_wins[x-1])/simulations,2)))


delta = datetime.datetime.now() - begin

print('')
print('Histrogram of wins required for final playoff spot')
for x in range(1,len(last_playoff_wins)+1):
    print(str(x)+'\t'+str(round((last_playoff_wins[x-1])/(simulations*1.0)*100,3))+'\t'+str(round((first_playoff_miss[x-1])/(simulations*1.0)*100,3)))


print('{0:,}'.format(simulations) +" Simulations ran in "+str(delta))


    
    
    