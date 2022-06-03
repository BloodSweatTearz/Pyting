#!/usr/bin/python3
#-*- coding: utf-8 -*-
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from getpass import getpass
import hashlib
import signal
import time
import json
import sys

sys.path.append("../")
from cipher import *
from commands import Cmd
from debug import *

class Client:
    def __init__(self, IP_ADDRESS="127.0.0.1", PORT=8000, RECV_SIZE=4096):
        self.CLIENT = socket(AF_INET, SOCK_STREAM)
        self.IP_ADDRESS = IP_ADDRESS
        self.PORT = PORT
        self.RECV_SIZE = RECV_SIZE

        self.ACTIVE = True
        self.RECEIVE_THREAD = None
        self.SEND_THREAD = None

        # user info
        self.USERNAME = ''
        self.PASSWORD = ''

        # 모든 방 리스트
        # {ROOM_NAME:{"UUID":"", "MEMBERS":[]}, ...}
        self.ROOMS = {}

        # 내가 접속중인 방
        # default : -1 : 아무 방에도 접속 중이지 않음
        # value : ROOM_UUID
        self.DEFAULT_CHANNEL_NAME = "general"
        self.CURRENT_ROOM = -1

        # 접속 중인 방의 유저 리스트
        self.USERLIST = []

    def setup(self):
        print("Attempting to connect to chat server...", end=' ')
        try:
            self.CLIENT.connect((self.IP_ADDRESS, self.PORT))
        except ConnectionRefusedError:
            print("Failed..\n")
            self.ACTIVE = False
            return
        print("Connected!!")
        print("All packets through this chat are interacting by specific encryption.")

        # 컨 + C 또는 강제 종료되는 경우 서버 정상 종료
        signal.signal(signal.SIGINT, self.CLIENT.close)
        signal.signal(signal.SIGABRT, self.CLIENT.close)

    def start_io_loop(self, lobbyForm):
        if self.ACTIVE:
            self.RECEIVE_THREAD = Thread(target=self.print_message, args=(lobbyForm, ))
            self.RECEIVE_THREAD.start()
            #self.RECEIVE_THREAD.join()

    # 로그인 체크
    def login_check(self, username, password):
        password = hashlib.sha512(password.encode()).hexdigest()
        # send info
        info = {"id":username, "pw":password}
        send_packet = self.dtoj(Cmd.Login, info) # 주의! info는 딕셔너리임. "msg":info
        self.CLIENT.send(packet_encrypt(send_packet).encode(encoding='utf-8'))

        # recv result
        info_result = self.receive_message()
        #self.CURRENT_ROOM = info_result["rooms"]["general"]["id"]
        self.CURRENT_ROOM = self.DEFAULT_CHANNEL_NAME

        #todo : draw member by info_result["rooms"]["general"]["members"] dict

        if(info_result['msg'] == True): # msg가 참이면 로그인 성공
            self.USERNAME = username
            self.PASSWORD = password
            return True
        return False
        # return info_result['msg']

    # 회원가입
    def register(self, username, password):
        password = hashlib.sha512(password.encode()).hexdigest()
        # send info
        info = {"id":username, "pw":password}
        send_packet = self.dtoj(Cmd.Register, info) # 주의! info는 딕셔너리임. "msg":info
        self.CLIENT.send(bytes(packet_encrypt(send_packet), "utf8"))

        # recv result
        info_result = self.receive_message()
        if(info_result['msg'] == True): # msg가 참이면 회원가입 성공
            debug_print("[O] Register Success!")
            return True
        return False

    # 현재 위치 저장
    def where_am_i(self, recv_packet):
        rooms_raw = recv_packet['rooms']
        try:
            for channal_name in rooms_raw.keys():
                if self.USERNAME in rooms_raw[channal_name]['members']:
                    self.CURRENT_ROOM = channal_name
                    return True
            return False
        except:
            return False

    # 룸 정보 초기화
    def room_list_refresh(self, recv_packet):
        self.ROOMS = recv_packet["rooms"]

    # 룸 유저정보 초기화
    def room_member_list_refresh(self, recv_packet):
        if not self.where_am_i(recv_packet):
            debug_print("현재 위치 저장 실패")

        # if(recv_packet['rooms']["current_room_uuid"] != -1):
        #     self.USERLIST = recv_packet["members"]
        if(self.CURRENT_ROOM != -1):
            self.USERLIST = recv_packet['rooms'][self.CURRENT_ROOM]['members']

    # data to json
    def dtoj(self, cmd, msg):
        if cmd.value is None:
            debug_print("[dtoj] Error, cmd value is None")
            return ""
        return json.dumps({"username": self.USERNAME, "room_uuid": self.CURRENT_ROOM, "cmd": cmd.value, "msg": msg})

    # json to data
    def jtod(self, packet):
        return json.loads(packet)

    # cmd {
    #  0 : send message
    #  1 : send command
    #  2 : login info
    #  3 : register info
    # }
    # msg {
    #  if cmd == 0 :
    #    msg : message
    #  if cmd == 1 :
    #    msg : command
    #  if cmd == 2 :
    #    msg : {id:"",pw:""}
    #  if cmd == 3 :
    #    msg : {id:"",pw:""}
    # }

    def send_message(self, message):
        if self.CURRENT_ROOM == -1:
            debug_print("[send_message] Error, WHERE ROOM?")
            return
        # try:
        send_packet = None
        if message == "/quit":
            self.ACTIVE = False
        else:
            if message.startswith('/'):
                send_packet = self.dtoj(Cmd.Command, message)
            else:
                send_packet = self.dtoj(Cmd.Chat, message)
        self.CLIENT.send(bytes(packet_encrypt(send_packet), "utf8"))
        # except:
        #     debug_print("Exception Detected!")
        #     self.ACTIVE = False
        #     self.CLIENT.send(bytes(packet_encrypt("/quit")))
        #     import os
        #     os._exit(13)

    def receive_message(self):
        try:
            self.CLIENT.settimeout(1)
            try:
                message = self.CLIENT.recv(self.RECV_SIZE).decode("utf8")
            except Exception as e: # socket.timeout
                #debug_print("RECV TIMEOUT!!! : ",e) # reset
                self.CLIENT.settimeout(None)
                return {'msg' : "Decrypt Error!"}
            self.CLIENT.settimeout(None) # reset

            #debug_print("DEBUG[message] :",message)
            message = packet_decrypt(message)
            message = self.jtod(message) # 받은 json을 data로 변경
            if(message["msg"] == "Decrypt Error!"):
                self.ACTIVE = False
                return message
            '''
                {
                    "rooms":{
                        "general":{
                            "id":"d343e3f4-dc36-11ec-9241-0242ac110002",
                            "members":[
                                "{\"username\": \"\", \"room_uuid\": -1, \"cmd\": 0, \"msg\": \"hellow\"}",
                                "{\"username\": \"asdf\", \"room_uuid\": -1, \"cmd\": 0, \"msg\": \"helloo\"}",
                            ]
                        }
                    },
                    "msg":" * You have connected to the server at 127.0.0.1."
                }
            '''
            self.room_list_refresh(message)
            self.room_member_list_refresh(message)
            return message
        except OSError:
            self.ACTIVE = False

    def get_room_list(self):
        res = []
        for room in self.ROOMS.keys():
            res.append(room)
        return res

    def print_message(self, lobbyForm):
        while self.ACTIVE:
            packet_data = self.receive_message()
            if(
                packet_data == None
                or
                packet_data['msg'] == "Decrypt Error!"
            ):
                continue

            if("whisper_flag" in packet_data):
                from PyQt5.QtWidgets import QListWidgetItem
                item = QListWidgetItem('<{}->me> {}'.format(packet_data["sender"], packet_data["msg"]))
                lobbyForm.chatWidget.addItem(item)
                lobbyForm.chatWidget.scrollToBottom()
                continue

            if packet_data["username"] != self.USERNAME:
                from PyQt5.QtWidgets import QListWidgetItem
                item = QListWidgetItem('[{}] {}'.format(packet_data["username"], packet_data["msg"]))
                lobbyForm.chatWidget.addItem(item)
                lobbyForm.chatWidget.scrollToBottom()
            lobbyForm.chatWidget.scrollToBottom()

    def run_client(self):
        self.setup()
        if(self.login()): # 참이면 로그인 성공
            self.start_io_loop()
            self.CLIENT.close()
        self.CLIENT.close()

    def reconnect(self):
        self.CLIENT.close()
        ip_address = self.IP_ADDRESS
        port = self.PORT
        recv_size = self.RECV_SIZE
        self.__init__(IP_ADDRESS=ip_address, PORT=port, RECV_SIZE=recv_size)
        self.setup()

    def disconnect(self):
        self.CLIENT.close()

# test
if __name__ == "__main__":
    client = Client()
    client.login_test()
    client.run_client()
    client.receive_message()
    exit(0)
