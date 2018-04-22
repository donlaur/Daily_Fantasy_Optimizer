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
        elif split[0]=="Byeong" and split[1]=="Hun":
            name = "Byeong-Hun An"    
            return name
        elif split[0]=="Hao" and split[1]=="Tong":
            name = "Hao-Tong Li"
            return name
        elif split[0]=="Young" and split[1]=="Han":
            name = "Young-Han Song"
            return name
        elif split[0]=="Cheng" and split[1]=="Tsung":
            name = "Cheng-Tsung Pan"
            return name
        elif split[0]=="Seung" and split[1]=="Yul":
            name = "Seung-Yul Noh"
            return name
        elif split[0]=="Miguel" and split[1]=="Angel":
            name = "Miguel Angel Carballo"
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
proj = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/draftkings/current.csv'))

def prep_data(proj):
    player_data = proj.set_index('Golfer')
    return player_data

def optimize(proj, player_data, max_pts, delta, exc, lock):
    plist = proj['Golfer'].tolist()
    exclude = exc
    lock = lock
    for i in plist:
        if player_data.loc[i, 'count'] >= player_data.loc[i, 'cap']:
            exclude.append(player_data.loc[i, 'exclude'])
    prob = pulp.LpProblem('PGA optimization', pulp.LpMaximize)
    players = pulp.LpVariable.dicts('Players', plist, cat='Binary')
    prob += pulp.lpSum([player_data['Projection'][i] * players[i] for i in plist]), "total pts"
    prob += pulp.lpSum([player_data['Salary'][i] * players[i] for i in plist]) <= 50000, "total cost"
    prob += pulp.lpSum([players[i] for i in plist]) == 6, "total players"
    prob += pulp.lpSum([players[i] for i in exclude]) ==  0, "excluded players"
    prob += pulp.lpSum([players[i] for i in lock]) == len(lock), "locked players"
    prob += pulp.lpSum([player_data['Projection'][i] * players[i] for i in plist]) <= max_pts - delta
    prob.solve()
    df = output(prob)
    for i in df['Golfer']:
        player_data.loc[i, 'count'] += 1
    return prob

def output(prob, get_ids=False):
    if get_ids==True:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['Golfer'])
        df = df.merge(proj, on='Golfer')
        return list(df['ID'])
    
    else:
        lineup = []
        for sol in prob.variables():
            if sol.varValue == 1:
                lineup.append(format_result(sol.name))
        df = pd.DataFrame(lineup, columns=['Golfer'])
        df = df.merge(proj, on='Golfer')
        return df
