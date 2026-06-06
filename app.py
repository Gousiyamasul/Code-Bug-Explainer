from flask import Flask, render_template, request, jsonify, redirect, url_for, session
# # render_template - a tool that opens the html from the templates folder and sends them to the browser
# # request - a tool that helps flask receive data sent from the browser(like buggy code user types)
# # jsonify - a tool that converts Python data into Json fromat to send back to browser
import os
# # it helps python talk to your computer's operating system (Windows in our case )
# # without Os , python cannot access files and folders on our computer
from dotenv import load_dotenv
# # it opens our .env file and loads all the secret keys into our program
import requests
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv()

app = Flask(__name__)
# # __name__ this is a special python variable that tells flask "this is the main file, start from here"
# # Flask(__)-> we are creating a Flask Application

app.secret_key = os.getenv("SECRET_KEY")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")

mysql = MySQL(app)

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Home Page
@app.route('/')
@login_required
def home():
    return render_template('index.html', username=session['username'])


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            return render_template('register.html', error="Please fill all fields!")

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match!")

        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters!")

        try:
            cursor = mysql.connection.cursor()

            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                cursor.close()
                return render_template('register.html', error="Email already exists!")

            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            existing_username = cursor.fetchone()

            if existing_username:
                cursor.close()
                return render_template('register.html', error="Username already taken!")

            hashed_password = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                (username, email, hashed_password)
            )

            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('login'))

        except Exception as e:
            print("Register Error:", e)
            return render_template('register.html', error="Something went wrong!")

    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template('login.html', error="Please fill all fields!")

        try:
            cursor = mysql.connection.cursor()

            cursor.execute(
                "SELECT id, username, password FROM users WHERE email=%s",
                (email,)
            )

            user = cursor.fetchone()
            cursor.close()

            if not user:
                return render_template('login.html', error="Email not found!")

            if not check_password_hash(user[2], password):
                return render_template('login.html', error="Wrong password!")

            session['user_id'] = user[0]
            session['username'] = user[1]

            return redirect(url_for('home'))

        except Exception as e:
            print("Login Error:", e)
            return render_template('login.html', error="Something went wrong!")

    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Explain Bug
@app.route('/explain', methods=['POST'])
@login_required
def explain():

    data = request.get_json()

    code = data.get('code')
    language = data.get('language')

    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',

        headers={
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json'
        },

        json={
            'model': 'meta-llama/llama-3.2-3b-instruct:fee',

            'max_tokens': 1000,

            'messages': [
                {
                    'role': 'user',

                    'content': [
                        {
                            'type': 'text',

                            'text': f'''
You are a coding expert helping a beginner.

Analyze this {language} code carefully and provide:

1. What the bug is
2. Which line has the bug
3. Why it is a bug
4. How to fix it
5. Corrected code
6. Another similar example

Code:
{code}
'''
                        }
                    ]
                }
            ]
        }
    )

    result = response.json()

    if 'choices' in result:
        explanation = result['choices'][0]['message']['content']
    else:
        explanation = str(result)

    cursor = mysql.connection.cursor()

    cursor.execute(
        "INSERT INTO bugs(language, code, explanation, user_id) VALUES(%s,%s,%s,%s)",
        (language, code, explanation, session['user_id'])
    )

    mysql.connection.commit()
    cursor.close()

    return jsonify({'explanation': explanation})


# History
@app.route('/history')
@login_required
def history():

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT language, code, explanation, created_at FROM bugs WHERE user_id=%s ORDER BY created_at DESC",
        (session['user_id'],)
    )

    bugs = cursor.fetchall()

    cursor.close()

    return render_template(
        'history.html',
        bugs=bugs,
        username=session['username']
    )


if __name__ == '__main__':
    app.run(debug=True)









































# from flask import Flask, render_template, request, jsonify, redirect, url_for, session
# import os
# from dotenv import load_dotenv
# import requests
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash
# from functools import wraps
# from datetime import datetime

# load_dotenv()

# app = Flask(__name__)
# app.secret_key = os.getenv("SECRET_KEY")

