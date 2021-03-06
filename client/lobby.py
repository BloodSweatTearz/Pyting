#-*- coding: utf-8 -*-
import functools
import re
import sys

from PyQt5.QtGui import QPixmap, QColor, QTextCursor
from PyQt5.QtWidgets import QWidget, QDialog, QListWidgetItem, QMessageBox
from ui.pytingUI import lobbyForm, center, fix_window_size

sys.path.append("../")
from cipher import *
from server.server import emoticons
from debug import *

class lobby_window(QDialog, QWidget, lobbyForm):
    cmd = [ # command, parameter, detail tips
            ["help", "", "You can get some tips."],
            ["join", "room", "You can join room with command."],
            ["whisper", "nickname", "You can tell users secretly."],
            ["whoami", "", "Who are you? I'll let you know who you are. :>"]
    ]

    enable_cmd_tooltip = False

    def __init__(self, Client):
        super(lobby_window, self).__init__()
        self.setupUi(self)
        self.show()
        self.form_size(0)
        center(self)

        #Event Mapping
        self.makeChatEdit.returnPressed.connect(self.makeChat)
        self.chatEdit.returnPressed.connect(self.sendChat)

        self.roomlist.doubleClicked.connect(self.connectRoom)

        self.createChatBtn.clicked.connect(self.makeChat)
        self.exitBtn.clicked.connect(self.exitRoom)

        #Load Refresh Icon
        self.qPixmapFileVar = QPixmap()
        self.qPixmapFileVar.load("./imgResource/refresh.png")
        self.qPixmapFileVar = self.qPixmapFileVar.scaledToWidth(self.refreshImg.width())
        self.refreshImg.setPixmap(self.qPixmapFileVar)

        #Refresh는 이미지라 Clicked지원 안해서 이렇게 매핑
        self.refreshImg.mousePressEvent = functools.partial(self.refreshRoomList)
        self.chatEdit.textChanged.connect(self.commandHelper)

        self.CLIENT = Client
        self.CLIENT.start_io_loop(self)

    def create_dummy(self):
        pass

    def makeChat(self):
        chan_name = self.makeChatEdit.text()
        if chan_name == '':
            QMessageBox.about(self, "Channel Name", 'Please type channel name!')
            return
        self.chatEdit.setText("/join {}".format(chan_name))
        self.sendChat()
        self.makeChatEdit.clear()
        self.sendChat()
        self.chatEdit.setText("")

        self.form_size(1)
        self.roomlist.clearSelection()
        self.roomlist.clearFocus()

        self.chatWidget.scrollToBottom()

    def refreshRoomList(self, event):
        self.roomlist.clear()
        res = self.CLIENT.get_room_list()
        from PyQt5.QtWidgets import QListWidgetItem
        for room in res:
            room_item = QListWidgetItem(room)
            self.roomlist.addItem(room_item)

    def connectRoom(self):
        room_name = self.roomlist.currentItem().text()
        self.chatEdit.setText("/join {}".format(room_name))
        self.sendChat()
        self.chatEdit.setText("")

        self.form_size(1)
        self.roomlist.clearSelection()
        self.roomlist.clearFocus()

    def sendChat(self):
        sysCmd = self.chat_can_command()
        if sysCmd is None:
            #채팅 보내면 됨.
            message = self.chatEdit.text()
            if message == '':
                return
            self.CLIENT.send_message(message)
            for name in emoticons.keys():
                message = message.replace(name, emoticons[name])
            self.drawChat("me", message)
        elif (sysCmd is not None) and (self.chatEdit.text().find(sysCmd[0]) == 1):
            #채팅이 아니라 명령어 실행
            parameter = self.chatEdit.text().split(' ')
            if sysCmd[0] == "join" and parameter[1] is not None:
                self.mynamelabel.setText("hi, {}\n you are on channel {}".format(self.CLIENT.USERNAME, parameter[1]))
                self.CLIENT.send_message(self.chatEdit.text())
            elif sysCmd[0] == "help":
                command = QListWidgetItem("----chatting command helper----")
                self.chatWidget.addItem(command)
                for command in self.cmd:
                    command = QListWidgetItem("/{} {} - {}".format(command[0], command[1], command[2]))
                    self.chatWidget.addItem(command)
                command = QListWidgetItem("-----------------------------------------------")
                self.chatWidget.addItem(command)
            elif sysCmd[0] == "whoami":
                command = QListWidgetItem("----you are {}----".format(self.CLIENT.USERNAME))
                self.chatWidget.addItem(command)
            elif sysCmd[0] == "whisper":
                message = self.chatEdit.text()
                data = message.split(' ', 2)
                user = data[1]
                msg = data[2]
                self.CLIENT.send_message(message)
                self.drawChat(f"me->{user}", msg)
            else:
                self.CLIENT.send_message(self.chatEdit.text())
        self.chatEdit.clear()
        self.chatWidget.scrollToBottom()

    def exitRoom(self):
        self.chatWidget.clear()
        self.chatEdit.clear()
        self.memberList.clear()
        self.form_size(0)

    def drawChat(self, sender, msg):
        chatItem = QListWidgetItem("[{}] {}".format(sender, msg))
        self.chatWidget.addItem(chatItem)
        self.memberList.clear()
        users = self.CLIENT.USERLIST
        for user in users:
            memberItem = QListWidgetItem(user)
            self.memberList.addItem(memberItem)
        self.chatWidget.scrollToBottom()

    def chat_can_command(self):
        #return Command List
        p = re.compile('(/[a-zA-Z]*)')
        chat_can_command = re.match(p, self.chatEdit.text())
        if chat_can_command:
            user_command = chat_can_command.group(1)[1:len(chat_can_command.group(1))]
            for sysCmd in self.cmd:
                if sysCmd[0] == user_command:
                    return sysCmd
                if sysCmd[0].find(user_command) == 0:
                    return sysCmd

    def commandHelper(self):
        sysCmd = self.chat_can_command()

        if sysCmd == None:
            self.enable_cmd_tooltip = False
            self.cmdHelper.move(10000, 10000)
        else :
            self.cmdHelper.setPlainText("")

            colorvar = QColor(255, 200, 0)
            self.cmdHelper.setTextColor(colorvar)
            self.cmdHelper.setText("/" + sysCmd[0])

            self.cmdHelper.moveCursor(QTextCursor.End)
            self.cmdHelper.insertPlainText("  ")
            self.cmdHelper.moveCursor(QTextCursor.End)

            colorvar = QColor(255, 255, 255)
            self.cmdHelper.setTextColor(colorvar)
            self.cmdHelper.insertPlainText(sysCmd[1])

            self.cmdHelper.moveCursor(QTextCursor.End)
            self.cmdHelper.insertPlainText("  ")
            self.cmdHelper.moveCursor(QTextCursor.End)

            colorvar = QColor(128, 128, 128)
            self.cmdHelper.setTextColor(colorvar)
            self.cmdHelper.insertPlainText(sysCmd[2])

            self.cmdHelper.move(250, 330)

    def form_size(self, set):
        # formsize(0) == only Lobby
        # formsize(1) == extened Chatting
        if set == 0:
            fix_window_size(self, 240, 450)
        if set == 1:
            fix_window_size(self, 800, 450)

    def closeEvent(self, QCloseEvent):
        '''
        re = QMessageBox.question(self, "종료 확인", "종료 하시겠습니까?",
                    QMessageBox.Yes|QMessageBox.No)

        if re == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()
        '''
        self.CLIENT.ACTIVE = False
        self.CLIENT.disconnect()
