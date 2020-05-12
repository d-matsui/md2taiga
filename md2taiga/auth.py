import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from md2taiga.db import get_db

bp = Blueprint('auth', __name__)


@bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hostname = request.form['hostname']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not hostname:
            error = 'Hostname is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ? AND hostname = ?', (username, hostname)
        ).fetchone() is not None:
            error = f'User {username} on {hostname} is already registerd.'
            # TODO: add validation by using taiga auth api

        if error is None:
            db.execute(
                'INSERT INTO user (username, password, hostname) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), hostname,)
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hostname = request.form['hostname']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ? AND hostname = ?', (username, hostname,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username and/or hostname.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('editing.create'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
