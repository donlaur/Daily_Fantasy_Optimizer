from datetime import datetime
from flask import Flask, session, request, url_for, redirect, render_template
from flask import flash, abort, g, jsonify, make_response
from flask_login import LoginManager, login_required
from flask_login import login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datatables import ColumnDT, DataTables
from werkzeug.security import generate_password_hash, check_password_hash
from io import StringIO
import json
import os
import nas_dk_optimizer
import nfl_dk_optimizer
import nfl_fd_optimizer
import golf_dk_optimizer
import golf_fd_optimizer
import wnba_dk_optimizer
import wnba_fd_optimizer
import pandas as pd
import numpy as np
import pulp

app = Flask(__name__)
db_path = os.path.join(os.path.curdir, './data/rotogoat.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SECRET_KEY'] = 'rotogoat_secret'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'

# User class
class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username',  db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(250))
    email = db.Column('email', db.String(50), unique=True, index=True)
    registered_on = db.Column('registered_on', db.DateTime)

    def __init__(self, username, password, email):
        self.username = username
        self.set_password(password)
        self.email = email
        self.registered_on = datetime.utcnow()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

# Player class
class Player(db.Model):

    __tablename__ = 'players'

    pid      = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.Text)
    pos      = db.Column(db.Text)
    dob      = db.Column(db.Text)
    ht       = db.Column(db.Text)
    wt       = db.Column(db.Float)
    y        = db.Column(db.Integer)
    tid      = db.Column(db.Integer)
    ta       = db.Column(db.Text)
    gamelogs = db.relationship('Gamelogs', backref='gamelogs')

# Gamelogs class
class Gamelogs(db.Model):

    __tablename__ = 'gamelogs'

    lid     = db.Column(db.Integer, primary_key=True)
    season  = db.Column(db.Text)
    pid     = db.Column(db.Float, db.ForeignKey('players.pid'))
    gid     = db.Column(db.Text)
    date    = db.Column(db.Text)
    opp     = db.Column(db.Text)
    ha      = db.Column(db.Text)
    mins    = db.Column(db.Float)
    fgm     = db.Column(db.Float)
    fga     = db.Column(db.Float)
    fg_pct  = db.Column(db.Float)
    fg3m    = db.Column(db.Float)
    fg3a    = db.Column(db.Float)
    fg3_pct = db.Column(db.Float)
    ftm     = db.Column(db.Float)
    fta     = db.Column(db.Float)
    ft_pct  = db.Column(db.Float)
    oreb    = db.Column(db.Float)
    dreb    = db.Column(db.Float)
    reb     = db.Column(db.Float)
    ast     = db.Column(db.Float)
    stl     = db.Column(db.Float)
    blk     = db.Column(db.Float)
    tov     = db.Column(db.Float)
    pf      = db.Column(db.Float)
    pts     = db.Column(db.Float)
    pm      = db.Column(db.Float)
    fdp     = db.Column(db.Float)


# after AJAX post parser
def ajax_parse(data):
    data = data.replace('id%5B%5D=', '')
    data = data.replace('&', ' ')
    data = data.split()
    for i in range(0, len(data)):
        data[i] = data[i].replace('+', ' ')
    return data

# home page route
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# register hidden route
@app.route('/register_hidden' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    user = User(request.form['username'] , request.form['password'],request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))

# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = User.query.filter_by(username=username).first()
    if registered_user is None:
        flash('Username is invalid', 'error')
        return redirect(url_for('index'))
    if not registered_user.check_password(password):
        flash('Password is invalid', 'error')
        return redirect(url_for('index'))
    login_user(registered_user, remember = remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))

# logout route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

# gamelog route
@app.route('/gamelogs', methods=['GET'])
@login_required
def gamelogs():
    return render_template('gamelogs.html')

# nas dk optimizer route
@app.route('/nas_dk_optimizer', methods=['GET'])
@login_required
def nas_dk_opt():
    return render_template('nas_dk_optimizer.html')

# nfl dk optimizer route
@app.route('/nfl_dk_optimizer', methods=['GET'])
@login_required
def nfl_dk_opt():
    return render_template('nfl_dk_optimizer.html')

# nfl fd optimizer route
@app.route('/nfl_fd_optimizer', methods=['GET'])
@login_required
def nfl_fd_opt():
    return render_template('nfl_fd_optimizer.html')

# golf dk optimizer route
@app.route('/golf_dk_optimizer', methods=['GET'])
def golf_dk_opt():
    return render_template('golf_dk_optimizer.html')

# golf fd optimizer route
@app.route('/golf_fd_optimizer', methods=['GET'])
def golf_fd_opt():
    return render_template('golf_fd_optimizer.html')

# wnba fd optimizer route
@app.route('/wnba_fd_optimizer', methods=['GET'])
@login_required
def page():
    return render_template('wnba_fd_optimizer.html')

# wnba dk optimizer route
@app.route('/wnba_dk_optimizer', methods=['GET'])
@login_required
def dkopt():
    return render_template('wnba_dk_optimizer.html')

