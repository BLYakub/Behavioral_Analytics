import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox, QWidget, QComboBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
import client
import pyautogui
import time


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(bool)

    def __init__(self, sock, app):
        super().__init__()
        self.sock = sock
        self.app = app
        self.setWindowTitle('Login')
        self.setGeometry(500, 500, 400, 250)
        self.close_window = False

        # Create username label and field
        self.username_label = QLabel('Username:', self)
        self.username_label.move(50, 50)
        self.username_field = QLineEdit(self)
        self.username_field.move(150, 50)

        # Create password label and field
        self.password_label = QLabel('Password:', self)
        self.password_label.move(50, 80)
        self.password_field = QLineEdit(self)
        self.password_field.move(150, 80)

        # Create action combobox
        self.action_label = QLabel('Action:', self)
        self.action_label.move(50, 110)
        self.action_combobox = QComboBox(self)
        self.action_combobox.addItem('Login')
        self.action_combobox.addItem('Sign Up')
        self.action_combobox.move(150, 110)

        # Create enter button
        self.enter_button = QPushButton('Enter', self)
        self.enter_button.move(150, 160)
        self.enter_button.clicked.connect(self.login_or_signup)

    def start_timer(self):
        # Set timer for one minute
        self.warning1_timer = QTimer(self)
        self.warning1_timer.timeout.connect(self.show_warning1)
        self.warning1_timer.start(60000)

        self.warning2_timer = QTimer(self)
        self.warning2_timer.timeout.connect(self.show_warning2)

    def login_or_signup(self):
        # Get username and password fields' text
        username = self.username_field.text()
        password = self.password_field.text()
        action = self.action_combobox.currentText()

        # Check if fields are empty
        if username == '' or password == '':
            QMessageBox.warning(self, 'Warning', 'Please enter both username and password')
        else:
            buffer = client.get_buffer(f"new_user:{action}:{username}:{password}")
            self.sock.send(buffer.encode())
            self.sock.send(f"new_user:{action}:{username}:{password}".encode())

            buffer = self.sock.recv(5).decode()
            check = self.sock.recv(int(buffer)).decode()
            print(check)

            if check != "ok":
                QMessageBox.information(self, 'Warning', f'{check}')

            else:
                self.close_window = True
                self.login_successful.emit(True)
                # QApplication.quit()
                self.close()

    def show_warning1(self):
        # Stop the first timer and start the second timer
        self.warning1_timer.stop()
        self.warning2_timer.start(60000)

        # Show the first warning
        QMessageBox.warning(self, 'Warning', 'You have one minute to enter your password before computer gets blocked')

    def show_warning2(self):
        # Stop the second timer and disable user actions
        self.warning2_timer.stop()
        QMessageBox.warning(self, 'Warning', 'Computer will now get blocked')
        
        buffer = client.get_buffer(f"new_user:block::")
        self.sock.send(buffer.encode())
        self.sock.send(f"new_user:block::".encode())

        # client.block_comp = True
        self.login_successful.emit(False)
        self.close_window = True
        self.close()

    def closeEvent(self, event):
        if not self.close_window:
            event.ignore()  # Ignore attempts to close the window


