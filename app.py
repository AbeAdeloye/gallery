from flask import Flask, render_template, request, redirect, url_for, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os


app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 't3fHEQ&WUQ/!x6a'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'photogallery'

# Intialize MySQL
mysql = MySQL(app)

bootstrap = Bootstrap(app)


@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # Get list of Photo Galleries for specific User
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM gallery WHERE galleryowner = %s', (session['id'],))
        gallery = cursor.fetchall()
        return render_template('home.html', name = session['username'], gallery = gallery)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST' and 'galleryname' in request.form:
            galleryname = request.form['galleryname']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO gallery VALUES (NULL, %s, %s)', (galleryname, session['id'],))
            return redirect(url_for('home'))
        return render_template('galleryedit.html',name = session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/gallery/<id>', methods=['GET', 'POST'])
def galleryhome(id):
    if not 'loggedin' in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        f = request.files['image']
        f.save("static/"+ f.filename)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO images VALUES (NULL, %s, %s, %s)', (f.filename, id,session['id']))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM gallery WHERE galleryid = %s and galleryowner = %s', (id,session['id']))
    gallery = cursor.fetchone()

    cursor.execute('SELECT * FROM images WHERE galleryid = %s and userid = %s', (id,session['id']))
    images = cursor.fetchall()
    if gallery:
        return render_template('galleryhome.html',name = session['username'], gallery = gallery,images=images)

@app.route('/gallery/delete/<id>', methods=['GET'])
def deletegallery(id):
    if not 'loggedin' in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT count(*) as count FROM images WHERE galleryid = %s and userid = %s', (id,session['id']))
    images_count = cursor.fetchone()
    if not images_count['count']:
        cursor.execute('Delete FROM gallery WHERE galleryid = %s and galleryowner = %s', (id,session['id']))
    return redirect(url_for('home'))

@app.route('/image/delete/<idimages>')
def imagedelete(idimages):
    if not 'loggedin' in session:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM images WHERE idimages = %s and userid = %s', (idimages,session['id']))
    image = cursor.fetchone()
    if image:
        cursor.execute('Delete FROM images WHERE idimages = %s', (idimages,))
        os.remove("static/" + str (image['image']))
        return redirect(url_for('gallery')+'/'+ str(image['galleryid']))
    else:
        return redirect(url_for('home'))



@app.route('/logout')
def logout():
   # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    msg =''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()

        # If account exists in accounts table in out database
        if account:
            # Check if password is valid            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
            # Fetch one record and return result
            account = cursor.fetchone()

            # Check if account is valid
            if account:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Password is incorrect
                msg = 'Password is incorrect..'

        # create a new account
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s)', (username, password,))
            mysql.connection.commit()
            # Create session data, we can access this data in other routes
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
    return render_template('login.html',msg=msg)
