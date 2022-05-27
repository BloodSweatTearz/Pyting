#!/usr/bin/python3
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from getpass import getpass
import time
import sys
import signal
import json
import sys 

sys.path.append("../")
from cipher import *

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
        self.CURRENT_ROOM = -1 

        # 접속 중인 방의 유저 리스트
        self.USERLIST = []

    def setup(self):
        print("Attempting to connect to server...", end=' ')
        try:
            self.CLIENT.connect((self.IP_ADDRESS, self.PORT))
        except ConnectionRefusedError:
            print("Failed!\n")
            self.ACTIVE = False
            return
        print("Connected!")
        print("All packets through this chat are interacting by specific encryption.")
        print(f"Client connected to server at {self.IP_ADDRESS}.")

        # 컨 + C 또는 강제 종료되는 경우 서버 정상 종료
        signal.signal(signal.SIGINT, self.CLIENT.close)
        signal.signal(signal.SIGABRT, self.CLIENT.close)

    def start_io_loop(self):
        if self.ACTIVE:
            self.RECEIVE_THREAD = Thread(target=self.print_message)
            self.SEND_THREAD = Thread(target=self.send_message)
            self.RECEIVE_THREAD.start()
            self.SEND_THREAD.start()
            self.RECEIVE_THREAD.join()
            self.SEND_THREAD.join()

    # 로그인
    def login(self):
        username = input("\nEnter username: ")
        password = getpass("Enter password: ")
        if(self.login_check(username, password)): # 참이면 로그인 정보 확인(성공)
            self.USERNAME = username
            self.PASSWORD = password
            return True
        else: # 로그인 실패
            print("[!] USER INFO HAS NONE. PLZ REGISETER FIRST.")
            return False

    # 로그인(테스트용)
    # 서버에 login 기능이 없기 때문에 만듦
    def login_test(self):
        self.USERNAME = input("\nEnter username: ")
        self.PASSWORD = getpass("Enter password: ")
        

    # 로그인 체크
    def login_check(self, username, password):
        # send info
        info = {"id":username, "pw":password}
        send_packet = self.dtoj(2, info) # 주의! info는 딕셔너리임. "msg":info
        self.CLIENT.send(packet_encrypt(send_packet).encode(encoding='utf-8'))

        # recv result
        info_result = self.receive_message()
        print("WHAT????:",info_result)

        if(info_result['msg'] == True): # msg가 참이면 로그인 성공
            return True
        return False
        # return info_result['msg']

    # 회원가입
    def register(self, username, password):
        # send info
        info = {"id":username, "pw":password}
        send_packet = self.dtoj(3, info) # 주의! info는 딕셔너리임. "msg":info
        self.CLIENT.send(bytes(packet_encrypt(send_packet), "utf8"))

        # recv result
        info_result = self.receive_message()
        if(info_result['msg'] == True): # msg가 참이면 회원가입 성공
            print("[O] Register Success!")
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
            print("현재 위치 저장 실패")

        # if(recv_packet['rooms']["current_room_uuid"] != -1):
        #     self.USERLIST = recv_packet["members"]
        if(self.CURRENT_ROOM != -1):
            self.USERLIST = recv_packet['rooms'][self.CURRENT_ROOM]['members']

    # data to json
    def dtoj(self, cmd, msg):
        return json.dumps({"username": self.USERNAME, "room_uuid":self.CURRENT_ROOM, "cmd":cmd, "msg":msg})
        
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
    def send_message(self):
        print()
        while self.ACTIVE:
            try:
                message = input(f"{self.USERNAME}: ")
                if message == "/quit":
                    self.ACTIVE = False
                else:
                    # msg to json
                    ## cmd = 1
                    send_packet = None
                    if(message.startswith('/')):
                        send_packet = self.dtoj(1, message)
                    ## cmd = 0
                    else:
                        send_packet = self.dtoj(0, message)
                self.CLIENT.send(bytes(packet_encrypt(send_packet), "utf8"))
            except:
                print("Exception Detected!")
                self.ACTIVE = False
                self.CLIENT.send(bytes(packet_encrypt("/quit")))
                import os
                os._exit(13)
    
    def receive_message(self):
        try:
            message = self.CLIENT.recv(self.RECV_SIZE).decode("utf8")
            message = packet_decrypt(message)
            message = self.jtod(message) # 받은 json을 data로 변경
            if(message["msg"] == "Decrypt Error!"):
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
    
    def print_message(self):
        while(self.ACTIVE):
            print(self.receive_message()['msg'])    

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
    print()
    client = Client()
    # client.login_test()
    client.run_client()
    exit(0)