class AnomalyWindow(QMainWindow):
    anomaly_verified = pyqtSignal(bool)

    def __init__(self, sock, app):
        super().__init__()
        self.sock = sock
        self.app = app
        self.setWindowTitle('Re-Enter')
        self.setGeometry(500, 500, 400, 250)
        self.close_window = False

        self.password_label = QLabel('Anomaly detected! Re-enter your user password:', self)
        self.password_label.move(50, 50)

        # Create password label and field
        self.password_label = QLabel('Password:', self)
        self.password_label.move(50, 80)
        self.password_field = QLineEdit(self)
        self.password_field.move(150, 80)

        # Create enter button
        self.enter_button = QPushButton('Enter', self)
        self.enter_button.move(150, 160)
        self.enter_button.clicked.connect(self.re_enter_psw)

        self.warning1_timer = QTimer(self)
        self.warning1_timer.timeout.connect(self.show_warning1)
        self.warning1_timer.start(60000)

        self.warning2_timer = QTimer(self)
        self.warning2_timer.timeout.connect(self.show_warning2)

    def start_timer(self):
        # Set timer for one minute
        self.warning1_timer = QTimer(self)
        self.warning1_timer.timeout.connect(self.show_warning1)
        self.warning1_timer.start(60000)

        self.warning2_timer = QTimer(self)
        self.warning2_timer.timeout.connect(self.show_warning2)


    def re_enter_psw(self):
        password = self.password_field.text()

        if password == '':
            QMessageBox.warning(self, 'Warning', 'Please Enter Your Password!')
        
        else:
            buffer = client.get_buffer(password)
            self.sock.send(buffer.encode())
            self.sock.send(password.encode())

            buffer = self.sock.recv(5).decode()
            check = self.sock.recv(int(buffer)).decode()

            if check != "okay":
                QMessageBox.warning(self, 'Warning', 'Incorrect Password. Computer will now be blocked.')
                # client.block_comp = True
                self.anomaly_verified.emit(False)
            else:
                self.anomaly_verified.emit(True)

            self.close_window = True
            self.close()

    def show_warning1(self):
        # Stop the first timer and start the second timer
        self.warning1_timer.stop()
        self.warning2_timer.start(60000)

        # Show the first warning
        QMessageBox.warning(self, 'Warning', 'You have one minute to enter your password before computer gets blocked')

    def show_warning2(self):
        # Stop the second timer and disable user actions
        self.warning2_timer.stop()
        QMessageBox.warning(self, 'Warning', 'Computer will now get blocked')
        
        buffer = client.get_buffer("-")
        self.sock.send(buffer.encode())
        self.sock.send("-".encode())

        buffer = self.sock.recv(5).decode()
        check = self.sock.recv(int(buffer)).decode()
        
        # client.block_comp = True
        self.anomaly_verified.emit(True)
        self.close_window = True
        self.close()
            
    def closeEvent(self, event):
        if not self.close_window:
            event.ignore()  # Ignore attempts to close the window
            

class BlockedWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        # self.close_window = False
        self.app = app
        self.setWindowTitle('Blocked Window')
        self.setGeometry(500, 500, 400, 200) # Set window position and size

        # Create a QLabel widget with "Computer is blocked" text and set its font and size
        label = QLabel(self)
        label.setText("Computer is blocked")
        # label.setFont(label.font().pointSize() * 2, bold=True)

    # def closeEvent(self, event):
        # if not self.close_window:
            # event.ignore()


class LogoutWindow(QWidget):
    logout_verified = pyqtSignal(bool)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.close_window = False

        self.setWindowTitle('Logout Window')
        self.setGeometry(100, 100, 400, 200) # Set window position and size

        label = QLabel(self)
        label.setText("Are you still active?")
        # label.setFont(label.font().pointSize() * 2, bold=True)

        # Create two QPushButton widgets for "Yes" and "No"
        button_yes = QPushButton('Yes', self)
        button_no = QPushButton('No', self)

        # Connect the buttons to their respective functions
        button_yes.clicked.connect(self.closeWindow)
        button_no.clicked.connect(self.logout)

        # Create a QHBoxLayout widget to align the buttons horizontally
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(button_yes)
        hbox.addWidget(button_no)

        # Create a QVBoxLayout widget to stack the label and hbox widgets vertically
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addStretch()
        vbox.addLayout(hbox)

        # Set the main layout of the window to the vbox layout
        self.setLayout(vbox)

    def start_timer(self):
        self.warning_timer = QTimer(self)
        self.warning_timer.timeout.connect(self.logout)
        self.warning_timer.start(60000)

    def logout(self):
        self.warning_timer.stop()
        QMessageBox.warning(self, 'Warning', 'User has been logged out')

        self.logout_verified.emit(True)
        self.close_window = True
        self.close()

    def closeWindow(self):
        self.logout_verified.emit(False)
        self.close_window = True
        self.close()

    def closeEvent(self, event):
        if not self.close_window:
            event.ignore()

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     login_window = LoginWindow(0)
#     login_window.show()
#     app.exec_()
#     print("Yo dog")
