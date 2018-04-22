import os
import pandas as pd
import pulp

def format_result(name):
    name = name.replace('Players_', '')
    name = name.replace('_', ' ')
    if len(name.split())==3:
        split = name.split()
        if split[1]=="de":
            return name
        elif split[0]=="Elena":
            return name
        else:
            name = split[0] + ' ' + split[1] + '-' + split[2]
            return name
    else:
        return name

cur_dir = os.path.curdir
# read in data
proj = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/draftkings/current.csv'))

def prep_data(proj):
    player_data = proj.set_index('player')
    return player_data

def optimize(proj, player_data, max_pts, delta, exc, lock):
    plist = proj['player'].tolist()
    tlist = list(proj['Team'].unique())
    glist = list(proj['Game'].unique())
    guards = proj[proj['Position']=="G"]['player'].tolist()
    forwards = proj[proj['Position']=="F"]['player'].tolist()
    exclude = exc
    lock = lock
    for i in plist:
        if player_data.loc[i, 'count'] >= player_data.loc[i, 'cap']:
            exclude.append(player_data.loc[i, 'exclude'])

    prob = pulp.LpProblem('WNBA optimization', pulp.LpMaximize)
    players = pulp.LpVariable.dicts('Players', plist, cat='Binary')
    teams = pulp.LpVariable.dicts('Teams', tlist, cat='Binary')
    prob += pulp.lpSum([player_data['dkp'][i] * players[i] for i in plist]), "total pts"
    prob += pulp.lpSum([player_data['Salary'][i] * players[i] for i in plist]) <= 50000, "total cost"
    prob += pulp.lpSum([players[i] for i in guards]) >= 2, "total Gs"
    prob += pulp.lpSum([players[i] for i in forwards]) >= 3, "total Fs"
    prob += pulp.lpSum([teams[i] for i in tlist]) >= 3, "min teams"
    prob += pulp.lpSum([players[i] for i in plist]) == 6, "total players"
    prob += pulp.lpSum([players[i] for i in exclude]) ==  0, "excluded players"
    for game in glist:
        prob += pulp.lpSum([players[i] for i in plist if player_data.loc[i, 'Game'] == game]) <= 5
    for team in tlist:
        prob += pulp.lpSum([players[i] for i in plist if player_data.loc[i, 'Team'] == team]) <= 4
    if lock:
        prob += pulp.lpSum([players[i] for i in lock]) == len(lock), "locked players"
    prob += pulp.lpSum([player_data['dkp'][i] * players[i] for i in plist]) <= max_pts - delta
    prob.solve()
    df = output(prob)
    for i in df['player']:
        player_data.loc[i, 'count'] += 1
    return prob

def output(prob, get_ids=False):
    if get_ids==True:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['player'])
        df = df.merge(proj, on='player')
        df = df.sort_values(by='Position', ascending=False)
        return list(df['ID'])
    
    else:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['player'])
        df = df.merge(proj, on='player')
        df = df.sort_values(by='Position', ascending=False)
        return df
