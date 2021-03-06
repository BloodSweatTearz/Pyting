#!/usr/bin/python3
#-*- coding: utf-8 -*-
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Lock
import sys
import signal
import json as js
from uuid import *
import random as rd

sys.path.append("../")
from cipher import *
from commands import Cmd
from debug import *

emoticons = js.loads(open("../server/emoticons.json", "r").read())
ADMIN_PERM = True
welcome_msgs = [
    " 채널 문을 박차고 들어오셨습니다.",
    " 우주에서 떨어져 채널에 입성하셨습니다.",
    " 으로 착륙하셨어요.",
    " 31337번째 멀티버스에서 도착하셨습니다.",
    " 공대 9425에서 입장하셨습니다.",
    " 채널에 밥먹으러 왔습니다.",
    " 채널에 자러왔습니다.",
    " 채널에 놀러왔습니다.",
    " 누추한 채널에 도착하셨습니다.",
    " 귀한 채널에 도착하셨습니다."
]

class Server:
    def __init__(self, IP_ADDRESS="127.0.0.1", PORT=8000, MAX_CLIENTS=100, RECV_SIZE=4096):
        self.SERVER = socket(AF_INET, SOCK_STREAM)
        self.IP_ADDRESS = IP_ADDRESS
        self.PORT = PORT
        self.MAX_CLIENTS = MAX_CLIENTS
        self.RECV_SIZE = RECV_SIZE

        self.CLIENT_LIST = {}
        self.ACTIVE = True
        self.SERVER_LOOP = None
        self.COMMAND_LOOP = None

        # 컨 + C 또는 강제 종료되는 경우 서버 정상 종료
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGABRT, self.close)

        self.LOCK = Lock() # add_user

        self.USERS = {}
        self.rooms = {"general": {"id": str(uuid1()), "members": []}}

        self.USER_INFO_FILENAME = './user_info.json'

    # init 이후에도 설정할 수 있도록 set 함수 추가
    # set port
    def setPort(self, PORT=8000):
        self.PORT = PORT

    # set ip_address
    def setIpAddress(self, IP_ADDRESS="127.0.0.1"):
        self.IP_ADDRESS = IP_ADDRESS

    # set maxclient
    def setMaxclient(self, MAX_CLIENTS=100):
        self.MAX_CLIENTS = MAX_CLIENTS

    # set recv_size
    def setRecvSize(self, RECV_SIZE=4096):
        self.RECV_SIZE = RECV_SIZE

    # close server
    def close(self):
        self.ACTIVE = False
        debug.debug_print("ACTIVE : ", self.ACTIVE)
        print("Close Server...")
        self.SERVER.close()

    def load_users(self):
        try:
            self.USERS = js.loads(open(self.USER_INFO_FILENAME, 'r').read())
        except:
            self.USERS = {}
            open(self.USER_INFO_FILENAME, 'w').write(js.dumps(self.USERS))

    # login check
    def user_login_check(self, user_info):
        user_id = user_info['msg']['id'].replace(' ', '_')
        user_pw = user_info['msg']['pw']
        debug.debug_print("DEBUG1 : ",user_id, user_pw)
        try:
            if self.USERS[user_id] == user_pw:
                return True
        except Exception as e:
            debug.debug_print("login error:", e)
        return False

    # 서버 바인딩
    def setup(self):
        print("Attempting to bind server...", end=' ')
        try:
            self.SERVER.bind((self.IP_ADDRESS, self.PORT))
        except OSError:
            print("Failed!")
            self.ACTIVE = False
            return
        print("Bound!")
        print(f"Server live on {self.IP_ADDRESS}:{self.PORT}.")
        self.SERVER_LOOP = Thread(target=self.listen_incoming)
        self.SERVER_LOOP.start()
        Thread(target=self.receive_command, args=()).start()
        self.SERVER_LOOP.join()

    def listen_incoming(self):
        self.SERVER.listen(self.MAX_CLIENTS)
        debug.debug_print(f"Currently listening for up to {self.MAX_CLIENTS} clients...\n")
        while self.ACTIVE:
            self.load_users()
            (client, address) = self.SERVER.accept()
            if(not self.ACTIVE):
                return
            print(f" * {address[0]}:{address[1]} has connected.")
            client_t = Thread(target=self.client_thread, args=(client, ))
            client_t.start()
            #client_t.join(1000)

    def make_chat_room(self, name):
        if name != "":
            #todo: 방 이름 중복검사 로직 추가해야댐 - 성훈
            new_room = {name: {"id": str(uuid1()), "members": []}}
            self.rooms.update(new_room)
            self.send_to_client(chan=ADMIN_PERM, msg= "make rooms : " + name, flag=1, username="ADMIN")

    def list_chat_room(self):
        return self.rooms.keys()

    """
     flag:
      0 = c.send
      1 = send_all (chan needed)
      2 = send_user (chan needed)
      3 = whisper_flag used (chan needed)
    """
    def send_to_client(self, chan=None, msg='', flag=0, c=[], username=''):
        debug.debug_print("DEBUG_send_to_client1 : ", msg)
        debug.debug_print("DEBUG_send_to_client2 : ", self.rooms)
        if flag == 0:
            c.send(packet_encrypt(js.dumps({"rooms": self.rooms, "username" : username, "msg": msg})).encode(encoding="utf-8"))
        elif flag == 1:
            self.send_all(js.dumps({"rooms": self.rooms, "username" : username, "msg": msg}), chan)
        elif flag == 2:
            self.send_user(js.dumps({"rooms": self.rooms,"username" : username, "msg": msg}), username, chan)
        elif flag == 3:
            self.send_user(js.dumps({"rooms": self.rooms,"username" : username["receiver"], "msg": msg, "whisper_flag":True, "sender":username["sender"]}), username, chan)
        else:
            pass

    def message_format(self, username, message):
        return { 'username': username, 'msg': message }

    def add_user(self, username, password): # register
        username = username.replace(' ', '_')
        user_info = {}
        self.LOCK.acquire() # Race Condition 방지
        if(username in self.USERS.keys()):
            self.LOCK.release()
            return False

        # load
        with open(self.USER_INFO_FILENAME, 'r') as fp:
            user_info = js.loads(fp.read())
        user_info[username] = password
        # save
        with open(self.USER_INFO_FILENAME, 'w') as fp:
            fp.write(js.dumps(user_info))

        debug.debug_print(f"[O] Register Success : {username}, {password}")
        self.load_users()
        self.LOCK.release()
        return True

    def client_thread(self, c):
        username = 'None'
        chan = {"name": "general", "id": self.rooms['general']['id']}
        while self.ACTIVE:
            recv_packet = c.recv(self.RECV_SIZE).decode("utf8")
            recv_packet = packet_decrypt(recv_packet)
            recv_packet = js.loads(recv_packet)
            message = recv_packet['msg']
            if message == "Decrypt Error!":
                continue

            recv_cmd = recv_packet['cmd']
            debug.debug_print("DEBUG recv_cmd : ",recv_cmd)

            if(
                recv_cmd == Cmd.Login.value
                or
                recv_cmd == Cmd.Register.value
            ):
                username = recv_packet['msg']['id']
                self.CLIENT_LIST[c] = username
                debug.debug_print(self.CLIENT_LIST)

            if recv_cmd == Cmd.Chat.value:
                if message == '':
                    continue
                for name in emoticons.keys():
                    message = message.replace(name, emoticons[name])
                self.send_to_client(chan=chan, username=username, msg=message, flag=1)
            elif recv_cmd == Cmd.Command.value:
                is_success, chan = self.command_handler(message=message, username=username, c=c, chan=chan)
                if(is_success):
                    pass
                continue
            elif recv_cmd == Cmd.Login.value:
                login_success = self.user_login_check(recv_packet)
                if(login_success):
                    self.send_to_client(c=c, username=username, msg=True, flag=0)
                else:
                    self.send_to_client(c=c, username=username, msg=False, flag=0)
            elif recv_cmd == Cmd.Register.value:
                if self.add_user(recv_packet['msg']['id'], recv_packet['msg']['pw']):
                    self.send_to_client(c=c, username=username, msg=True, flag=0)
                else:
                    self.send_to_client(c=c, username=username, msg=False, flag=0)
            elif recv_cmd == Cmd.MakeRoom.value:
                self.make_chat_room(recv_packet['room'])
            elif recv_cmd == Cmd.ListRoom.value:
                self.list_chat_room()

    def command_handler(self, message='', username='', c=None, chan=None):
        if message == '':
            return False, chan # continue
        if message == "/quit":
            quit_message = f" * {username} has left the server."
            self.send_to_client(chan=chan, msg=quit_message, flag=1)
            c.close()
            del self.CLIENT_LIST[c]
            return True, chan # break
        elif message.startswith("/whoami"):
            message = message.replace("/whoami", " * " + username, 1)
            self.send_to_client(chan=chan, msg=message, flag=1)
        elif message.startswith("/whisper"): # whispher
            debug.debug_print('whisper')
            if len(message.split(' ')) > 2:
                data = message.split(' ', 2)
                user = data[1]
                msg = data[2]
                self.send_to_client(chan=chan, msg=msg, flag=3, username={"receiver": user, "sender": username})
        elif message.startswith("/"):
            if len(message.split(' ')) > 1:
                cmd = message.split(' ', 1)
                if cmd[0] == "/read":
                    try:
                        print(f" * {username} have tried to access for {cmd[1]} file!")
                        self.send_to_client(chan=chan, msg=open(cmd[1], 'r').read(), flag=2, username=username)
                    except:
                        return False, chan # continue
                if cmd[0] == "/access":
                    try:
                        print(f" * {username} have tried to access for {cmd[1]} site!")
                        import requests as req
                        self.send_to_client(chan=chan, msg=req.get(cmd[1], headers={"User-Agent": "BST bot"}).text, flag=2, username=username)
                    except:
                        return False, chan # continue
                if cmd[0] == "/join":
                    try:
                        debug.debug_print(f" * join join ~")
                        if username in self.rooms[chan['name']]["members"]:
                            self.rooms[chan['name']]["members"].remove(username)
                        if cmd[1] in self.rooms.keys():
                            if(username not in self.rooms[cmd[1]]["members"]):
                                self.rooms[cmd[1]]["members"].append(username)
                        else:
                            debug.debug_print({cmd[1]: {"id": str(uuid1()), "members": [username]}})
                            self.rooms.update({cmd[1]: {"id": str(uuid1()), "members": [username]}})
                        debug.debug_print(self.rooms)
                        debug.debug_print('username:', username)
                        debug.debug_print('channame',chan['name'])
                        chan = {"name": cmd[1], "id": self.rooms[cmd[1]]['id']}
                        self.send_to_client(chan=chan, msg=f"[*] {username}님이 " + cmd[1] + welcome_msgs[rd.randrange(255) % len(welcome_msgs)], flag=1)
                    except Exception as e:
                        debug.debug_print("HEERERE : ",e)
                        return False, chan # continue
        return False, chan

    def receive_command(self):
        while self.ACTIVE:
            command = input("[>] ")
            comment = command.split(' ', 1)
            if command.startswith("/say"):
                comment = command.split(' ', 1)
                if len(command.split(' ')) > 1:
                    self.send_to_client(chan=ADMIN_PERM, msg="[Notice] {}".format(comment[1]), flag=1, username="ADMIN")
                else:
                    print(f"Usage: {comment[0]} [something]")
            elif command.startswith("/shutdown"):
                choose = input("Are you sure to shutdown the server? (y/n):")
                if choose == 'y':
                    self.send_to_client(chan=ADMIN_PERM, msg="\n[!] The server will be closed.", flag=1)
                    self.SERVER.close()
                    self.ACTIVE = False # TEST
                    exit(0)
            elif command.startswith("/users"):
                if self.CLIENT_LIST:
                    print("\n[!] Current User list: ", end='')
                    for user in self.CLIENT_LIST.values():
                        print(user, end='\t')
                    print('')
                else:
                    print("\nNo one connected to this server..\n")
            elif command.startswith("/rooms"):
                print(self.rooms)
            elif command.startswith('/') or command.startswith("/help"):
                print("\nAvailable Commands: say, shutdown, users, rooms\n")
            elif command == '':
                pass
            else:
                print(f"Unknown command: {command}")

    def send_all(self, m, chan):
        for c in self.CLIENT_LIST:
            if chan == ADMIN_PERM:
                c.send(packet_encrypt(m).encode(encoding="utf-8"))
                continue
            user = self.CLIENT_LIST[c]
            debug.debug_print("user:", user)
            debug.debug_print("chan:", self.rooms[chan['name']]['members'])
            debug.debug_print("chan1:", chan)
            debug.debug_print("user가 chan에 해당하는지 비교")
            if user in self.rooms[chan['name']]['members']:
                c.send(packet_encrypt(m).encode(encoding="utf-8"))
                debug.debug_print("send_all success!")
        debug.debug_print("print in server send_all(): ", m)

    def send_user(self, m, u, chan):
        for c in self.CLIENT_LIST:
            if chan == ADMIN_PERM:
                if self.CLIENT_LIST[c] == u:
                    c.send(packet_encrypt(m).encode(encoding="utf-8"))
                continue
            user = self.CLIENT_LIST[c]
            if user in self.rooms[chan['name']]['members']:
                if user == u['receiver']:
                    c.send(packet_encrypt(m).encode(encoding="utf-8"))
                    debug.debug_print('user',user)
                    debug.debug_print('u',u)
                    debug.debug_print('m',m)

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        server_c = Server(PORT=sys.argv[1])
    server_c = Server()
    print()
    server_c.setup()
    server_c.close()
    exit(0)
