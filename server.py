import sqlite3
import pandas as pd
import json
import re
from ml_classifier import *
from socket import *
from select import select
import pickle
from profiles import *
from datetime import datetime
import time


# Categorizes the given text using the machine learning model prediction funciton in the ml_classifier file
# Adds the text data and predicted topics to the user data
def categorize_text(data, client_sock):
    global waiting_verify

    data_type = data.split('>')[0]
    user_id = data.split('>')[1]
    text = data.split('>')[2]
    topic = predict_topic(text)

    c.execute("INSERT INTO label_data (text, subject, verified) VALUES(?,?,?)",(text, topic, 0))
    conn.commit()  

    if data_type == 'new_text':
        c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}'")
        text_data = c.fetchall()
        topics = []
        for data in text_data:
            for i in range(data[2]):
                topics.append(data[1])

        is_anomaly = conf_detect_anomaly(topic, topics)

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        
        if is_anomaly:
            c.execute("INSERT INTO anomalies (time, user_id, ip_addr, field, anomaly, is_anomaly, handled) VALUES(?,?,?,?,?,?,?)",(current_time, user_id, user_passwords[user_id][2], 'texts', topic, 1, 0))
            conn.commit()

            with open('log_events.txt', "a+") as file_object:
                file_object.write(f"{current_time} - Anomaly - {user_id} typed an irregular subject: {topic}\n")

            waiting_verify[client_sock] = user_id
            buffer = get_buffer("Anomaly detected! Re-enter your user password:")
            client_sock.send(buffer.encode())
            client_sock.send("Anomaly detected! Re-enter your user password:".encode())

        if not is_anomaly:

            buffer = get_buffer("okay")
            client_sock.send(buffer.encode())
            client_sock.send("okay".encode())

            c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}' AND topic = '{topic}'")
            record = c.fetchone()

            if record is None:
                c.execute("INSERT INTO texts (user_id, topic, count) VALUES(?,?,?)",(user_id, topic, 1))
            else:
                c.execute(f"UPDATE texts SET count = '{record[-1] + 1}' WHERE user_id = '{user_id}' AND topic = '{topic}'")
            conn.commit()  

    return topic


# Processes the given websites to be added to the user data and categorized
def process_websites(data, client_sock):
    global waiting_verify

    data = data.split('>')
    user_id = data[1]
    websites = data[2]
    websites = websites.split(';')
    websites = [tab.split('  ') for tab in websites]
    
    c.execute(f"SELECT * FROM websites WHERE user_id = '{user_id}'")
    web_data = c.fetchall()
    web_data = [web[2] for web in web_data]

    non_anomalies = []
    anomalies = []
    
    for tab in websites:
        topic = categorize_text(f">{user_id}>{tab[1]}", client_sock)
        tab.append(topic)

        is_anomaly = conf_detect_anomaly(topic, web_data)

        if is_anomaly:
            anomalies.append(tab)

        if not is_anomaly:
            non_anomalies.append(tab)
        
    if anomalies:
        topics = []
        for tab in anomalies:
            if tab[2] not in topics:
                topics.append(tab[2])

            tab = '  '.join(tab)
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            c.execute("INSERT INTO anomalies (time, user_id, ip_addr, field, anomaly, is_anomaly, handled) VALUES(?,?,?,?,?,?,?)",(current_time, user_id, user_passwords[user_id][2], 'websites', tab, 1, 0))
            conn.commit()
            time.sleep(1)

        topics = ", ".join(topics)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
    
        with open('log_events.txt', "a+") as file_object:
            file_object.write(f"{current_time} - Anomaly - {user_id} searched the following topics: {topics}\n")

        for tab in non_anomalies:
            c.execute("INSERT INTO websites (user_id, link, topic, title) VALUES(?,?,?,?)",(user_id, tab[0], tab[2], tab[1]))
        conn.commit()
        
        waiting_verify[client_sock] = user_id
        buffer = get_buffer("Anomaly detected! Re-enter your user password:")
        client_sock.send(buffer.encode())
        client_sock.send("Anomaly detected! Re-enter your user password:".encode())
    
    else:
        buffer = get_buffer("okay")
        client_sock.send(buffer.encode())
        client_sock.send("okay".encode())

        for tab in non_anomalies:
            c.execute("INSERT INTO websites (user_id, link, topic, title) VALUES(?,?,?,?)",(user_id, tab[0], tab[2], tab[1]))
        conn.commit()


