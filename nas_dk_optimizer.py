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
        elif split[2]=="III":
            return name
        elif split[2]=="Jr.":
            return name
        else:
            name = split[0] + ' ' + split[1] + '-' + split[2]
            return name
    else:
        return name

cur_dir = os.path.curdir
# read in data
proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nas/draftkings/current.csv'))

def prep_data(proj):
    player_data = proj.set_index('Driver')
    return player_data

def optimize(proj, player_data, max_pts, delta, exc, lock):
    plist = proj['Driver'].tolist()
    exclude = exc
    lock = lock
    for i in plist:
        if player_data.loc[i, 'count'] >= player_data.loc[i, 'cap']:
            exclude.append(player_data.loc[i, 'exclude'])
    prob = pulp.LpProblem('NAS optimization', pulp.LpMaximize)
    players = pulp.LpVariable.dicts('Players', plist, cat='Binary')
    prob += pulp.lpSum([player_data['Median'][i] * players[i] for i in plist]), "total pts"
    prob += pulp.lpSum([player_data['Salary'][i] * players[i] for i in plist]) <= 50000, "total cost"
    prob += pulp.lpSum([players[i] for i in plist]) == 6, "total players"
    prob += pulp.lpSum([players[i] for i in exclude]) ==  0, "excluded players"
    prob += pulp.lpSum([players[i] for i in lock]) == len(lock), "locked players"
    prob += pulp.lpSum([player_data['Median'][i] * players[i] for i in plist]) <= max_pts - delta
    prob.solve()
    df = output(prob)
    for i in df['Driver']:
        player_data.loc[i, 'count'] += 1
    return prob

def output(prob, get_ids=False):
    if get_ids==True:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['Driver'])
        df = df.merge(proj, on='Driver')
        df = df.sort_values(by='Position', ascending=False)
        return list(df['ID'])
    
    else:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['Driver'])
        df = df.merge(proj, on='Driver')
        df = df.sort_values(by='Position', ascending=False)
        return df
