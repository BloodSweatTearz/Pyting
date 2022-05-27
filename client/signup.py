from PyQt5.QtWidgets import QWidget, QDialog

from ui.pytingUI import signupForm, center, fix_window_size


class signup_window(QDialog, QWidget, signupForm):
    def __init__(self):
        super(signup_window, self).__init__()
        self.setupUi(self)
        self.show()
        center(self)
        fix_window_size(self, 175, 175)


