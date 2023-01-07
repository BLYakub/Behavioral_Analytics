import sqlite3
import pandas as pd
import json
import re
from ml_classifier import *
from socket import *
from select import select

# conn = sqlite3.connect('my_db.db')
# c = conn.cursor()
all_sockets = []
conn_sock = socket(AF_INET,SOCK_STREAM)
all_sockets.append(conn_sock)
conn_sock.bind(("localhost",55000))
conn_sock.listen()

training_data = []

def categorize_text(data):

    text = data.split(':')[1]
    topic = predict_topic(text)
    training_data.append((text, topic))

    return(topic)

def process_websites(data):

    websites = data.split(':')[1]
    websites = websites.split('#')
    websites = [tab.split(' ') for tab in websites]
    websites = [tab.append(categorize_text(tab[1])) for tab in websites]

def save_apps(data):
    apps = data.split(':')[1]
    apps = apps.split('#')

while True:
    read,write,error =  select(all_sockets, all_sockets,[])

    for curr_socket in read:

        # If it is a new connection then it is added to the list of sockets
        if curr_socket == conn_sock:
            client_sock,addr = conn_sock.accept()
            all_sockets.append(client_sock)
            print("connected")
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
                    # topic = categorize_text(data)
                    print(data.split(':')[1])
                    print(categorize_text(data))
                
                if "new_websites" in data:
                    process_websites(data)

                if "new_apps" in data:
                    save_apps(data)

