import os
import sys
import torch
from PyQt5 import uic
from PyQt5 import QtSql
from PyQt5.QtWidgets import QLabel, QApplication, QLineEdit
from PyQt5.QtWidgets import QPushButton, QMainWindow, QStackedWidget, QDesktopWidget
from db import login, signup, user_exists

from main import WirelessExtraction


class LoginWindow(QMainWindow):
    def __init__(self):
        super(LoginWindow, self).__init__()
        uic.loadUi("./ui/login.ui", self)
        screen = QDesktopWidget().screenGeometry()
        self.create_connection()
        self.model_path = os.path.join(os.getcwd(), 'weights', 'best.pt')
        self.model = torch.hub.load(
            'ultralytics/yolov5', 'custom', self.model_path)  # custom trained model

        # pages
        self.page_controller = self.findChild(
            QStackedWidget, 'login_signup_stack')
        self.login_page_index = 0
        self.signup_page_index = 1

        self.signup_page_btn = self.findChild(QPushButton, 'signup_page_btn')
        self.login_page_btn = self.findChild(QPushButton, 'login_page_btn')

        self.signup_page_btn.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.signup_page_index))
        self.login_page_btn.clicked.connect(
            lambda: self.page_controller.setCurrentIndex(self.login_page_index))

        # Login data
        self.username_login = self.findChild(QLineEdit, 'username_login')
        self.username_login.setPlaceholderText("Username")
        self.password_login = self.findChild(QLineEdit, 'password_login')
        self.password_login.setPlaceholderText("Password")
        self.password_login.setEchoMode(QLineEdit.Password)
        self.login_status = self.findChild(QLabel, 'status_login')
        self.login_btn = self.findChild(QPushButton, 'login')
        self.login_btn.clicked.connect(self.login_user)

        # Sign up data
        self.username_signup = self.findChild(QLineEdit, 'username_signup')
        self.username_signup.setPlaceholderText("Username")
        self.email = self.findChild(QLineEdit, 'email')
        self.email.setPlaceholderText("Email")
        self.password_signup = self.findChild(QLineEdit, 'password_signup')
        self.password_signup.setPlaceholderText("Password")
        self.password_signup.setEchoMode(QLineEdit.Password)
        self.confirm_password = self.findChild(QLineEdit, 'confirm_password')
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.signup = self.findChild(QPushButton, 'signup')
        self.signup_status = self.findChild(QLabel, 'status_signup')
        self.signup.clicked.connect(self.signup_user)

    def create_connection(self):
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("data.sqlite")
        if not self.db.open():
            print("Error")
        self.query = QtSql.QSqlQuery()

    def login_user(self):
        self.username = self.username_login.text()
        password = self.password_login.text()

        status = login(self.query, self.username, password)
        # if not status:
        #     return self.set_login_status(
        #         "Login Failed!",
        #         "Invalid email or password. Please try again",
        #         "color: red; font-weight: bold;",
        #         True,
        #     )
        status = self.set_login_status(
            "Login Successful!",
            "Login Successful!",
            "color: green; font-weight: bold;",
            True,
        )
        self.main_window = WirelessExtraction(
            self.model, self.query.value("id"))
        self.close()
        self.main_window.show()

    # TODO Rename this here and in `login_user`
    def set_login_status(self, status, text, style, output):
        print(status)
        self.login_status.setText(text)
        self.login_status.setStyleSheet(style)
        return output

    def signup_user(self):
        print("Signing Up user...")
        username = self.username_signup.text()
        password = self.password_signup.text()
        confirm = self.confirm_password.text()
        email = self.email.text()
        if username is None or password is None or confirm is None or email is None:
            print("Please enter all the details.")
            self.signup_status.setText("Please enter all the details.")
            self.signup_status.setStyleSheet("color: red; font-weight: bold;")
            return False

        if user_exists(self.query, username):
            self.signup_status.setText(
                "A user with that username already exists.")
            self.signup_status.setStyleSheet("color: red; font-weight: bold;")
            return False

        if password != confirm:
            print("Password and Confirm Password doesn't match")
            self.signup_status.setText(
                "Passwords do not match. Please try again.")
            self.signup_status.setStyleSheet("color: red; font-weight: bold;")
            return False

        signup(self.query, username, email, password)

        print("User created successfully")
        self.signup_status.setText(
            "Sign Up Successful! Please login to continue. ")
        self.signup_status.setStyleSheet("color: green; font-weight: bold;")

        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = LoginWindow()
    w.show()
    sys.exit(app.exec_())
