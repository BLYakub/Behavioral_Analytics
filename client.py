import win32com.client
import subprocess
from browser_history.browsers import Chrome
import time
from googletrans import Translator
import cloudscraper
from bs4 import BeautifulSoup
import requests
from ml_classifier import *

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

    print(apps)

def get_tabs():
    c = Chrome()
    outputs = c.fetch_history()

    # his is a list of (datetime.datetime, url) tuples
    his = outputs.histories
    # print(his[-1][-1])
    return his

def get_website_content(url):
    
    scraper = cloudscraper.create_scraper() 
    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    
    try:
        r = scraper.get(url, headers = headers)
    
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('title').text
        description = soup.find('meta', attrs={'name': 'description'})
    
        if "content" in str(description):
            description = description.get("content")
        else:
            description = ""
    
    
        h1 = soup.find_all('h1')
        h1_all = ""
        for x in range (len(h1)):
            if x ==  len(h1) -1:
                h1_all = h1_all + h1[x].text
            else:
                h1_all = h1_all + h1[x].text + ". "
    
    
        paragraphs_all = ""
        paragraphs = soup.find_all('p')
        for x in range (len(paragraphs)):
            if x ==  len(paragraphs) -1:
                paragraphs_all = paragraphs_all + paragraphs[x].text
            else:
                paragraphs_all = paragraphs_all + paragraphs[x].text + ". "
    
    
    
        h2 = soup.find_all('h2')
        h2_all = ""
        for x in range (len(h2)):
            if x ==  len(h2) -1:
                h2_all = h2_all + h2[x].text
            else:
                h2_all = h2_all + h2[x].text + ". "
    
    
    
        h3 = soup.find_all('h3')
        h3_all = ""
        for x in range (len(h3)):
            if x ==  len(h3) -1:
                h3_all = h3_all + h3[x].text
            else:
                h3_all = h3_all + h3[x].text + ". "
    
        allthecontent = ""
        allthecontent = str(title) + " " + str(description) + " " + str(h1_all) + " " + str(h2_all) + " " + str(h3_all) + " " + str(paragraphs_all)
        allthecontent = str(allthecontent)[0:999]

        print(allthecontent)
    except Exception as e:
            print(e)

def get_website_title(url):    
    # making requests instance
    reqs = requests.get(url)
    
    # using the BeautifulSoup module
    soup = BeautifulSoup(reqs.text, 'html.parser')
    
    # displaying the title
    # print("Title of the website is : ")
    # for title in soup.find_all('title'):
    #     print(title.get_text())
    return soup.find_all('title')

url = 'https://www.geeksforgeeks.org/extract-title-from-a-webpage-using-python/'

# get_tabs()

def categorize_websites():
    his = get_tabs()
    titles = get_website_title(his[-1][-1])
    
    for title in titles:
        print(title.get_text())
        web_category(title.get_text())

# categorize_websites()
# get_logon_logoff()
# get_website_content('https://en.wikipedia.org/wiki/Microsoft')

# translator = Translator()
 
# try:
#         translation = translator.translate(allthecontent).texrt
#         translation = str(translation)[0:999]
#         time.sleep(10)
        
# except Exception as e:
#         print(e)


