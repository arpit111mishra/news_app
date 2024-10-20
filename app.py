from flask import Flask, render_template, request, redirect, url_for, flash, session
import bcrypt
import os
import requests
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  

# Constants
NEWS_API_KEY = "38b407279a88439aab83903b193f8580"  # Better to use environment variable
NEWS_API_BASE_URL = "https://newsapi.org/v2/everything"

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
        try:
            # Prepare the API request parameters
            params = {
                'q': keyword,
                'apiKey': NEWS_API_KEY,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10  # Number of articles to fetch
            }
            
            # Make the API request
            response = requests.get(NEWS_API_BASE_URL, params=params)
            
            # Check if the request was successful
            if response.status_code == 200:
                news_data = response.json()
                articles = news_data.get('articles', [])
                
                # Process articles to handle missing data
                for article in articles:
                    # Ensure all required fields exist
                    article['title'] = article.get('title', 'No title available')
                    article['description'] = article.get('description', 'No description available')
                    article['url'] = article.get('url', '#')
                    article['urlToImage'] = article.get('urlToImage', None)
                    
                    # Ensure source exists
                    if not article.get('source'):
                        article['source'] = {'name': 'Unknown Source'}
                    
                    # Format the published date
                    if article.get('publishedAt'):
                        try:
                            date_obj = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                            article['publishedAt'] = date_obj.strftime('%B %d, %Y')
                        except ValueError:
                            article['publishedAt'] = 'Date unknown'
                
            else:
                print(f"API Error: Status Code {response.status_code}")
                print(f"Response: {response.text}")
                flash(f"Error fetching news: {response.json().get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            flash('Failed to fetch news. Please check your internet connection and try again.')
            
        except Exception as e:
            print(f"Unexpected Error: {e}")
            flash('An unexpected error occurred while fetching news.')
    
    return render_template('news.html', articles=articles)

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

# Template filters
@app.template_filter('datetime')
def format_datetime(value):
    if not value:
        return ""
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        return date_obj.strftime('%B %d, %Y')
    except:
        return value

if __name__ == '__main__':
    app.run(debug=True)