# Proccesses the given apps to be added to the user data
def save_apps(data, client_sock):
    global waiting_verify

    user_id = data.split('>')[1]
    apps = data.split('>')[2]
    apps = apps.split('#')

    c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}'")
    app_data = c.fetchall()
    all_apps = []
    for data in app_data:
        for i in range(data[2]):
            all_apps.append(data[1])

    non_anomalies = []
    anomalies = []

    for app in apps:
        is_anomaly = conf_detect_anomaly(app, all_apps)

        if is_anomaly:
            anomalies.append(app)

        if not is_anomaly:
            non_anomalies.append(app)

    if anomalies:
        for app in anomalies:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            c.execute("INSERT INTO anomalies (time, user_id, ip_addr, field, anomaly, is_anomaly, handled) VALUES(?,?,?,?,?,?,?)",(current_time, user_id, user_passwords[user_id][2], "apps", app, 1, 0))
            conn.commit()
            time.sleep(1)
        
        anomalies = ", ".join(anomalies)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
    
        with open('log_events.txt', "a+") as file_object:
            file_object.write(f"{current_time} - Anomaly - {user_id} used the following irregular apps: {anomalies}\n")
        
        waiting_verify[client_sock] = user_id
        buffer = get_buffer("Anomaly detected! Re-enter your user password:")
        client_sock.send(buffer.encode())
        client_sock.send("Anomaly detected! Re-enter your user password:".encode())

        for app in non_anomalies:
            c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}' AND name = '{app}'")
            record = c.fetchone()

            if record is None:
                c.execute("INSERT INTO apps (user_id, name, count) VALUES(?,?,?)",(user_id, app, 1))
            else:
                c.execute(f"UPDATE apps SET count = '{record[2] + 1}' WHERE user_id = '{user_id}' AND name = '{app}'")
        conn.commit()
    
    else:
        buffer = get_buffer("okay")
        client_sock.send(buffer.encode())
        client_sock.send("okay".encode())

        for app in non_anomalies:
            c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}' AND name = '{app}'")
            record = c.fetchone()

            if record is None:
                c.execute("INSERT INTO apps (user_id, name, count) VALUES(?,?,?)",(user_id, app, 1))
            else:
                c.execute(f"UPDATE apps SET count = '{record[-1] + 1}' WHERE user_id = '{user_id}' AND name = '{app}'")        
        conn.commit()


def get_buffer(data):
    suffix = str(len(data)).rjust(5,"0")
    return suffix


# Logout given user, updates the logout time of the user in the database
def logout_user(data, client_sock):

    data = data.split('>')
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    c.execute(f"UPDATE online SET log_off = '{current_time}' WHERE user_id = '{data[1]}' AND log_off IS NULL")
    conn.commit()

    connected_users[client_sock][1] = ""