# cfl dk optimizer route
@app.route('/cfl_dk_optimizer', methods=['GET'])
@login_required
def cflopt():
    return render_template('cfl_dk_optimizer.html')

# projections route
@app.route('/projections', methods=['GET'])
@login_required
def projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/fanduel/current.csv'),
                     usecols=['player', 'Position', 'Team', 'Opponent', 'Injury.Indicator', 'min', 'fdp_floor', 'fdp', 'fdp_ceiling', 'Salary', 'Value', 'exclude', 'lock', 'cap'])
    return df.to_json(orient='split')

# dk projections route, not sure in use.
@app.route('/DK_projections', methods=['GET'])
@login_required
def dk_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/draftkings/current.csv'),
                     usecols=['player', 'Position', 'Team', 'Opponent', 'Injury', 'min', 'dkp_floor', 'dkp', 'dkp_ceiling', 'Salary', 'Value', 'exclude', 'lock', 'cap'])
    return df.to_json(orient='split')

# cfl projections route
@app.route('/cfl_projections', methods=['GET'])
@login_required
def cfl_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/cfl/draftkings/current.csv'),
                    usecols=['Player', 'Position', 'Team', 'Safe', 'Proj', 'Upside', 'Salary'])
    return df.to_json(orient='split')

# nas draftkings projections route
@app.route('/nas_dk_projections', methods=['GET'])
@login_required
def nas_dk_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/nas/draftkings/current.csv'),
                    usecols=['Driver', 'Salary', 'Perc25', 'Median', 'Perc75', 'ProbWin', 'exclude', 'lock', 'cap'])
    return df.to_json(orient='split')

# nfl draftkings projections route
@app.route('/nfl_dk_projections', methods=['GET'])
@login_required
def nfl_dk_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/nfl/draftkings/current.csv'),
                    usecols=['Name', 'Position', 'Salary', 'Team', 'Opponent', 'Injury', 'exclude', 'lock', 'cap'])
    return df.to_json(orient='split')

# nfl fanduel projections route
@app.route('/nfl_fd_projections', methods=['GET'])
@login_required
def nfl_fd_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/nfl/fanduel/current.csv'),
                    usecols=['Name', 'Position', 'Salary', 'Team', 'Opponent', 'Injury Indicator', 'exclude', 'lock', 'cap'])
    return df.to_json(orient='split')

# golf draftkings projections route
@app.route('/golf_dk_projections', methods=['GET'])
@login_required
def golf_dk_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/draftkings/current.csv'),
                     usecols=['exclude', 'lock', 'Golfer', 'Salary', 'Projection', 'cap'])
    return df.to_json(orient='split')

@app.route('/golf_fd_projections', methods=['GET'])
@login_required
def golf_fd_projections():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/fanduel/current.csv'),
                     usecols=['exclude', 'lock', 'Golfer', 'Salary', 'Projection', 'cap'])
    return df.to_json(orient='split')

# nfl draftkings lineups route
@app.route('/nas-draftkings-lineups/', methods=['GET', 'POST'])
def optimize_nas_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nas/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    player_data = nas_dk_optimizer.prep_data(proj)
    json_list = []
    for i in range(0, n_lineups):
        prob = nas_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = nas_dk_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# nfl draftkings lineups route
@app.route('/nfl-draftkings-lineups/', methods=['GET', 'POST'])
def optimize_nfl_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nfl/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    player_data = nfl_dk_optimizer.prep_data(proj)
    json_list = []
    for i in range(0, n_lineups):
        prob = nfl_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = nfl_dk_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# nfl fanduel lineups route
@app.route('/nfl-fanduel-lineups/', methods=['GET', 'POST'])
def optimize_nfl_fd():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nfl/fanduel/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    player_data = nfl_fd_optimizer.prep_data(proj)
    json_list = []
    for i in range(0, n_lineups):
        prob = nfl_fd_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = nfl_fd_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# golf draftkings lineups route
@app.route('/golf-draftkings-lineups/', methods=['GET', 'POST'])
def optimize_golf_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    player_data = golf_dk_optimizer.prep_data(proj)
    json_list = []
    for i in range(0, n_lineups):
        prob = golf_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = golf_dk_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# golf fanduel lineups route
@app.route('/golf-fanduel-lineups/', methods=['GET', 'POST'])
def optimize_golf_fd():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/fanduel/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    json_list = []
    player_data = golf_fd_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = golf_fd_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = golf_fd_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# wnba fanduel lineups route.  picked up by the ajax
@app.route('/wnba-fanduel-lineups/', methods=['GET', 'POST'])
def optimize_wnba_fd():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/fanduel/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    json_list = []
    player_data = wnba_dk_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = wnba_fd_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = wnba_fd_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# wnnba draftkings lineups route.  picked up by the ajax
