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
    suffix = str(len(data)).rjust(5,"0")
    return suffix


# Gets all running applications
def get_running_apps():
    global check_anomaly, used_apps

    apps = []
    NOT_WANTED_APPS = 'Description-----------Application Frame Host Setup/Uninstall ProcessName ApplicationFrameHost SystemSettings TextInputHost python explorer'
    # cmd = 'powershell "gps | where {$_.MainWindowTitle } | select Description'
    cmd = 'powershell "gps | where {$_.MainWindowTitle } | select ProcessName'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    for line in proc.stdout:
        if line.rstrip() and line.decode().rstrip() not in NOT_WANTED_APPS:
            # only print lines that are not empty
            # decode() is necessary to get rid of the binary string (b')
            # rstrip() to remove `\r\n`
            app = line.decode().rstrip()
            temp = app.replace(' ', '')

            if app == "chrome":
                app = "Google Chrome"
            elif app == "Code":
                app = "Visual Studio Code"

            if temp.isalpha() and app not in used_apps:
                apps.append(app)
    
    if apps:
        if not check_anomaly:
            for app in apps:
                used_apps.append(app)

            apps = '#'.join(apps)
            buffer = get_buffer(f"new_apps>{user_id}>{apps}")
            sock.send(buffer.encode())
            sock.send(f"new_apps>{user_id}>{apps}".encode())
            # verify_user_anomaly()
            check_anomaly = True

    
# Gets all the visited websites
def get_tabs():
    global check_anomaly, visited_websites

    c = Chrome()
    outputs = c.fetch_history()

    # his is a list of (datetime.datetime, url) tuples
    his = outputs.histories
    websites = []
    today = datetime.datetime.today()
    today = today.strftime("%d/%m/%Y")

    # if not check_anomaly:
    for tab in his:
        date = tab[0].strftime('%d/%m/%Y')
        tab_time = tab[0].strftime("%H:%M:%S")

        if date == today and tab_time > login_time and tab[1] not in visited_websites and tab[1] not in websites:
            websites.append(tab[1])
    
    web_list = []
    for url in websites:
        title = get_website_title(url)
        if title:
            if " - חיפוש ב-Google" in title:
                title = title.replace(" - חיפוש ב-Google", "")

            web_list.append(f"{url}  {title}")
                
    if websites:
        if not check_anomaly:
            for web in websites:
                visited_websites.append(web.split("  ")[0])

            websites = ';'.join(web_list)
            buffer = get_buffer(f"new_websites>user_1>{websites}")
            sock.send(buffer.encode())
            sock.send(f"new_websites>{user_id}>{websites}".encode())
            # verify_user_anomaly()
            check_anomaly = True


# Gets the titels of the websites using the URLs
def get_website_title(url):    
    # making requests instance
    reqs = requests.get(url)
    
    # using the BeautifulSoup module
    soup = BeautifulSoup(reqs.text, 'html.parser')
    try:    
        return soup.find_all('title')[0].get_text()
    except:
        return None


# Sends the real-time tracked typed text to the server
def type_trace(data):
    global check_anomaly, run_tracking
    if not check_anomaly:
        buffer = get_buffer(f"new_text>{user_id}>{data}")
        sock.send(buffer.encode())
        sock.send(f"new_text>{user_id}>{data}".encode())
        check_anomaly = True


# Blocks computer keyboard and mouse input
def block_computer():
    global block_comp

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    # Move the mouse pointer to the upper-left corner of the screen
    x, y = 0, 0

    # Move the mouse pointer to the lower-right corner of the screen
    w, h = pyautogui.size()
    w -= 1
    h -= 1

    for i in range(150):
        kboard.block_key(i)

    while block_comp:
        pyautogui.moveTo(x, y, duration=0)
        pyautogui.moveTo(w, h, duration=0)

    for i in range(150):
        kboard.unblock_key(i)


# Blocks and unblocks computer upon server command
def wait_for_block():
    global run_tracking, block_comp
    while True:
        try:
            data, address = udp_socket.recvfrom(5)
            if data.decode() == "block":
                block_comp = True
                run_tracking = False
            else:
                block_comp = False
        except:
            block_comp = False


# Blocks computer if user verification fails upon anomaly detection, else continues tracking
def on_anomaly_verified(successful):
    global block_comp, run_tracking, check_anomaly, app_thread, web_thread
    block_comp = not successful
    if block_comp:
        run_tracking = False

    check_anomaly = False


# Runs anomaly verification window to verifiy user identity upon anomaly detection
def verify_user_anomaly():
    global block_comp, check_anomaly, app_thread, web_thread

    buffer = sock.recv(5).decode()
    check = sock.recv(int(buffer)).decode()

    if check != "okay":
        anomaly_window = AnomalyWindow(sock, app)
        anomaly_window.anomaly_verified.connect(on_anomaly_verified)
        anomaly_window.show()
        app.exec_()
    else:
        check_anomaly = False
    

