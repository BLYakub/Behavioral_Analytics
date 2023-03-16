import sqlite3
import pandas as pd
import json
import re
from ml_classifier import *
from socket import *
from select import select
import pickle
from profiles import *

conn = sqlite3.connect('my_db.db')
c = conn.cursor()

all_sockets = []
conn_sock = socket(AF_INET,SOCK_STREAM)
all_sockets.append(conn_sock)
conn_sock.bind(("localhost",55000))
conn_sock.listen()
print('waiting')

user_passwords = {}
admin_sock = None


def categorize_text(data):
    data_type = data.split('*')[0]
    user_id = data.split('*')[1]
    text = data.split('*')[2]
    topic = predict_topic(text)
    print(text)
    print(topic)

    c.execute("INSERT INTO label_data (text, subject) VALUES(?,?)",(text, topic))
    conn.commit()  

    if data_type == 'new_text':
        c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}'")
        text_data = c.fetchall()
        topics = []
        for data in text_data:
            for i in range(data[2]):
                topics.append(data[1])

        is_anomaly = detect_anomaly(topics, topic)

        if is_anomaly:
            anomaly_alert = f"User: {user_id} typed a text about {topic}. Is this an irregularity?"
            buffer = get_buffer(anomaly_alert)
            admin_sock.send(buffer.encode())
            admin_sock.send(anomaly_alert.encode())

            buffer = admin_sock.recv(5).decode()
            alert_answer = admin_sock.recv(int(buffer)).decode()

            if alert_answer == "yes":
                return "anomaly"
            else:
                is_anomaly = False

        if not is_anomaly:
            c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}' AND topic = '{topic}'")
            record = c.fetchone()

            if record is None:
                c.execute("INSERT INTO texts (user_id, topic, count) VALUES(?,?,?)",(user_id, topic, 1))
            else:
                c.execute(f"UPDATE texts SET count = {record[-1] + 1} WHERE user_id = '{user_id}' AND topic = '{topic}'")
            conn.commit()  

    return topic

def process_websites(data):
    data = data.split('>')
    user_id = data[1]
    websites = data[2]
    websites = websites.split(';')
    websites = [tab.split('  ') for tab in websites]
    
    c.execute(f"SELECT * FROM websites WHERE user_id = '{user_id}'")
    web_data = c.fetchall()
    web_data = [web[2] for web in web_data]
    
    for tab in websites:
        # print(tab)
        topic = categorize_text(f"*{user_id}*{tab[1]}")
        tab.append(topic)

        is_anomaly = detect_anomaly(web_data, topic)

        if is_anomaly:
            anomaly_alert = f"User: {user_id} browsed the website {tab[1]} which is about {tab[2]}. Is this an irregularity?"
            buffer = get_buffer(anomaly_alert)
            admin_sock.send(buffer.encode())
            admin_sock.send(anomaly_alert.encode())

            buffer = admin_sock.recv(5).decode()
            alert_answer = admin_sock.recv(int(buffer)).decode()

            if alert_answer == "yes":
                return False
            else:
                is_anomaly = False

        if not is_anomaly:
            c.execute("INSERT INTO websites (user_id, link, topic, title) VALUES(?,?,?,?)",(user_id, tab[0], tab[2], tab[1]))
        
        conn.commit()

    print(websites)

    # for tab in websites:
    #     c.execute("INSERT INTO websites (user_id, link, title, topic) VALUES(?,?,?,?)",(user_id, tab[0], tab[1], tab[2])) 
    return True

def save_apps(data):
    user_id = data.split(':')[1]
    apps = data.split(':')[2]
    apps = apps.split('#')

    print(apps)

    c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}'")
    app_data = c.fetchall()
    all_apps = []
    for data in app_data:
        for i in range(data[2]):
            all_apps.append(data[1])

    for app in apps:
        is_anomaly = detect_anomaly(all_apps, app)

        if is_anomaly:
            anomaly_alert = f"User: {user_id} used the app {app}. Is this an irregularity?"
            buffer = get_buffer(anomaly_alert)
            admin_sock.send(buffer.encode())
            admin_sock.send(anomaly_alert.encode())

            buffer = admin_sock.recv(5).decode()
            alert_answer = admin_sock.recv(int(buffer)).decode()

            if alert_answer == "yes":
                return False
            else:
                is_anomaly = False

        if not is_anomaly:
            c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}' AND name = '{app}'")
            record = c.fetchone()

            if record is None:
                c.execute("INSERT INTO apps (user_id, name, count) VALUES(?,?,?)",(user_id, app, 1))
            else:
                c.execute(f"UPDATE apps SET count = {record[-1] + 1} WHERE user_id = '{user_id}' AND name = '{app}'")
    
    conn.commit()
    return True