# if os.environ.get('RENDER'):
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bugexplainer.db'
# else:
#     db_user = os.getenv("MYSQL_USER")
#     db_password = os.getenv("MYSQL_PASSWORD")
#     db_host = os.getenv("MYSQL_HOST")
#     db_name = os.getenv("MYSQL_DB")
#     app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{db_user}:{db_password}@{db_host}/{db_name}'

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), nullable=False, unique=True)
#     email = db.Column(db.String(100), nullable=False, unique=True)
#     password = db.Column(db.String(255), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     bugs = db.relationship('Bug', backref='user', lazy=True)

# class Bug(db.Model):
#     __tablename__ = 'bugs'
#     id = db.Column(db.Integer, primary_key=True)
#     language = db.Column(db.String(50))
#     code = db.Column(db.Text)
#     explanation = db.Column(db.Text)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# @app.route('/')
# @login_required
# def home():
#     return render_template('index.html', username=session['username'])

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         email = request.form.get('email')
#         password = request.form.get('password')
#         confirm_password = request.form.get('confirm_password')
#         if not username or not email or not password or not confirm_password:
#             return render_template('register.html', error="Please fill all fields!")
#         if password != confirm_password:
#             return render_template('register.html', error="Passwords do not match!")
#         if len(password) < 6:
#             return render_template('register.html', error="Password must be at least 6 characters!")
#         try:
#             existing_user = User.query.filter_by(email=email).first()
#             if existing_user:
#                 return render_template('register.html', error="Email already exists!")
#             existing_username = User.query.filter_by(username=username).first()
#             if existing_username:
#                 return render_template('register.html', error="Username already taken!")
#             hashed_password = generate_password_hash(password)
#             new_user = User(username=username, email=email, password=hashed_password)
#             db.session.add(new_user)
#             db.session.commit()
#             return redirect(url_for('login'))
#         except Exception as e:
#             print("Register error:", e)
#             return render_template('register.html', error="Something went wrong!")
#     return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
#         if not email or not password:
#             return render_template('login.html', error="Please fill all fields!")
#         try:
#             user = User.query.filter_by(email=email).first()
#             if not user:
#                 return render_template('login.html', error="Email not found! Please register.")
#             if not check_password_hash(user.password, password):
#                 return render_template('login.html', error="Wrong password! Please try again.")
#             session['user_id'] = user.id
#             session['username'] = user.username
#             return redirect(url_for('home'))
#         except Exception as e:
#             print("Login error:", e)
#             return render_template('login.html', error="Something went wrong!")
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))

# @app.route('/explain', methods=['POST'])
# @login_required
# def explain():
#     data = request.get_json()
#     code = data.get('code')
#     language = data.get('language')
#     response = requests.post(
#         'https://openrouter.ai/api/v1/chat/completions',
#         headers={
#             'Authorization': f'Bearer {OPENROUTER_API_KEY}',
#             'Content-Type': 'application/json'
#         },
#         json={
#             'model': 'meta-llama/llama-3.2-3b-instruct:fee',
#             # 'model':'mistralai/mistral-small-3.1-24b-instruct:fee',
#             'max_tokens': 1000,
#             'messages': [
#                 {
#                     'role': 'user',
#                     'content': [
#                         {
#                             'type': 'text',
#                             'text':f'You are a coding expert helping a beginner. Analyze this {language} code carefully and provide a COMPLETE explanation including: 1) What the bug is 2) which line has thebug 3) why it is a bug 4) How to fix it with corrected code 5) and also give a additional example of same type also. Always finish your complete explanation:\n\n{code}'
#                         }
#                     ]
#                 }
#             ]
#         }
#     )
#     result = response.json()
#     if 'choices' in result:
#         explanation = result['choices'][0]['message']['content']
#     else:
#         explanation = str(result)
#     new_bug = Bug(
#         language=language,
#         code=code,
#         explanation=explanation,
#         user_id=session['user_id']
#     )
#     db.session.add(new_bug)
#     db.session.commit()
#     return jsonify({'explanation': explanation})

# @app.route('/history')
# @login_required
# def history():
#     bugs = Bug.query.filter_by(user_id=session['user_id']).order_by(Bug.created_at.desc()).all()
#     return render_template('history.html', bugs=bugs, username=session['username'])

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)