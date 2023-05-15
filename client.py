import win32com.client
import subprocess
from browser_history.browsers import Chrome
import datetime
from googletrans import Translator
from bs4 import BeautifulSoup
import requests
# from keyboard import record
import keyboard as kboard
from socket import *
import os
import docx
from rake_nltk import Rake
from threading import Thread
import time
from threads import *
from pynput import mouse, keyboard
import sys
from admin import *
from client_gui import *
import pyautogui


def get_buffer(data):
    length = len(data)
    count = 0

    while length != 0:
        length = int(length/10)
        count+=1

    buffer = (5-count)*'0' + f'{len(data)}'
    return buffer


def get_running_apps():
    apps = []
    NOT_WANTED_APPS = 'Description-----------Application Frame Host'
    cmd = 'powershell "gps | where {$_.MainWindowTitle } | select Description'
    # cmd = 'powershell "gps | where {$_.MainWindowTitle } | select ProcessName'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    for line in proc.stdout:
        if line.rstrip() and line.decode().rstrip() not in NOT_WANTED_APPS:
            # only print lines that are not empty
            # decode() is necessary to get rid of the binary string (b')
            # rstrip() to remove `\r\n`
            app = line.decode().rstrip()
            if app not in used_apps:
                apps.append(app)
                used_apps.append(app)
    try:
        apps.remove('Setup/Uninstall')
    except:
        pass
    
    if apps:
        apps = '#'.join(apps)
        buffer = get_buffer(f"new_apps:{user_id}:{apps}")
        sock.send(buffer.encode())
        sock.send(f"new_apps:{user_id}:{apps}".encode())
        verify_user_anomaly()

    
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
        if date == today and tab[1] not in visited_websites:
            websites.append(tab[1])
            visited_websites.append(tab[1])
    
    # print(websites)
    web_list = []
    for url in websites:
        title = get_website_title(url)
        if title:
            web_list.append(f"{url}  {title}")
            
    print("websites")
    print(web_list)
    websites = ';'.join(web_list)
    
    if websites:
        buffer = get_buffer(f"new_websites>{user_id}>{websites}")
        sock.send(buffer.encode())
        sock.send(f"new_websites>{user_id}>{websites}".encode())
        verify_user_anomaly()


def get_website_title(url):    
    # making requests instance
    reqs = requests.get(url)
    
    # using the BeautifulSoup module
    soup = BeautifulSoup(reqs.text, 'html.parser')
    try:    
        return soup.find_all('title')[0].get_text()
    except:
        return None


def type_trace():
    while True:
        recorded = kboard.record(until='enter')
        all_keys = [key.name for key in recorded if key.event_type == "down"]
        all_keys.pop(-1)
        all_keys = ''.join(all_keys)
        all_keys = all_keys.replace('space', ' ')
        all_keys = all_keys.replace('shift', '')
        print("Typed text")
        print(all_keys)

        if all_keys != '' and len(all_keys) > 5:
            buffer = get_buffer(f"new_text*{user_id}*{all_keys}")
            sock.send(buffer.encode())
            sock.send(f"new_text*{user_id}*{all_keys}".encode())
            verify_user_anomaly()


def get_word_docs():
    print('running')
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
    time_threshold = datetime.datetime.now() - datetime.timedelta(days=1)  # 1 day
    for document, modified_time in documents:
        if modified_time > time_threshold:
            new_docs.append(document)

    for doc in new_docs:
        print(doc)

    if new_docs:
        for doc in new_docs:
            get_word_text(doc)
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
    print("Word doc")
    print(new_words)

    buffer = get_buffer(f"new_text*{user_id}*{new_words}")
    sock.send(buffer.encode())
    sock.send(f"new_text*{user_id}*{new_words}".encode())
    verify_user_anomaly()


def unblock_computer():
    global block_comp
    buffer = sock.recv(5).decode()
    check = sock.recv(int(buffer)).decode()
    print(check)
    block_comp = False


def block_computer():
    global block_comp

    thread = Thread(target=unblock_computer)

    print("block")
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    # Move the mouse pointer to the upper-left corner of the screen
    x, y = 0, 0

    # Move the mouse pointer to the lower-right corner of the screen
    w, h = pyautogui.size()
    w -= 1
    h -= 1

    thread.start()

    # kboard.block_key(kboard.all_modifiers)
    for i in range(150):
        kboard.block_key(i)

    while block_comp:
        pyautogui.moveTo(x, y, duration=0)
        pyautogui.moveTo(w, h, duration=0)

    for i in range(150):
        kboard.unblock_key(i)

    print("done blocking")


def wait_for_block():
    global run_tracking, block_comp
    while True:
        data, address = udp_socket.recvfrom(5)
        block_comp = True
        run_tracking = False


