import sqlite3

conn = sqlite3.connect('data.db')
c = conn.cursor()
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT, key TEXT)')


def delete_chat(user):
    c.execute('DELETE FROM chattable WHERE username =?', [user])
    conn.commit()

def delete_qanda(user):
    c.execute('DELETE FROM qandatable WHERE username =?', [user])
    conn.commit()
def create_chattable():
    c.execute('CREATE TABLE IF NOT EXISTS chattable(rowid INTEGER PRIMARY KEY,username TEXT, message TEXT, role TEXT)')

def create_qandatable():
    c.execute('CREATE TABLE IF NOT EXISTS qandatable(rowid INTEGER PRIMARY KEY,username TEXT, message TEXT, role TEXT)')

def add_chatdata(username, message, role):
    c.execute('INSERT INTO chattable(username,message, role) VALUES (?,?, ?)', (username, message, role))
    conn.commit()

def add_qandadata(username, message, role):
    c.execute('INSERT INTO qandatable(username,message, role) VALUES (?,?, ?)', (username, message, role))
    conn.commit()

def get_chatdata(username):
    c.execute('SELECT * FROM chattable WHERE username =?', [username])
    data = c.fetchall()
    return data

def get_qandadata(username):
    c.execute('SELECT * FROM qandatable WHERE username =?', [username])
    data = c.fetchall()
    return data

def add_userdata(username, password, key):
    c.execute('INSERT INTO userstable(username,password, key) VALUES (?,?,?)', (username, password, key))
    conn.commit()


def update_key(key, user):
    c.execute('UPDATE userstable SET key =? WHERE username =?', (key, user))
    conn.commit()


def check_if_user_already_exists(username):
    c.execute('SELECT * FROM userstable WHERE username =?', [username])
    data = c.fetchall()
    return len(data) == 0


def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data
