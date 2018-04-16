# coding: utf-8
from www import app
from .db import database, User
from peewee import fn
from flask import session, url_for, redirect, request, render_template, flash, g
from flask_oauthlib.client import OAuth
import config
import random
import yaml
import os
import codecs
import datetime

oauth = OAuth()
openstreetmap = oauth.remote_app(
    'OpenStreetMap',
    base_url='https://api.openstreetmap.org/api/0.6/',
    request_token_url='https://www.openstreetmap.org/oauth/request_token',
    access_token_url='https://www.openstreetmap.org/oauth/access_token',
    authorize_url='https://www.openstreetmap.org/oauth/authorize',
    consumer_key=app.config['OAUTH_KEY'] or '123',
    consumer_secret=app.config['OAUTH_SECRET'] or '123'
)


@app.before_request
def before_request():
    database.connect()
    load_quest()


@app.teardown_request
def teardown(exception):
    if not database.is_closed():
        database.close()


def choose_path():
    # Select max step for each path, order by steps
    query = (User
             .select(User.path, User.step)
             .group_by(User.path)
             .having(User.step == fn.MAX(User.step))
             .tuples())
    paths = {p: 0 for p in range(len(g.quest['paths']))}
    paths.update({t[0]: t[1] for t in query})
    smin = min(paths.values())
    pmin = [p for p in paths if paths[p] == smin]
    path = random.choice(pmin)
    return path


def get_user():
    if 'osm_uid' in session:
        try:
            return User.get(User.uid == session['osm_uid'])
        except User.DoesNotExist:
            # Logging user out
            if 'osm_token' in session:
                del session['osm_token']
            if 'osm_uid' in session:
                del session['osm_uid']
    return None


def is_admin(user):
    if not user:
        return False
    if user.uid in config.ADMINS:
        return True
    return False


def load_quest():
    with codecs.open(os.path.join(config.BASE_DIR, 'quest.yml'), 'r', 'utf-8') as f:
        g.quest = yaml.load(f)


@app.route('/')
def front():
    user = get_user()
    if config.OVER:
        return render_template('over.html', participated=user and user.step >= 2)

    pquery = User.select(User.path).where(User.step == len(g.quest['steps'])+1).tuples()
    puzzle = {
        'rows': 3,
        'columns': 4,
        'pieces': set([q[0] for q in pquery]),
    }
    if user:
        if user.step == len(g.quest['steps'])+1:
            return render_template('done.html', piece=user.path, puzzle=puzzle,
                                   admin=is_admin(user))
        task = g.quest['paths'][user.path][user.step-1]
        img = None if len(task) <= 1 else task[1]
        desc = None if len(task) <= 2 else task[2]
        return render_template('task.html', step=user.step, admin=is_admin(user),
                               task=g.quest['steps'][user.step-1], image=img, desc=desc,
                               path=user.path,
                               total_steps=len(g.quest['steps']), puzzle=puzzle)
    return render_template('index.html', puzzle=puzzle, admin=is_admin(user))


@app.route('/submit', methods=['POST'])
def submit():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    code = request.form['code']
    if code.isdigit() and int(code) == g.quest['paths'][user.path][user.step-1][0]:
        user.step += 1
        user.updated = datetime.datetime.now()
        user.save()
    else:
        flash(u'Не угадали, извините.')
    return redirect(url_for('front'))


@app.route('/robots.txt')
def robots():
    return app.response_class('User-agent: *\nDisallow: /', mimetype='text/plain')


@app.route('/login')
def login():
    if 'osm_token' not in session:
        session['objects'] = request.args.get('objects')
        if request.args.get('next'):
            session['next'] = request.args.get('next')
        return openstreetmap.authorize(callback=url_for('oauth'))
    return redirect(url_for('front'))


@app.route('/oauth')
def oauth():
    resp = openstreetmap.authorized_response()
    if resp is None:
        return 'Denied. <a href="' + url_for('login') + '">Try again</a>.'
    session['osm_token'] = (
            resp['oauth_token'],
            resp['oauth_token_secret']
    )
    user_details = openstreetmap.get('user/details').data
    uid = int(user_details[0].get('id'))
    name = user_details[0].get('display_name')
    session['osm_uid'] = uid
    try:
        User.get(User.uid == uid)
    except User.DoesNotExist:
        User.create(uid=uid, name=name, path=choose_path(), step=1)

    if session.get('next'):
        redir = session['next']
        del session['next']
    else:
        redir = url_for('front')
    return redirect(redir)


@openstreetmap.tokengetter
def get_token(token='user'):
    if token == 'user' and 'osm_token' in session:
        return session['osm_token']
    return None


@app.route('/logout')
def logout():
    if 'osm_token' in session:
        del session['osm_token']
    if 'osm_uid' in session:
        del session['osm_uid']
    return redirect(url_for('front'))
