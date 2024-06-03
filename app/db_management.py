import mysql.connector
import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# database and user have to be created first of all
db_name = os.getenv('db_name')
user_db = os.getenv('user')
pw_db = db_password = os.getenv('root_pw')
host = os.getenv('host')


conn = mysql.connector.connect(host=host, user=user_db, password=pw_db, port = 3306, ssl_disabled = True)
c = conn.cursor(buffered=True)
#c.execute('DROP DATABASE data;')
c.execute('CREATE DATABASE IF NOT EXISTS %s CHARACTER SET utf8 COLLATE utf8_bin;' % db_name)
conn = mysql.connector.connect(host=host, user=user_db, password=pw_db, database=db_name, port = 3306, ssl_disabled = True)
c = conn.cursor(buffered=True)


# create tables
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(user VARCHAR(100) PRIMARY KEY,password TEXT, apikey VARCHAR(100));')



def create_chattable():
    c.execute(
        'CREATE TABLE IF NOT EXISTS chattable(rowid INTEGER auto_increment PRIMARY KEY,user VARCHAR(100), message TEXT, role VARCHAR(100), FOREIGN KEY (user) REFERENCES userstable(user));')


def create_qandatable():
    c.execute(
        'CREATE TABLE IF NOT EXISTS qandatable(rowid INTEGER auto_increment PRIMARY KEY,user VARCHAR(100), message TEXT, role VARCHAR(100), FOREIGN KEY (user) REFERENCES userstable(user));')

def create_knowledgebases_private():
    c.execute(
        'CREATE TABLE IF NOT EXISTS knowledgebases_private(rowid INTEGER auto_increment PRIMARY KEY,user VARCHAR(100), knowledgebase VARCHAR(100), FOREIGN KEY (user) REFERENCES userstable(user));')

def create_knowledgebases_public():
    c.execute(
        'CREATE TABLE IF NOT EXISTS knowledgebases_public(rowid INTEGER auto_increment PRIMARY KEY, knowledgebase VARCHAR(100), protected boolean);')
    #add protected database
    if check_if_public_knowledgebase_already_exists("repo4euD21openaccess"):
        add_public_knowledgebase("index_repo4euD21openaccess", True)


def delete_chat(user):
    c.execute('DELETE FROM chattable WHERE user = %s;', [user])
    conn.commit()



def delete_qanda(user):
    c.execute('DELETE FROM qandatable WHERE user = %s;', [user])
    conn.commit()

def delete_private_knowledgebase(user, knowledgebase):
    c.execute('DELETE FROM knowledgebases_private WHERE user = %s AND knowledgebase = %s;', (user, knowledgebase))
    conn.commit()

def delete_public_knowledgebase(knowledgebase):
    c.execute('DELETE FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase])
    conn.commit()
def add_chatdata(username, message, role):
    c.execute('INSERT INTO chattable(user,message, role) VALUES (%s, %s, %s);', (username, message, role))
    conn.commit()


def add_qandadata(username, message, role):
    c.execute('INSERT INTO qandatable(user,message, role) VALUES (%s, %s, %s);', (username, message, role))
    conn.commit()


def add_userdata(username, password, key):
    c.execute('INSERT INTO userstable(user,password, apikey) VALUES (%s, %s, %s);', (username, password, key))
    conn.commit()

def add_private_knowledgebase(username, knowledgebase):
    c.execute('INSERT INTO knowledgebases_private(user,knowledgebase) VALUES (%s, %s);', (username, knowledgebase))
    conn.commit()

def get_private_knowledgebase(username):
    c.execute('SELECT * FROM knowledgebases_private WHERE user = %s;', [username])
    data = c.fetchall()
    return data

def add_public_knowledgebase(knowledgebase, protected):
    c.execute('INSERT INTO knowledgebases_public(knowledgebase, protected) VALUES (%s, %s);', (knowledgebase, protected))
    conn.commit()

def get_public_knowledgebase():
    c.execute('SELECT * FROM knowledgebases_public')
    data = c.fetchall()
    return data

def get_chatdata(username):
    c.execute('SELECT * FROM chattable WHERE user = %s;', [username])
    data = c.fetchall()
    return data



def get_qandadata(username):
    c.execute('SELECT * FROM qandatable WHERE user = %s;', [username])
    data = c.fetchall()
    return data


def get_user_data(username):
    c.execute('SELECT * FROM userstable WHERE user = %s;', [username])
    data = c.fetchall()
    return data


def update_key(key, user):
    c.execute('UPDATE userstable SET apikey = %s WHERE user = %s;', (key, user))
    conn.commit()


def check_if_user_already_exists(username):
    c.execute('SELECT * FROM userstable WHERE user = %s;', [username])
    data = c.fetchall()
    return len(data) == 0


def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE user = %s AND password = %s ;', (username, password))
    data = c.fetchall()
    return data

def check_if_public_knowledgebase_already_exists(knowledgebase):
    c.execute('SELECT * FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase])
    data = c.fetchall()
    return len(data) == 0

def check_if_public_knowledgebase_protected(knowledgebase):
    c.execute('SELECT * FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase])
    data = c.fetchall()
    if len(data) == 0:
        #private database -> is not protected
        print("not protected")
        return False
    return data[0][2]