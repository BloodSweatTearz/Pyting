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
        username = self.id_4.text()
        pw = self.pw.text()
        pw_re = self.pw_re.text()

        if(pw == pw_re):
            is_success = self.CLIENT.register(username, pw)
            print("DEBUG register : ",is_success)
            if(is_success):
                QMessageBox.about(self, "Register", 'Register Success!')    
                self.CLIENT.reconnect()
                return                
        QMessageBox.about(self, "Register", 'Register Failed :(')
        self.CLIENT.reconnect()
        return

