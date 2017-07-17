from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,BooleanField
from wtforms.validators import InputRequired, Email
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from functools import wraps
from Logger import Logger

DEBUG = True

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'secret'
app.config['MYSQL_DB'] = 'MyFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialize MYSQL
mysql = MySQL(app)


Articles = Articles()



@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html',articles=Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html',id=id)

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = EmailField('email',[validators.Length(min=6,max=50),validators.Email()])
    password = PasswordField('Password',[
                validators.DataRequired(),
                validators.EqualTo('confirm',message='Password do not match.')
            ])
    confirm = PasswordField('Confirm password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])

@app.route('/register', methods =['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method ==  'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        accept = form.accept_tos.data

        #create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

       # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))

    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        if username == 'admin':
            error = 'ERROR: Invalid credentials. Tried login with "admin" user'
            log(error)
            return render_template('login.html', error='Invalid credentials')
        # Cursor
        cur = mysql.connection.cursor()

        # get user by username
        result = cur.execute('SELECT * FROM users WHERE username = %s',[username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate,password):
                #LOGGER
                Logger('PASSWORD MATCHED',app)
                # starting session
                session['logged_in'] = True
                session['username'] = username
                flash('Log in successful','success')
                return redirect(url_for('dashboard'))

            else:
                #LOGGER
                Logger('PASSWORD NOT MATCHED',app)
                # displaying error
                error = 'Invalid password'
                return render_template('login.html',error=error)
            # close connection
            cur.close()
        else:
            #LOGGER
            Logger('NO USER',app)
            # displaying error
            error = 'Username  not found'
            return render_template('login.html',error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('Log out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.debug = DEBUG
    app.secret_key = 'qwerty12345'
    app.run()