# Handles user login/signup 
def check_user_verification(client_socket, data, ip_addr):
    data = data.split('>')
    username = data[2]
    user_psw = data[3]

    if data[1] == "block":
        c.execute("INSERT INTO blocked_computers (user_id, ip_addr) VALUES(?,?)",(None, ip_addr))
        conn.commit()

    elif data[1] == "Login":
        if username in user_passwords and user_passwords[username][0] == user_psw:
            buffer = get_buffer("ok")
            client_socket.send(buffer.encode())
            client_socket.send("ok".encode())

            if user_passwords[username][1] == 1:
                buffer = get_buffer(f"admin:{username}:{user_psw}")
                client_socket.send(buffer.encode())
                client_socket.send(f"admin:{username}:{user_psw}".encode())
            
            else:
                buffer = get_buffer(f"user:{username}:{user_psw}")
                client_socket.send(buffer.encode())
                client_socket.send(f"user:{username}:{user_psw}".encode())

                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")

                check = False
                if user_passwords[username][2] != ip_addr:
                    c.execute("INSERT INTO anomalies (time, user_id, ip_addr, field, anomaly, is_anomaly, handled) VALUES(?,?,?,?,?,?,?)",(current_time, username, ip_addr, "ip addr", ip_addr, 1, 0))
                    conn.commit()
                    waiting_verify[client_socket] = username
                    buffer = get_buffer("Anomaly detected! Re-enter your user password:")
                    client_socket.send(buffer.encode())
                    client_socket.send("Anomaly detected! Re-enter your user password:".encode())
                else:
                    buffer = get_buffer("okay")
                    client_socket.send(buffer.encode())
                    client_socket.send("okay".encode())
  
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                c.execute("INSERT INTO online (user_id, log_on, log_off) VALUES(?,?,?)",(username, current_time, None))
                conn.commit()   

                connected_users[client_socket][1] = username
                    
        else:
            buffer = get_buffer("Username or password incorrect!")
            client_socket.send(buffer.encode())
            client_socket.send("Username or password incorrect!".encode())

    
    elif data[1] == "Sign Up":
        if username in user_passwords:
            buffer = get_buffer("Username already taken")
            client_socket.send(buffer.encode())
            client_socket.send("Username already taken".encode())

        else:
            buffer = get_buffer("ok")
            client_socket.send(buffer.encode())
            client_socket.send("ok".encode())

            user_passwords[username] = (user_psw, 0, ip_addr)

            c.execute("INSERT INTO users (username, password, is_admin, ip_address) VALUES(?,?,?,?)",(username, user_psw, 0, ip_addr))
            conn.commit()  

            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            c.execute("INSERT INTO online (user_id, log_on, log_off) VALUES(?,?,?)",(username, current_time, None))
            conn.commit()   

            buffer = get_buffer(f"user:{username}:{user_psw}")
            client_socket.send(buffer.encode())
            client_socket.send(f"user:{username}:{user_psw}".encode())

            connected_users[client_socket][1] = username

            buffer = get_buffer("okay")
            client_socket.send(buffer.encode())
            client_socket.send("okay".encode())


# Handles user verification upon anomaly detection.
def anomaly_verification(client_sock, user_id, password):

    if user_passwords[user_id][0] == password:
        buffer = get_buffer("okay")
        client_sock.send(buffer.encode())
        client_sock.send("okay".encode())
        waiting_verify.pop(client_sock)
        return False
    
    buffer = get_buffer("intruder")
    client_sock.send(buffer.encode())
    client_sock.send("intruder".encode())

    c.execute("INSERT INTO blocked_computers (user_id, ip_addr) VALUES(?,?)",(user_id, user_passwords[user_id][2]))
    conn.commit()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    with open('log_events.txt', "a+") as file_object:
        file_object.write(f"{current_time} - Computer {user_passwords[user_id][2]} has been blocked\n")

    connected_users[client_sock][1] = ""
    logout_user(f"logoff>{user_id}", client_sock)
    waiting_verify.pop(client_sock)

    return True


# Blocks the computer in the given data if computer is connected to the server
def block_users(data):
    ip_addr = data.split(" ")[1]

    for udp_addr in udp_sockets:
        if udp_addr[0] == ip_addr:
            for key, value in connected_users.items():
                if value[0] == ip_addr and value[1] != None:
                    logout_user(f"logoff;{value[1]}", key)
                    break
            
            udp_sock.sendto("block".encode(), udp_addr)
            break

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    
    with open('log_events.txt', "a+") as file_object:
        file_object.write(f"{current_time} - Computer {ip_addr} has been blocked\n")


