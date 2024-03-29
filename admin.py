import sys
import sqlite3
from profiles import *
from socket import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHeaderView, QLineEdit, QMessageBox, QLabel, QMainWindow, QAction, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter


class Window(QMainWindow):

    """Main Window."""
    def __init__(self, sock, parent=None):
        """Initializer."""
        super().__init__(parent)
        self.sock = sock
        self.conn = sqlite3.connect('my_db.db')
        # self.conn = sqlite3.connect('temp_db.db')
        self.c = self.conn.cursor()
        self.setWindowTitle("Admin View")
        self.resize(1000, 600)
        self.centralWidget = QLabel("Hello, World")
        self.centralWidget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setCentralWidget(self.centralWidget)

        self._createActions()
        self._createMenuBar() 


    def _createActions(self):
        # Creating actions using the second constructor
        self.dataAction = QAction("&View Data.", self)
        self.predictionAction = QAction("&Topic Predictions", self)
        self.anomalyAction = QAction("&Anomly Data", self)
        self.blockedComputers = QAction("&Blocked Computers", self)
        self.connectedComputers = QAction("&Connected Computers", self)


    def _createMenuBar(self):
        menuBar = self.menuBar()

        dataMenu = menuBar.addMenu("&View Data")
        self.dataAction.triggered.connect(self.view_user_data)
        dataMenu.addAction(self.dataAction)
        self.predictionAction.triggered.connect(self.view_topic_predictions)
        dataMenu.addAction(self.predictionAction)
        self.connectedComputers.triggered.connect(self.view_connected_computers)
        dataMenu.addAction(self.connectedComputers)

        anomalyMenu = menuBar.addMenu("&Anomalies")
        self.anomalyAction.triggered.connect(self.view_anomaly_data)
        anomalyMenu.addAction(self.anomalyAction)
        self.blockedComputers.triggered.connect(self.view_blocked_computers)
        anomalyMenu.addAction(self.blockedComputers)


    # View user profiles 
    def view_user_data(self):
        self.c.execute("SELECT * FROM users WHERE is_admin = '0'")
        users = self.c.fetchall()

        self.selectBox1 = QComboBox()
        for user in users:
            self.selectBox1.addItem(user[0])
        # self.selectBox1.currentIndexChanged.connect(self.update_chart)

        self.selectBox2 = QComboBox()
        self.selectBox2.addItem("Apps")
        self.selectBox2.addItem("Websites")
        self.selectBox2.addItem("Texts")
        # self.selectBox2.currentIndexChanged.connect(self.update_chart)

        button = QPushButton("Show Data")
        button.clicked.connect(self.update_chart)

        # Create the chart and chart view
        self.chart = QChart()
        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.Antialiasing)

        # Create the labels for the chart data
        self.dataLabel1 = QLabel()
        self.dataLabel2 = QLabel()
        self.dataLabel3 = QLabel()

        # Create the layout for the chart and labels
        chartLayout = QVBoxLayout()
        chartLayout.addWidget(self.chartView)

        dataLayout = QHBoxLayout()
        dataLayout.addWidget(self.dataLabel1)
        dataLayout.addWidget(self.dataLabel2)
        dataLayout.addWidget(self.dataLabel3)

        # Create the layout for the combo boxes
        comboLayout = QHBoxLayout()
        comboLayout.addWidget(self.selectBox1)
        comboLayout.addWidget(self.selectBox2)
        comboLayout.addWidget(button)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(comboLayout)
        mainLayout.addLayout(chartLayout)
        mainLayout.addLayout(dataLayout)

        # Set the layout for the window
        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)


    def update_chart(self):
        # Get the selected option from the select box
        user = self.selectBox1.currentText()
        category = self.selectBox2.currentText().lower()

        self.c.execute(f"SELECT * FROM apps WHERE user_id = '{user}'")
        apps = self.c.fetchall()

        self.c.execute(f"SELECT * FROM websites WHERE user_id = '{user}'")
        websites = self.c.fetchall()

        self.c.execute(f"SELECT * FROM texts WHERE user_id = '{user}'")
        texts = self.c.fetchall()
        # print(apps, websites, texts)
        app_data, web_data, text_data = create_profile(apps, websites, texts)

        app_data = ', '.join(app_data)
        web_data = ', '.join(web_data)
        text_data = ', '.join(text_data)
        
        self.dataLabel1.setText(f"Most Used Apps:\n{app_data}")
        self.dataLabel2.setText(f"Most Searched Topics:\n{web_data}")
        self.dataLabel3.setText(f"Most Typed Topics:\n{text_data}")

        # Clear any existing data in the chart
        self.chart.removeAllSeries()

        self.c.execute(f"SELECT * FROM {category} WHERE user_id = '{user}'")
        user_data = self.c.fetchall()

        if category == "websites":
            user_data = [web[2] for web in user_data]
            user_data = [(t, user_data.count(t)) for t in set(user_data)]
        
        else:
            user_data = [(data[1], data[2]) for data in user_data]

        data_percentage = get_data_percentage(user_data)

        series = QPieSeries()
        for value, percent in data_percentage:
            series.append(value, percent)

        for i, slice in enumerate(series.slices()):
            slice.setLabel(f"{slice.label()}: {data_percentage[i][1]}%")

        self.chart.addSeries(series)
        self.chart.setTitle(user)
        self.chartView.setChart


    # View topics predected by the ML model
    def view_topic_predictions(self):
        self.c.execute("SELECT * FROM label_data WHERE verified = '0'")
        record = self.c.fetchall()

        self.topic_table = QTableWidget(self)
        self.topic_table.setRowCount(len(record))
        self.topic_table.setColumnCount(4)

        header = self.topic_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)       
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        # Set the column headers
        self.topic_table.setHorizontalHeaderLabels(["Text", "Topic", "Approve", "Change"])

        # Add data to the table
        for i in range(self.topic_table.rowCount()):

            item = QTableWidgetItem(record[i][0])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.topic_table.setItem(i, 0, item)

            item = QTableWidgetItem(record[i][1])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.topic_table.setItem(i, 1, item)

            button1 = QPushButton("Approve")
            self.topic_table.setCellWidget(i, 2, button1)
            button1.clicked.connect(lambda: self.approve_topic(record))

            self.topic_field = QLineEdit(self)
            # self.topic_table.setCellWidget(i, 3, self.topic_field)
            button2 = QPushButton("Change")
            # self.topic_table.setCellWidget(i, 3, button2)
            button2.clicked.connect(lambda: self.change_topic(record))

            layout = QHBoxLayout()
            layout.addWidget(self.topic_field)
            layout.addWidget(button2)

            cellWidget = QWidget()
            cellWidget.setLayout(layout)
            self.topic_table.setCellWidget(i, 3, cellWidget)

            self.topic_table.setRowHeight(i, 48)

        train_button = QPushButton("Train Model", self)
        train_button.clicked.connect(self.train_model)

        layout = QVBoxLayout()
        layout.addWidget(self.topic_table)
        layout.addWidget(train_button)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def train_model(self):

        buffer = str(len("train_model")).rjust(5,"0")

        self.sock.send(buffer.encode())
        self.sock.send(f"train_model".encode())


    def approve_topic(self, topic_data):
        index = self.topic_table.indexAt(self.sender().pos())
        topic_data = topic_data[index.row()]

        text = topic_data[0]
        topic = topic_data[1]

        self.c.execute(f"UPDATE label_data SET verified = '1' WHERE text = '{text}' AND subject = '{topic}'")
        self.conn.commit()

        self.view_topic_predictions()


    def change_topic(self, topic_data):
        index = self.topic_table.indexAt(self.sender().pos())
        topic_data = topic_data[index.row()]

        text = topic_data[0]
        topic = topic_data[1]
        new_topic = self.topic_field.text().upper()
        allowed_topics = ["ENTERTAINMENT", "SPORTS", "TECHNOLOGY", "BUSINESS", "HEALTH", "SCIENCE"]

        if new_topic == "" or new_topic not in allowed_topics:
            QMessageBox.warning(self, 'Warning', 'Topic should be one of the following:\nEntertainment, Sports, Technology, Business, Health, Science')
        else:  
            self.c.execute(f"UPDATE label_data SET verified = '1', subject = '{new_topic}' WHERE text = '{text}' AND subject = '{topic}'")
            self.conn.commit()
            self.view_topic_predictions()


    def view_connected_computers(self):
        buffer = str(len("online_users")).rjust(5,"0")
        self.sock.send(buffer.encode())
        self.sock.send("online_users".encode())

        buffer = self.sock.recv(5).decode()
        data = self.sock.recv(int(buffer)).decode()

        data = data.split(":")
        data = [x.split(",") for x in data]

        self.connected_table = QTableWidget(self)
        self.connected_table.setRowCount(len(data))
        self.connected_table.setColumnCount(2)

        # Set the column headers
        self.connected_table.setHorizontalHeaderLabels(["IP Address", "User"])

        for i in range(self.connected_table.rowCount()):

            item = QTableWidgetItem(data[i][0])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.connected_table.setItem(i, 0, item)

            if data[i][1] == "":
                item = QTableWidgetItem("None")
            else:
                item = QTableWidgetItem(data[i][1])

            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.connected_table.setItem(i, 1, item)
        
        self.setCentralWidget(self.connected_table)


    # View user behavioral anomaly data
    def view_anomaly_data(self):

        self.c.execute("SELECT * FROM anomalies WHERE handled = '0'")
        record = self.c.fetchall()

        self.anomaly_table = QTableWidget(self)
        self.anomaly_table.setRowCount(len(record))
        self.anomaly_table.setColumnCount(8)

        # Set the column headers
        self.anomaly_table.setHorizontalHeaderLabels(["Time", "User ID", "IP Address", "Field", "Anomaly", "Confirm Action", "Decline Action", "Block Computer"])
        
        check_data = []
        for i in range(len(record)):
            check_data.append([record[i][0], record[i][1], record[i][2], record[i][3], record[i][4]])

        # Add data to the table
        for i in range(self.anomaly_table.rowCount()):

            if check_data[i][3] == "websites":
                web = check_data[i][4].split('  ')
                check_data[i][4] = web[2]

            for j in range(self.anomaly_table.columnCount() - 3):
                item = QTableWidgetItem(check_data[i][j])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
                self.anomaly_table.setItem(i, j, item)

            button1 = QPushButton("Approve")
            self.anomaly_table.setCellWidget(i, self.anomaly_table.columnCount() - 3, button1)
            button1.clicked.connect(lambda: self.confirm_action(record))

            button2 = QPushButton("Decline")
            self.anomaly_table.setCellWidget(i, self.anomaly_table.columnCount() - 2, button2)
            button2.clicked.connect(lambda: self.confirm_anomaly(record))

            button3 = QPushButton("Block")
            self.anomaly_table.setCellWidget(i, self.anomaly_table.columnCount() - 1, button3)
            button3.clicked.connect(lambda: self.block_computer(record))
        
        self.setCentralWidget(self.anomaly_table)


    def confirm_action(self, anomaly_data):
        index = self.anomaly_table.indexAt(self.sender().pos())

        anomaly_data = anomaly_data[index.row()]
        
        time = anomaly_data[0]
        user_id = anomaly_data[1]
        ip_addr = anomaly_data[2]
        field = anomaly_data[3]
        anomaly = anomaly_data[4]
        
        if field == "websites":
            anomaly = anomaly.split('  ')
            self.c.execute("INSERT INTO websites (user_id, link, topic, title) VALUES(?,?,?,?)",(user_id, anomaly[0], anomaly[2], anomaly[1]))
        
        elif field == "apps":
            self.c.execute(f"SELECT * FROM apps WHERE user_id = '{user_id}' AND name = '{anomaly}'")
            record = self.c.fetchone()

            if record is None:
                self.c.execute("INSERT INTO apps (user_id, name, count) VALUES(?,?,?)",(user_id, anomaly, 1))
            else:
                self.c.execute(f"UPDATE apps SET count = '{record[2] + 1}' WHERE user_id = '{user_id}' AND name = '{anomaly}'") 
        
        elif field == "texts":
            self.c.execute(f"SELECT * FROM texts WHERE user_id = '{user_id}' AND topic = '{anomaly}'")
            record = self.c.fetchone()

            if record is None:
                self.c.execute("INSERT INTO texts (user_id, topic, count) VALUES(?,?,?)",(user_id, anomaly, 1))
            else:
                self.c.execute(f"UPDATE texts SET count = '{record[-1] + 1}' WHERE user_id = '{user_id}' AND topic = '{anomaly}'") 
        
        else:
            self.c.execute(f"UPDATE users SET ip_address = '{ip_addr}' WHERE username = '{user_id}'")
            self.conn.commit()
            buffer = str(len(f"ip_change>{user_id}>{ip_addr}")).rjust(5,"0")
            self.sock.send(buffer.encode())
            self.sock.send(f"ip_change>{user_id}>{ip_addr}".encode())
            

        self.c.execute(f"UPDATE anomalies SET is_anomaly = '0', handled = '1' WHERE user_id = '{user_id}' AND time = '{time}'")
        self.conn.commit()

        self.view_anomaly_data()


    def block_computer(self, anomaly_data):
        index = self.anomaly_table.indexAt(self.sender().pos())

        anomaly_data = anomaly_data[index.row()]
        
        time = anomaly_data[0]
        user_id = anomaly_data[1]
        ip_addr = anomaly_data[2]

        self.c.execute(f"UPDATE anomalies SET handled = '1' WHERE user_id = '{user_id}' AND time = '{time}'")
        self.c.execute(f"SELECT * FROM blocked_computers WHERE user_id = '{user_id}' AND ip_addr = '{ip_addr}'")
        computers = self.c.fetchall()

        if not computers:
            self.c.execute("INSERT INTO blocked_computers (user_id, ip_addr) VALUES(?,?)",(user_id, ip_addr))
        self.conn.commit()

        buffer = str(len(f"block {ip_addr}")).rjust(5,"0")

        self.sock.send(buffer.encode())
        self.sock.send(f"block {ip_addr}".encode())

        self.view_anomaly_data()
    

    def confirm_anomaly(self, anomaly_data):
        index = self.anomaly_table.indexAt(self.sender().pos())

        anomaly_data = anomaly_data[index.row()]

        time = anomaly_data[0]
        user_id = anomaly_data[1]
        ip_addr = anomaly_data[2]
        field = anomaly_data[3]
        anomaly = anomaly_data[4]

        self.c.execute(f"UPDATE anomalies SET handled = '1' WHERE user_id = '{user_id}' AND time = '{time}'")
        self.conn.commit()

        self.view_anomaly_data()


    # View currently blocked computers
    def view_blocked_computers(self):

        self.c.execute("SELECT * FROM blocked_computers")
        record = self.c.fetchall()

        self.block_table = QTableWidget(self)
        self.block_table.setRowCount(len(record))
        self.block_table.setColumnCount(3)

        # Set the column headers
        self.block_table.setHorizontalHeaderLabels(["User ID", "IP Address", "Unblock Computer"])

        # Add data to the table
        for i in range(self.block_table.rowCount()):

            item = QTableWidgetItem(record[i][0])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.block_table.setItem(i, 0, item)

            item = QTableWidgetItem(record[i][1])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make cell uneditable
            self.block_table.setItem(i, 1, item)

            button = QPushButton("Unblock")
            self.block_table.setCellWidget(i, 2, button)
            button.clicked.connect(lambda: self.unblock_computer(record))
        
        self.setCentralWidget(self.block_table)
    

    def unblock_computer(self, anomaly_data):
        index = self.block_table.indexAt(self.sender().pos())
        
        anomaly_data = anomaly_data[index.row()]

        ip_addr = anomaly_data[1]

        self.c.execute(f"DELETE FROM blocked_computers WHERE ip_addr = '{ip_addr}'")
        self.conn.commit()

        buffer = str(len(f"unblock {ip_addr}")).rjust(5,"0")

        self.sock.send(buffer.encode())
        self.sock.send(f"unblock {ip_addr}".encode())

        self.view_blocked_computers()

    