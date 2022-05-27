from PyQt5 import uic
from PyQt5.QtWidgets import QDesktopWidget

loginForm = uic.loadUiType("./ui/login.ui")[0]
signupForm = uic.loadUiType("./ui/signup.ui")[0]
lobbyForm = uic.loadUiType("./ui/lobby.ui")[0]
forgotpwForm = uic.loadUiType("./ui/forgotpw.ui")[0]

def center(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())

def fix_window_size(self, x, y):
    self.resize(x, y)
    self.setMaximumSize(x, y)
    self.setMinimumSize(x, y)