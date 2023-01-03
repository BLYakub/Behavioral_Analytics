import sqlite3
import pandas as pd
import json
import re
from ml_classifier import *
conn = sqlite3.connect('my_db.db')
c = conn.cursor()

# c.execute("CREATE TABLE IF NOT EXISTS websites([link] TEXT, [count] INTEGER PRIMARY KEY, [subject] TEXT)")
# c.execute("CREATE TABLE IF NOT EXISTS apps([name] TEXT, [count] INTEGER PRIMARY KEY)")
# c.execute("CREATE TABLE IF NOT EXISTS online([log_on] TEXT, [log_off] TEXT)")
# c.execute("DELETE FROM websites")
# print(c.fetchall())

# conn.commit()
# conn.close()

data = []
with open('website_data.json', 'r') as f:
    for i in range(100000):
        try:
            line = f.readline()
            data.append(line)
        except:
            i = i - 1
            continue

for line in data:
    try:
        topic = re.compile(r'topic":{"S":"([^"]*)')
        to = topic.search(line)

        if to[1] != 'NATION' and to[1] != 'WORLD':
            # print(to[1])

            title = re.compile(r'title":{"S":"([^"]*)')
            ti = title.search(line)
            # print(ti[1])

            link = re.compile(r'link":{"S":"([^"]*)')
            li = link.search(line)
            # print(li[1])

            # c.execute(f"INSERT INTO websites (link, title, topic) VALUES ({li[1]}, {ti[1]}, {to[1]})")
            c.execute("insert into websites (link, title, topic) values(?,?,?)",(li[1], ti[1], to[1])) 
    except:
        continue

conn.commit()
conn.close()
# file = open('website_data.json', encoding="utf8")
  
# # returns JSON object as 
# # a dictionary
# data = json.load(file)
  
# # Iterating through the json
# # list
# for i in data:
#     print(i)
  
# # Closing file
# file.close()


