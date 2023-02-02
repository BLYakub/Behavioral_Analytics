import sqlite3
import pandas as pd
import json
import re
from ml_classifier import *
from socket import *
from select import select
import pickle

conn = sqlite3.connect('my_db.db')
c = conn.cursor()

all_sockets = []
conn_sock = socket(AF_INET,SOCK_STREAM)
all_sockets.append(conn_sock)
conn_sock.bind(("localhost",55000))
conn_sock.listen()
print('waiting')

user_passwords = {}


def categorize_text(data):
    data_type = data.split('*')[0]
    user_id = data.split('*')[1]
    text = data.split('*')[2]
    topic = predict_topic(text)
    print(text)
    print(topic)

    c.execute("INSERT INTO label_data (text, subject) VALUES(?,?)",(text, topic))

    if data_type == 'new_text':
        c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}' AND topic = '{topic}'")
        record = c.fetchone()

        if record is None:
            c.execute("INSERT INTO texts (user_id, topic, count) VALUES(?,?,?)",(user_id, topic, 1))
        else:
            c.execute(f"UPDATE texts SET count = {record[-1] + 1} WHERE user_id = '{user_id}' AND topic = '{topic}'")

    conn.commit()  
    return(topic)

def process_websites(data):
    data = data.split('>')
    user_id = data[1]
    websites = data[2]
    websites = websites.split(';')
    websites = [tab.split('  ') for tab in websites]
    
    for tab in websites:
        # print(tab)
        topic = categorize_text(f"*{user_id}*{tab[1]}")
        tab.append(topic)

    print(websites)

    for tab in websites:
        c.execute("INSERT INTO websites (user_id, link, title, topic) VALUES(?,?,?,?)",(user_id, tab[0], tab[1], tab[2])) 

    conn.commit()

def save_apps(data):
    user_id = data.split(':')[1]
    apps = data.split(':')[2]
    apps = apps.split('#')

    print(apps)
    for app in apps:
        c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}' AND name = '{app}'")
        record = c.fetchone()

        if record is None:
            c.execute("INSERT INTO apps (user_id, name, count) VALUES(?,?,?)",(user_id, app, 1))
        else:
            c.execute(f"UPDATE apps SET count = {record[-1] + 1} WHERE user_id = '{user_id}' AND name = '{app}'")
    
    conn.commit()


def get_buffer(data):
    length = len(data)
    count = 0

    while length != 0:
        length = int(length/10)
        count+=1

    buffer = (5-count)*'0' + f'{len(data)}'
    return buffer

def check_user_verification(client_socket):
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

        if user_passwords[username] == user_psw:
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

        user_passwords[username] = user_psw

        with open("user_psw.txt", "a") as file:
            file.write(f"\n{username}:{user_psw}")

        return True
    return False

def get_user_info():
    with open("user_psw.txt") as file:
        for line in file:
            line = line.strip()
            line = line.split(':')
            user_passwords[line[0]] = line[1]

get_user_info()

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
                    # categorize_text(data)
                
                if "new_websites" in data:
                    process_websites(data)

                if "new_apps" in data:
                    save_apps(data)