# Unblocks the given computer if the given computer is connected to the server
def unblock_computer(data):
    ip_addr = data.split(" ")[1]

    for udp_addr in udp_sockets:
        if udp_addr[0] == ip_addr:
            udp_sock.sendto("unblock".encode(), udp_addr)
            break

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    
    with open('log_events.txt', "a+") as file_object:
        file_object.write(f"{current_time} - Computer {ip_addr} has been unblocked\n")


# Send all currently connected users to the admin
def online_users(client_sock):
    users = []

    for value in connected_users.values():
        # if value[1] is not None:
        users.append(",".join(value))

    users = ":".join(users)

    buffer = get_buffer(users)
    client_sock.send(buffer.encode())
    client_sock.send(users.encode())


# Extract the users' information: username, password, IP address, is admin
def get_user_info():
    c.execute(f"SELECT * FROM users")
    record = c.fetchall()

    for user in record:
        user_passwords[user[0]] = [user[1], user[2], user[3]]


# Run socket connections between the server and the clients
def run_connection():

    while True:
        read,write,error =  select(all_sockets, all_sockets,[])

        for curr_socket in read:

            # If it is a new connection then it is added to the list of sockets
            if curr_socket == conn_sock:

                client_sock,addr = conn_sock.accept()
                data, address = udp_sock.recvfrom(2)
                udp_sockets.append(address)

                c.execute(f"SELECT * FROM blocked_computers WHERE ip_addr = '{addr[0]}'")
                computers = c.fetchall()

                if not computers:
                    buffer = get_buffer("okay")
                    client_sock.send(buffer.encode())
                    client_sock.send("okay".encode())
                else:
                    buffer = get_buffer("block")
                    client_sock.send(buffer.encode())
                    client_sock.send("block".encode())

                all_sockets.append(client_sock)
                connected_users[client_sock] = [addr[0], ""]

            else:

                # Else it recieves data from a certain client
                try:
                    buffer = curr_socket.recv(5).decode()
                    data = curr_socket.recv(int(buffer))
                except:
                    all_sockets.remove(curr_socket)
                    curr_socket.close()
                    connected_users.pop(curr_socket)
                    continue

                if not data:
                    all_sockets.remove(curr_socket)
                    curr_socket.close()
                    connected_users.pop(curr_socket)

                else:
                    try:
                        data = pickle.loads(data)
                    except:
                        data = data.decode()

                    if curr_socket in waiting_verify:
                        anomaly_verification(curr_socket, waiting_verify[curr_socket], data)

                    if "new_user" == data.split(">")[0]:
                        check_user_verification(curr_socket, data, curr_socket.getpeername()[0])

                    if "new_text" in data:
                        topic = categorize_text(data, curr_socket)
                    
                    if "new_websites" in data:
                        process_websites(data, curr_socket)

                    if "new_apps" in data:
                        save_apps(data, curr_socket)
                    
                    if "logoff" in data:
                        logout_user(data, curr_socket)

                    if "block" == data.split(" ")[0]:
                        block_users(data)
                    
                    if "unblock" == data.split(" ")[0]:
                        unblock_computer(data)

                    if "online_users" == data:
                        online_users(client_sock)

                    if "train_model" == data:
                        train_model()
                    
                    if "ip_change" == data.split(">")[0]:
                        data = data.split(">")
                        user_passwords[data[1]][2] = data[2]



if __name__ == '__main__': 

    conn = sqlite3.connect('my_db.db')
    c = conn.cursor()

    all_sockets = []
    conn_sock = socket(AF_INET,SOCK_STREAM)
    all_sockets.append(conn_sock)
    conn_sock.bind(("172.17.120.199",55000))
    conn_sock.listen()

    udp_sockets = []
    udp_sock = socket(AF_INET, SOCK_DGRAM)
    udp_sock.bind(('172.17.120.199', 55500))

    user_passwords = {}
    connected_users = {}
    waiting_verify = {}

    get_user_info()
    run_connection()

