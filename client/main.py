import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit
from qt_material import apply_stylesheet

from lobby import lobby_window
from signup import signup_window
from ui.pytingUI import *

from client import Client

myVersion = "1.0.0"

DEBUG = True

def debug_print(msg):
    global DEBUG
    if DEBUG:
        print("DEBUG:",msg)

class login_class(QMainWindow, loginForm):
    def __init__(self, Client):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.show()
        center(self)
        fix_window_size(self, 350, 350)

        self.pw.setEchoMode(QLineEdit.Password)
        self.setWindowTitle("Pyting v{}".format(myVersion))
        self.loadLogo()
        self.registerBtn.clicked.connect(self.signup_event)
        self.loginBtn.clicked.connect(self.login_event)

        self.CLIENT = Client
        self.CLIENT.setup()
    
    def loadLogo(self):
        self.qPixmapFileVar = QPixmap()
        self.qPixmapFileVar.load("./imgResource/pyting_Compact.png")
        self.qPixmapFileVar = self.qPixmapFileVar.scaledToWidth(self.mainlogo.width())
        self.mainlogo.setPixmap(self.qPixmapFileVar)

    def signup_event(self):
        self.hide()
        self.signup_window = signup_window(self.CLIENT)
        self.signup_window.exec()
        self.show()

    def login_event(self):
        id = self.id.text()
        pw = self.pw.text()
        if (id == "") or (pw == ""):
            QMessageBox.about(self, "error", 'plz input id pw :(')
            return

        is_success = CLIENT.login_check(id, pw)
        debug_print(is_success)
        if is_success:
            self.hide()
            self.lobby_window = lobby_window(self.CLIENT)
            self.lobby_window.mynamelabel.setText("hello, {}".format(id))
            self.lobby_window.exec()
        else:
            self.CLIENT.reconnect()
            QMessageBox.about(self, "error", 'login Failed :(')
            
if __name__ == "__main__":
    SERVER_IP = "localhost"
    SERVER_PORT = 8000
    CLIENT = Client(IP_ADDRESS=SERVER_IP, PORT=SERVER_PORT)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    apply_stylesheet(app, theme='dark_blue.xml')

    window = login_class(CLIENT)
    app.exec_()
