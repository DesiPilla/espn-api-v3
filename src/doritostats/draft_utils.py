import pandas as pd
from espn_api.football import League

''' HISTORICAL DRAFT ANALYTICS '''
def get_draft_details(league: League):
    draft = pd.DataFrame()

    # Get a dictionary of the starting roster slots and number of each for the League (Week 1 must have passed already)
    primary_slots = [slot for slot in league.roster_settings['starting_roster_slots'].keys(
    ) if ('/' not in slot) or (slot == 'D/ST')]

    for i, player in enumerate(league.draft):
        draft.loc[i, 'year'] = league.year
        draft.loc[i, 'team_owner'] = player.team.owner
        draft.loc[i, 'team_id'] = player.team.team_id
        draft.loc[i, 'player_name'] = player.playerName
        draft.loc[i, 'player_id'] = player.playerId
        draft.loc[i, 'round_num'] = player.round_num
        draft.loc[i, 'round_pick'] = player.round_pick
        try:
            # Get more player details (can take 1.5 min)
            player = league.player_info(playerId=draft.loc[i, 'player_id'])
            draft.loc[i, 'pro_team'] = player.proTeam
            draft.loc[i, 'proj_points'] = player.projected_total_points
            draft.loc[i, 'total_points'] = player.total_points
            draft.loc[i, 'position'] = [
                slot for slot in player.eligibleSlots if slot in primary_slots][0]
        except AttributeError:
            print('Pick {} missing.'.format(i+1))
            draft.loc[i, 'player_name'] = ''
            draft.loc[i, 'player_id'] = ''
            draft.loc[i, 'round_num'] = 99
            draft.loc[i, 'round_pick'] = 99
        except:
            print(i, player, league.draft[i-2:i+2])
            draft.loc[i, 'position'] = player.eligibleSlots[0]

    draft['first_letter'] = draft.player_name.str[0]
    draft['points_surprise'] = draft.total_points - draft.proj_points
    draft['positive_surprise'] = draft.points_surprise > 0
    draft['pick_num'] = (draft.round_num - 1) * \
        len(draft.team_id.unique()) + draft.round_pick

    draft_pick_values = pd.read_csv('./pick_value.csv')
    draft = pd.merge(draft, draft_pick_values, left_on='pick_num',
                     right_on='pick', how='left').drop(columns=['pick'])
    return draft


def get_multiple_drafts(league: League, start_year: int = 2020, end_year: int = 2021, swid=None, espn_s2=None):
    draft = pd.DataFrame()
    for year in range(start_year, end_year+1):
        print('Fetching {} draft...'.format(year), end='')
        try:
            draft_league = League(league_id=league.league_id,
                                  year=year,
                                  swid=swid,
                                  espn_s2=espn_s2)
        except:
            continue

        draft = pd.concat([draft, get_draft_details(draft_league)])

    return draft


def get_team_max(df, col, by='team_owner', keep=None):
    '''
    `by` = 'team_id', 'team_owner'
    '''

    def get_maxs(s):
        return ' | '.join(s[s == s.max()].index.values)

    value_counts = df.groupby([by, col])\
                     .count()['player_id']\
                     .unstack()\
                     .fillna(0)

    value_counts['max_value'] = value_counts.apply(get_maxs, axis=1)
    value_counts['max_count'] = value_counts.max(axis=1)
    value_counts = value_counts.iloc[:, -2:]

    if keep is not None:
        return value_counts[value_counts.index.isin(keep)]

    else:
        return value_counts