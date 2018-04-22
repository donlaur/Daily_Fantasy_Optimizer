import os
import pandas as pd
import numpy as np
import pulp

def format_result(name):
    name = name.replace('Players_', '')
    name = name.replace('_', ' ')
    if len(name.split())==3:
        split = name.split()
        if split[1]=="de":
            return name
        elif split[2]=="II":
            return name
        elif split[2]=="III":
            return name
        elif split[2]=="IV":
            return name
        elif split[2]=="V":
            return name
        elif split[2]=="Jr.":
            return name
        elif split[2]=="Sr.":
            return name
        else:
            name = split[0] + ' ' + split[1] + '-' + split[2]
            return name
    else:
        return name

cur_dir = os.path.curdir
# read in data
proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nfl/draftkings/current.csv'))

def prep_data(proj):
    proj['dkp'] = np.random.uniform(low=0, high=10, size=len(proj))
    player_data = proj.set_index('Name')
    return player_data

def optimize(proj, player_data, max_pts, delta, exc, lock):
    plist = proj['Name'].tolist()
    tlist = list(proj['Team'].unique())
    glist = list(proj['Game'].unique())
    qb = proj[proj['Position']=="QB"]['Name'].tolist()
    rb = proj[proj['Position']=="RB"]['Name'].tolist()
    wr = proj[proj['Position']=="WR"]['Name'].tolist()
    te = proj[proj['Position']=="TE"]['Name'].tolist()
    dst = proj[proj['Position']=="DST"]['Name'].tolist()
    exclude = exc
    lock = lock
    for i in plist:
        if player_data.loc[i, 'count'] == player_data.loc[i, 'cap']:
            exclude.append(player_data.loc[i, 'exclude'])
            if i in lock:
                lock.remove(player_data.loc[i, 'lock'])

    prob = pulp.LpProblem('NFL optimization', pulp.LpMaximize)
    players = pulp.LpVariable.dicts('Players', plist, cat='Binary')
    prob += pulp.lpSum([player_data['dkp'][i] * players[i] for i in plist]), "total pts"
    prob += pulp.lpSum([player_data['Salary'][i] * players[i] for i in plist]) <= 50000, "total cost"
    prob += pulp.lpSum([players[i] for i in qb]) == 1, "total qbs"
    prob += pulp.lpSum([players[i] for i in rb]) >= 2, "total rbs"
    prob += pulp.lpSum([players[i] for i in wr]) >= 3, "total wrs"
    prob += pulp.lpSum([players[i] for i in te]) >= 1, "total tes"
    prob += pulp.lpSum([players[i] for i in dst]) == 1, "total dsts"
    prob += pulp.lpSum([players[i] for i in plist]) == 9, "total players"
    for game in glist:
        prob += pulp.lpSum([players[i] for i in plist if player_data.loc[i, 'Game'] == game]) <= 8
    for team in tlist:
        prob += pulp.lpSum([players[i] for i in plist if player_data.loc[i, 'Team'] == team]) <= 4
    prob += pulp.lpSum([players[i] for i in exclude]) ==  0, "excluded players"
    prob += pulp.lpSum([players[i] for i in lock]) == len(lock), "lock players"
    prob += pulp.lpSum([player_data['dkp'][i] * players[i] for i in plist]) <= max_pts - delta
    prob.solve()
    df = output(prob)
    for i in df['Name']:
        player_data.loc[i, 'count'] += 1
    return prob

def output(prob):
    lineup = []
    for sol in prob.variables():
        if sol.varValue == 1:
            lineup.append(format_result(sol.name))
    df = pd.DataFrame(lineup, columns=['Name'])
    df = df.merge(proj, on='Name')
    return df
