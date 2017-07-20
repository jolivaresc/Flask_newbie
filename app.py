from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, jsonify
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,BooleanField
from wtforms.validators import InputRequired, Email
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from functools import wraps
from Logger import Logger

DEBUG = True

app = Flask(__name__
			)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'secret'
app.config['MYSQL_DB'] = 'MyFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialize MYSQL
mysql = MySQL(app)

#Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    '''
    take articles from data.py
    return render_template('articles.html',articles=Articles)
    '''
    '''
    Take articles from DB
    '''
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    query = "SELECT * FROM articles ORDER BY create_date DESC;"
    result = cur.execute(query)

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    #return render_template('article.html',id=id)

    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    query = "SELECT * FROM articles WHERE id = %s;"
    result = cur.execute(query, [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

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
        query = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s);"
        cur.execute(query, (name, email, username, password))

       # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
        Logger('User ('+name+') registered successfully',app)
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
            Logger(error,app)
            return render_template('login.html', error='Invalid credentials')
        # Cursor
        cur = mysql.connection.cursor()

        # get user by username
        query = "SELECT * FROM users WHERE username = %s;"
        result = cur.execute(query,[username])

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
            Logger('Access to Dashboard denied,  No active session found',app)
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Log out','success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()

    # Get articles
    #query = "SELECT * FROM articles ORDER BY create_date DESC;"
    query_with_names ='SELECT a.name,\
                c.*\
                FROM users a,\
                     articles c\
                WHERE a.username=\
                    (SELECT DISTINCT(b.author)\
                     FROM articles b\
                     WHERE a.username=b.author\
                       AND a.username=c.author)\
                ORDER BY c.create_date DESC;'

    result = cur.execute(query_with_names)
    #print(type(articles))
    if result > 0:
        articles = cur.fetchall()
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
@app.route('/test')
def test():
    cur = mysql.connection.cursor()

    # Get articles
    query_names ='SELECT a.name,\
                c.*\
                FROM users a,\
                     articles c\
                WHERE a.username=\
                    (SELECT DISTINCT(b.author)\
                     FROM articles b\
                     WHERE a.username=b.author\
                       AND a.username=c.author);'

    result = cur.execute(query_names)
    articles = cur.fetchall()
    cur.close()
    return jsonify(articles)

class ArticleForm(Form):
    title = StringField('Title',[validators.DataRequired()])
    body = TextAreaField('Body',[validators.DataRequired()])

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        cur = mysql.connection.cursor()
        query = "INSERT INTO articles(title, body, author) VALUES(%s, %s, %s);"
        cur.execute(query,(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()
        Logger('Article "'+ title +'" was Created',app)
        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)

# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.debug = DEBUG
    app.secret_key = 'qwerty12345'
    #host,pt="192.168.10.41",port=1234
    app.run("192.168.10.39",port=1234)