@app.route('/wnba-draftkings-lineups/', methods=['GET', 'POST'])
def optimize_wnba_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    json_list = []
    player_data = wnba_dk_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = wnba_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        df = wnba_dk_optimizer.output(prob)
        max_pts = pulp.value(prob.objective)
        json_list.append(df.to_json(orient='records'))
    return jsonify(json_list)

# nas draftkings lineup download route
@app.route('/dl_nas_dk', methods=['GET', 'POST'])
@login_required
def dl_nas_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/nas/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    idlist = []
    player_data = nas_dk_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = nas_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        idlist.append(nas_dk_optimizer.output(prob, get_ids=True))
        max_pts = pulp.value(prob.objective)
    df = pd.DataFrame(idlist, columns=['D', 'D', 'D', 'D', 'D', 'D'])
    resp = make_response(df.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

# golf draftkings lineup download route
@app.route('/dl_golf_dk', methods=['GET', 'POST'])
@login_required
def dl_golf_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    idlist = []
    player_data = golf_dk_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = golf_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        idlist.append(golf_dk_optimizer.output(prob, get_ids=True))
        max_pts = pulp.value(prob.objective)
    df = pd.DataFrame(idlist, columns=['G', 'G', 'G', 'G', 'G', 'G'])
    resp = make_response(df.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
    
# golf fanduel lineup download route
@app.route('/dl_golf_fd', methods=['GET', 'POST'])
@login_required
def dl_golf_fd():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/golf/fanduel/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    idlist = []
    player_data = golf_fd_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = golf_fd_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        idlist.append(golf_fd_optimizer.output(prob, get_ids=True))
        max_pts = pulp.value(prob.objective)
    df = pd.DataFrame(idlist, columns=['G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'])
    resp = make_response(df.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

# wnba draftkings lineup download route
@app.route('/dl_wnba_dk', methods=['GET', 'POST'])
@login_required
def dl_wnba_dk():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/draftkings/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    idlist = []
    player_data = wnba_dk_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = wnba_dk_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        idlist.append(wnba_dk_optimizer.output(prob, get_ids=True))
        max_pts = pulp.value(prob.objective)
    df = pd.DataFrame(idlist, columns=['G', 'G', 'F', 'F', 'F', 'UTIL'])
    resp = make_response(df.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

# wnba fanduel lineup download route
@app.route('/dl_wnba_fd', methods=['GET', 'POST'])
@login_required
def dl_wnba_fd():
    cur_dir = os.path.dirname(__file__)
    proj = pd.read_csv(os.path.join(cur_dir, './data/projections/wnba/fanduel/current.csv'))
    max_pts = 1000
    delta = 0.001
    n_lineups = request.form.get('n_lineups', type=int)
    exclude = request.form.get('exclude', type=str)
    exclude = ajax_parse(exclude)
    lock = request.form.get('lock', type=str)
    lock = ajax_parse(lock)
    cap = request.form.get('cap', type=str)
    cap = ajax_parse(cap)
    cap = list(map(int, cap))
    proj['cap'] = cap
    proj['cap'] = proj['cap'] * 0.01 * n_lineups
    idlist = []
    player_data = wnba_fd_optimizer.prep_data(proj)
    for i in range(0, n_lineups):
        prob = wnba_fd_optimizer.optimize(proj, player_data, max_pts, delta, exclude, lock)
        idlist.append(wnba_fd_optimizer.output(prob, get_ids=True))
        max_pts = pulp.value(prob.objective)
    df = pd.DataFrame(idlist, columns=['G', 'G', 'G', 'F', 'F', 'F', 'F'])
    resp = make_response(df.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

# data route
@app.route('/data')
@login_required
def data():
    columns = [
        ColumnDT(Player.name),
        ColumnDT(Player.pos),
        ColumnDT(Player.ta),
        ColumnDT(Gamelogs.opp),
        ColumnDT(Gamelogs.ha),
        ColumnDT(Gamelogs.date),
        ColumnDT(Gamelogs.fdp),
        ColumnDT(Gamelogs.mins),
        ColumnDT(Gamelogs.fgm),
        ColumnDT(Gamelogs.fga),
        ColumnDT(Gamelogs.fg3m),
        ColumnDT(Gamelogs.fg3a),
        ColumnDT(Gamelogs.ftm),
        ColumnDT(Gamelogs.fta),
        ColumnDT(Gamelogs.oreb),
        ColumnDT(Gamelogs.dreb),
        ColumnDT(Gamelogs.reb),
        ColumnDT(Gamelogs.ast),
        ColumnDT(Gamelogs.stl),
        ColumnDT(Gamelogs.blk),
        ColumnDT(Gamelogs.tov),
        ColumnDT(Gamelogs.pf),
        ColumnDT(Gamelogs.pts)
    ]

    query = db.session.query().select_from(Gamelogs).join(Player)

    params = request.args.to_dict()

    rowTable = DataTables(params, query, columns)

    return json.dumps(rowTable.output_result())


if __name__ == '__main__':
    app.run(debug=True)