def get_buffer(data):
    length = len(data)
    count = 0

    while length != 0:
        length = int(length/10)
        count+=1

    buffer = (5-count)*'0' + f'{len(data)}'
    return buffer

def show_user_profiles():

    for user in user_passwords.keys():
        print(user)
        c.execute(f"SELECT * FROM apps WHERE user_id = '{user}'")
        apps = c.fetchall()

        c.execute(f"SELECT * FROM websites WHERE user_id = '{user}'")
        websites = c.fetchall()

        c.execute(f"SELECT * FROM texts WHERE user_id = '{user}'")
        texts = c.fetchall()

        create_profile(apps, websites, texts)

def check_user_verification(client_socket):
    global admin_sock

    buffer = get_buffer("Login or Sign Up")
    client_socket.send(buffer.encode())
    client_socket.send("Login or Sign Up".encode())

    buffer = client_socket.recv(5).decode()
    data = client_socket.recv(int(buffer)).decode()

    if data.lower() == "login":
        buffer = get_buffer("Enter Username")
        client_socket.send(buffer.encode())
        client_socket.send("Enter Username".encode())

        buffer = client_socket.recv(5).decode()
        username = client_socket.recv(int(buffer)).decode()

        if username in user_passwords.values():
            return False
            
        buffer = get_buffer("Enter User Password")
        client_socket.send(buffer.encode())
        client_socket.send("Enter User Password".encode())

        buffer = client_socket.recv(5).decode()
        user_psw = client_socket.recv(int(buffer)).decode()

        if user_passwords[username][0] == user_psw:
            if user_passwords[username][1] == 1:
                admin_sock = client_socket

            return True
        return False
    
    elif data.lower() == "sign up":
        buffer = get_buffer("Enter Username")
        client_socket.send(buffer.encode())
        client_socket.send("Enter Username".encode())

        buffer = client_socket.recv(5).decode()
        username = client_socket.recv(int(buffer)).decode()

        if username in user_passwords:
            return False

        buffer = get_buffer("Enter User Password")
        client_socket.send(buffer.encode())
        client_socket.send("Enter User Password".encode())

        buffer = client_socket.recv(5).decode()
        user_psw = client_socket.recv(int(buffer)).decode()

        user_passwords[username] = (user_psw, 0)

        c.execute("INSERT INTO users (username, password, is_admin) VALUES(?,?)",(username, user_psw, 0))
        conn.commit()   

        return True
    return False

def get_user_info():
    c.execute(f"SELECT * FROM users")
    record = c.fetchall()

    for user in record:
        user_passwords[user[0]] = (user[1], user[2])

get_user_info()
show_user_profiles()

while True:
    read,write,error =  select(all_sockets, all_sockets,[])

    for curr_socket in read:

        # If it is a new connection then it is added to the list of sockets
        if curr_socket == conn_sock:
            client_sock,addr = conn_sock.accept()
            check_user = check_user_verification(client_sock)
            if check_user:
                all_sockets.append(client_sock)
                print("connected")
            else:
                client_sock.close()
        else:

            # Else it recieves data from a certain client
            try:
                buffer = curr_socket.recv(5).decode()
                data = curr_socket.recv(int(buffer))
            except:
                all_sockets.remove(curr_socket)
                continue

            if not data:
                all_sockets.remove(curr_socket)

            else:
                try:
                    data = pickle.loads(data)
                except:
                    data = data.decode()

                if "new_text" in data:
                    topic = categorize_text(data)
                    if topic == "anomaly":
                        curr_socket.close()
                        all_sockets.remove(curr_socket)
                
                if "new_websites" in data:
                    check = process_websites(data)
                    if not check:
                        curr_socket.close()
                        all_sockets.remove(curr_socket)

                if "new_apps" in data:
                    check = save_apps(data)
                    if not check:
                        curr_socket.close()
                        all_sockets.remove(curr_socket)

