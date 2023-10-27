import mysql.connector

# database and user have to be created first of all
db_name = "data"
user_db = "root"
pw_db = "xxxxxxxx"
host = "drugrepochatdb"
#host = "localhost"

conn = mysql.connector.connect(host=host, user=user_db, password=pw_db, port = 3306, ssl_disabled = True)
c = conn.cursor(buffered=True)
c.execute("CREATE DATABASE IF NOT EXISTS %s;", [db_name])
conn = mysql.connector.connect(host=host, user=user_db, password=pw_db, database=db_name, port = 3306, ssl_disabled = True)
c = conn.cursor(buffered=True)


# create tables
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(user VARCHAR(100) PRIMARY KEY,password TEXT, apikey TEXT);')



def create_chattable():
    c.execute(
        'CREATE TABLE IF NOT EXISTS chattable(rowid INTEGER auto_increment PRIMARY KEY,user TEXT, message TEXT, role TEXT);')

    c.execute("ALTER TABLE chattable CONVERT TO CHARACTER SET utf8;")


def create_qandatable():
    c.execute(
        'CREATE TABLE IF NOT EXISTS qandatable(rowid INTEGER auto_increment PRIMARY KEY,user TEXT, message TEXT, role TEXT);')


def delete_chat(user):
    c.execute('DELETE FROM chattable WHERE user = %s;', [user])
    conn.commit()



def delete_qanda(user):
    c.execute('DELETE FROM qandatable WHERE user = %s;', [user])
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
