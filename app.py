from flask import Flask, render_template, request, redirect, url_for, flash, session
import bcrypt
import os
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For development. In production, use a fixed secret key

# User data storage (temporary - will be replaced with database later)
users = {}

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('Please login first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in users and bcrypt.checkpw(password.encode('utf-8'), users[email]['password']):
            session['email'] = email
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in users:
            flash('Email already registered')
            return render_template('register.html')
            
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users[email] = {'password': hashed_password}
        
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/news')
@login_required
def news():
    keyword = request.args.get('keyword', '')
    articles = []
    if keyword:
        api_key = "38b407279a88439aab83903b193f8580"  # In production, use environment variable
        url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                news_data = response.json()
                articles = news_data['articles'][:5]
        except requests.exceptions.RequestException:
            flash('Failed to fetch news')
    return render_template('news.html', articles=articles)

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)