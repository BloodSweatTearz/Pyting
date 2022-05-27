from PyQt5.QtWidgets import QWidget, QDialog, QMessageBox

from ui.pytingUI import signupForm, center, fix_window_size

class signup_window(QDialog, QWidget, signupForm):
    def __init__(self, Client):
        self.CLIENT = Client

        super(signup_window, self).__init__()
        self.setupUi(self)
        self.show()
        center(self)
        fix_window_size(self, 175, 175)

        self.registerBtn.clicked.connect(self.register)

    def register(self):
        username = self.id_5.text()
        pw = self.pw.text()
        pw_re = self.pw_re.text()

        if(pw == pw_re):
            if(self.CLIENT.register(username, pw)):
                QMessageBox.about(self, "error", 'Register Success!')    
                return True                
        QMessageBox.about(self, "error", 'Register Failed :(')
        return False