def on_anomaly_verified(successful):
    global block_comp, run_tracking
    block_comp = not successful
    if block_comp:
        run_tracking = False


def verify_user_anomaly():
    global block_comp

    buffer = sock.recv(5).decode()
    check = sock.recv(int(buffer)).decode()

    if check != "okay":
        anomaly_window = AnomalyWindow(sock, app)
        anomaly_window.anomaly_verified.connect(on_anomaly_verified)
        anomaly_window.show()
        anomaly_window.start_timer()
        app.exec_()
    

def on_login_successful(successful):
    global block_comp, run_tracking, user_id, is_admin

    block_comp = not successful
    print(block_comp)
    if block_comp:
        run_tracking = False

    else:
        run_tracking = True
        buffer = sock.recv(5).decode()
        data = sock.recv(int(buffer)).decode()
        data = data.split(":")
        user_id = data[1]

        if data[0] == "admin":
            is_admin = True
        
        else:
            is_admin = False


def start_server_conn():
    login_window = LoginWindow(sock, app)
    login_window.login_successful.connect(on_login_successful)
    login_window.show()
    login_window.start_timer()
    app.exec_()


def logout_user(successful):
    global run_tracking

    if successful:
        buffer = get_buffer(f"logoff;{user_id}")
        sock.send(buffer.encode())
        sock.send(f"logoff;{user_id}".encode())

        run_tracking = False


def wait_for_user_activity():
    print("waiting")
    activity_detected = False
    # Define a function to handle user activity
    def on_activity(*args):
        nonlocal activity_detected
        activity_detected = True

    # Create a listener for mouse and keyboard events
    with mouse.Listener(on_click=on_activity) as mouse_listener:
        with keyboard.Listener(on_press=on_activity) as keyboard_listener:
            # Wait for user activity
            activity_detected = False
            while not activity_detected:
                time.sleep(1)
            
            # Stop the listeners
            mouse_listener.stop()
            keyboard_listener.stop()

    print("User activity detected!")
    start_server_conn()

    if not is_admin:
        verify_user_anomaly()


def track_user_inactive():
    print("Run Tracking")
    # app_thread = RepeatTimer(5, get_running_apps)
    # app_thread.start()

    # web_thread = RepeatTimer(60, get_tabs)
    # web_thread.start()

    # word_thread = RepeatTimer(300, get_word_docs)
    # word_thread.start()

    # type_thread = Thread(target=type_trace)
    # type_thread.start()

    inactivity_threshold = 300

    # Define a function to handle user activity
    def on_activity(*args):
        nonlocal last_activity_time
        last_activity_time = time.time()

    # Start tracking time
    last_activity_time = time.time()
    # Create a listener for mouse and keyboard events
    with mouse.Listener(on_move=on_activity, on_click=on_activity, on_scroll=on_activity) as mouse_listener:
        with keyboard.Listener(on_press=on_activity, on_release=on_activity) as keyboard_listener:
            # Loop until user shows activity
            while run_tracking:
                # Check if user has been inactive for too long
                if time.time() - last_activity_time > inactivity_threshold:
                    print("User is inactive!")
                    logout_window = LogoutWindow(app)
                    logout_window.logout_verified.connect(logout_user)
                    logout_window.show()
                    logout_window.start_timer()
                    app.exec_()
                else:
                    print("active")
                    pass                
                # Wait for 1 second before checking again
                time.sleep(1)
            
            # Stop the listeners
            mouse_listener.stop()
            keyboard_listener.stop()

    print("Tracking stopped.")

    # app_thread.cancel()
    # web_thread.cancel()
    # word_thread.cancel()
    # type_thread.cancel()


def run_user_activity():
    global is_admin, run_tracking, block_comp
    
    buffer = sock.recv(5).decode()
    check = sock.recv(int(buffer)).decode()

    if check == "block":
        block_comp = True
        run_tracking = False

    while True:
        print(block_comp)
        if not block_comp:
            wait_for_user_activity()
        
        if block_comp:
            block_computer()
            # run_tracking = True

        if not is_admin:
            track_user_inactive()

        if is_admin:
            app = QApplication(sys.argv)
            win = Window(sock)
            win.show()
            sys.exit(app.exec_())


if __name__ == '__main__': 
    sock = socket(AF_INET,SOCK_STREAM)
    sock.connect(("192.168.1.192",55000))

    # create a UDP socket
    udp_socket = socket(AF_INET, SOCK_DGRAM)

    # send data to the server
    server_address = ('192.168.1.192', 55500)
    udp_socket.sendto("yo".encode(), server_address)

    thread = Thread(target=wait_for_block)
    thread.start()

    app = QApplication(sys.argv)

    is_admin = False
    block_comp = False
    run_tracking = False

    visited_websites = []
    used_apps = []
    user_id = ""

    run_user_activity()
    # block_computer()
    # track_user_inactive()

        


