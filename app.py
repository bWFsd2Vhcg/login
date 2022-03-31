from dotenv import load_dotenv
from flask import Flask, g, redirect, render_template, request, session, url_for
from functools import wraps
from json import loads
from os import environ

load_dotenv()
USERS = loads(environ['USERS'])

app = Flask(__name__)
app.config['SECRET_KEY'] = environ['SECRET_KEY']


@app.before_request
def auth_middleware():
    g.user = session.get('user')


def login_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        if not g.user:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return func


@app.route('/')
@login_required
def index():
    return render_template('index.html', name=g.user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        next_page = request.args.get('next', url_for('index'))
        return render_template('login.html', next_page=next_page, form={})
    if request.method == 'POST':
        next_page = request.form.get('next', url_for('index'))
        if request.form.get('username') in USERS:
            if request.form.get('password') == USERS[request.form['username']]:
                session['user'] = request.form['username']
                return redirect(next_page)
        return render_template('login.html', next_page=next_page, error=True, form=request.form)


@app.route('/logout', methods=['POST'])
def logout():
    session['user'] = None
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