# Begins user tracking if login/signup is successful
def on_login_successful(successful):
    global block_comp, run_tracking, user_id, is_admin, user_psw

    block_comp = not successful
    if block_comp:
        run_tracking = False

    else:
        run_tracking = True
        buffer = sock.recv(5).decode()
        data = sock.recv(int(buffer)).decode()
        data = data.split(":")
        user_id = data[1]
        user_psw = data[2]

        if data[0] == "admin":
            is_admin = True
        
        else:
            is_admin = False


# Runs login/signup window
def start_server_conn():
    login_window = LoginWindow(sock, app)
    login_window.login_successful.connect(on_login_successful)
    login_window.show()
    login_window.start_timer()
    app.exec_()


# Logs out user 
def logout_user(successful):
    global run_tracking

    if successful:
        buffer = get_buffer(f"logoff>{user_id}")
        sock.send(buffer.encode())
        sock.send(f"logoff>{user_id}".encode())

        run_tracking = False


# Waits for user activity. Once user activity is detected, it runs the login/signup functions
def wait_for_user_activity():
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

    start_server_conn()

    if not is_admin and not block_comp:
        verify_user_anomaly()



# Continuously checks user activity and alerts if user is inactive. If user is inactive then the tracking
# stops and the system waits for user activity.
# Also runs the real-time text recording.
def track_user_inactive():
    global app_thread, web_thread, login_time, visited_websites, used_apps, user_id, user_psw
    now = datetime.datetime.now()
    login_time = now.strftime("%H:%M:%S")

    app_thread = RepeatTimer(10, get_running_apps)
    app_thread.start()

    web_thread = RepeatTimer(6, get_tabs)
    web_thread.start()

    inactivity_threshold = 30
    last_typed_threshold = 5

    # Define a function to handle user activity
    def on_key_activity(key):
        nonlocal last_activity_time, typed_text
        try:
            typed_text += key.char
        except:
            if keyboard.Key.space is key:
                typed_text += " "

            if keyboard.Key.enter is key:
                if user_psw in typed_text:
                    typed_text = typed_text.replace(user_psw, "")

                if typed_text != "" and len(typed_text) > 5:
                    type_trace(typed_text)
                typed_text = ""
        
        last_activity_time = time.time()


    def on_mouse_activity(*args):
        nonlocal last_activity_time, typed_text
        last_activity_time = time.time()
        
    def on_mouse_click(*args):
        nonlocal last_activity_time, typed_text
        last_activity_time = time.time()

        if user_psw in typed_text:
            typed_text = typed_text.replace(user_psw, "")

        if typed_text != "" and len(typed_text) > 5:
            type_trace(typed_text)
        typed_text = ""


    typed_text = ""
    # Start tracking time
    last_activity_time = time.time()
    # Create a listener for mouse and keyboard events
    with mouse.Listener(on_move=on_mouse_activity, on_click=on_mouse_click, on_scroll=on_mouse_activity) as mouse_listener:
        with keyboard.Listener(on_press=on_key_activity) as keyboard_listener:
            # Loop until user shows activity
            while run_tracking:
                # Check if user has been inactive for too long
                if time.time() - last_activity_time > inactivity_threshold:
                    logout_window = LogoutWindow(app)
                    logout_window.logout_verified.connect(logout_user)
                    logout_window.show()
                    logout_window.start_timer()
                    app.exec_()

                else:  
                    if time.time() - last_activity_time > last_typed_threshold:
                        if user_psw in typed_text:
                            typed_text = typed_text.replace(user_psw, "")

                        if typed_text != "" and len(typed_text) > 5:
                            type_trace(typed_text)
                        typed_text = ""
                        
                    if check_anomaly:
                        verify_user_anomaly()

                # Wait for 1 second before checking again 
                time.sleep(1)
            
            # Stop the listeners
            mouse_listener.stop()
            keyboard_listener.stop()

    app_thread.cancel()
    web_thread.cancel()

    visited_websites = []
    used_apps = []
    user_id = ""
    user_psw = ""
    login_time = ""


def run_user_activity():
    global is_admin, run_tracking, block_comp
    
    buffer = sock.recv(5).decode()
    check = sock.recv(int(buffer)).decode()

    if check == "block":
        block_comp = True
        run_tracking = False

    while True:

        if not block_comp:
            wait_for_user_activity()
        
        if block_comp:
            block_computer()

        if not is_admin:
            track_user_inactive()

        if is_admin:
            app = QApplication(sys.argv)
            win = Window(sock)
            win.show()
            sys.exit(app.exec_())


if __name__ == '__main__': 
    sock = socket(AF_INET,SOCK_STREAM)
    sock.connect(("172.17.120.199",55000))

    # create a UDP socket
    udp_socket = socket(AF_INET, SOCK_DGRAM)

    # send data to the server
    server_address = ('172.17.120.199', 55500)
    udp_socket.sendto("yo".encode(), server_address)

    thread = Thread(target=wait_for_block)
    thread.start()

    app = QApplication(sys.argv)

    is_admin = False
    block_comp = False
    run_tracking = False
    check_anomaly = False

    visited_websites = []
    used_apps = []
    user_id = ""
    user_psw = ""
    login_time = ""
    
    run_user_activity()

        


