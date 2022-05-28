#!/usr/bin/python3
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread, Lock
import sys
import signal
import json as js
from uuid import *

sys.path.append("../")
from cipher import *
from commands import Cmd

emoticons = js.loads(open("emoticons.json", "r").read())
#rooms = {"하이": {"id": str(uuid1()), "members": []}}
rooms = {"general": {"id": str(uuid1()), "members": []}}
users = { "asdf": "1234" , "pang": "1234", "qwer": "1234"}
ADMIN_PERM = True

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
        print("ACTIVE : ", self.ACTIVE)
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
        user_id = user_info['msg']['id']
        user_pw = user_info['msg']['pw']
        print("DEBUG1 : ",user_id, user_pw)
        try:
            if self.USERS[user_id] == user_pw:
                return True
        except Exception as e:
            print("login error:", e)
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
        print(f"Currently listening for up to {self.MAX_CLIENTS} clients...\n")
        while self.ACTIVE:
            self.load_users()
            (client, address) = self.SERVER.accept()
            if(not self.ACTIVE):
                return
            print(f" * {address[0]}:{address[1]} has connected.")
            client_t = Thread(target=self.client_thread, args=(client, ))
            client_t.start()
            client_t.join(1000)

    def make_chatting_room(self, name):
        if name != "":
            #todo: 방 이름 중복검사 로직 추가해야댐 - 성훈
            new_room = {name: {"id": str(uuid1()), "members": []}}
            self.rooms.update(new_room)
            print("DEBUG_make_chatting_room : ",name)
            self.send_to_client(ADMIN_PERM, msg= "make rooms : " + name, flag=1, username="ADMIN")
            print("[make_chatting_room] Chatting Room created : ", new_room)
        else:
            print("[make_chatting_room] Chatting Room name is empty.")

    def list_chatting_room(self):
        print("[list_chatting_room] return ", rooms.keys())
        return rooms.keys()


    """
     flag:
      0 = c.send
      1 = send_all (chan needed)
      2 = send_user (chan needed)
    """
    def send_to_client(self, chan='', msg='', flag=0, c=[], username=''):
        print("DEBUG_send_to_client1 : ",msg)
        print("DEBUG_send_to_client2 : ",rooms)
        if flag == 0:
            c.send(packet_encrypt(js.dumps({"rooms": rooms, "username" : username, "msg": msg})).encode(encoding="utf-8"))
        elif flag == 1:
            self.send_all(js.dumps({"rooms": rooms, "username" : username, "msg": msg}), chan)
        elif flag == 2:
            self.send_user(js.dumps({"rooms": rooms,"username" : username, "msg": msg}), username, chan)
        elif flag == 3: #makeRoom Alert
            self.send_all(msg, chan)

        else:
            pass

    def message_format(self, username, message):
        return { 'username': username, 'msg': message }

    # password는 아직은 평문
    def add_user(self, username, password): # register
        
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

        print(f"[O] Register Success : {username}, {password}")
        self.load_users()
        self.LOCK.release()
        return True

    def client_thread(self, c):
        if(not self.ACTIVE):
            return
        recv_packet = c.recv(self.RECV_SIZE).decode("utf8")
        recv_packet = packet_decrypt(recv_packet)
        recv_packet = js.loads(recv_packet)
        print("recv_packet:" ,recv_packet) # test
        chan = {"name": "general", "id": str(uuid1())}
        username = recv_packet['msg']['id']
        self.CLIENT_LIST[c] = username

        recv_cmd = recv_packet['cmd']
        print("DEBUG recv_cmd : ",recv_cmd)

        user_string = "<" + username + "> "
        private_string = "[" + username + "] "
        welcome_message = f" * You have connected to the server at {self.IP_ADDRESS}."

        if recv_cmd == Cmd.Login.value:
            login_success = self.user_login_check(recv_packet)
            if(login_success):
                self.rooms["general"]["members"].append(username)
                self.send_to_client(c=c, username=username, msg=True, flag=0)
            else:
                self.send_to_client(c=c, username=username, msg=False, flag=0)
                return
        elif recv_cmd == Cmd.Register.value:
            if self.add_user(recv_packet['msg']['id'], recv_packet['msg']['pw']):
                self.send_to_client(c=c, username=username, msg=True, flag=0)
            else:
                self.send_to_client(c=c, username=username, msg=False, flag=0)
                #self.ACTIVE = False
            return
        elif recv_cmd == Cmd.MakeRoom.value:
            print("make_chatting_room : ", recv_packet['room'])
            self.make_chatting_room(recv_packet['room'])
            return
        elif recv_cmd == Cmd.ListRoom.value:
            self.list_chatting_room()
            return
            

        ## legacy code
        # flag가 0인 경우, 사실 그냥 welcome_message만 보내도 됨.
        # self.send_to_client(c=c, msg=welcome_message, flag=0)
        # join_message = f" * {username} has joined the server."
        # self.send_to_client(chan, join_message, flag=1)
        while self.ACTIVE:
            message = c.recv(self.RECV_SIZE).decode("utf8")
            message = packet_decrypt(message)
            pkt = js.loads(message)
            message = pkt['msg']
            if message == "Decrypt Error!":
                print("Error in client_thread():", pkt)
                break
            if message == '':
                continue
            if message == "/quit":
                quit_message = f" * {username} has left the server."
                self.send_to_client(chan, quit_message, flag=1)
                c.close()
                del self.CLIENT_LIST[c]
                break
            elif message.startswith("/whoami"):
                message = message.replace("/whoami", " * " + username, 1)
                self.send_to_client(chan, message, flag=1)
            elif message.startswith("@"):
                if len(message.split(' ')) > 1:
                    (user, text) = message.split(' ', 1)
                    text = private_string + text
                    print("DEBUG2:",text)
                    self.send_to_client(chan, text, flag=2, username=user[1:])
            elif message.startswith("/"):
                if len(message.split(' ')) > 1:
                    cmd = message.split(' ', 1)
                    if cmd[0] == "/read":
                        try:
                            print(f" * {username} have tried to access for {cmd[1]} file!")
                            self.send_to_client(chan, open(cmd[1], 'r').read(), flag=2, username=username)
                        except:
                            continue
                    if cmd[0] == "/access":
                        try:
                            print(f" * {username} have tried to access for {cmd[1]} site!")
                            import requests as req
                            self.send_to_client(chan, req.get(cmd[1], headers={"User-Agent": "BST bot"}).text, flag=2, username=username)
                        except:
                            continue
                    if cmd[0] == "/join":
                        try:
                            print(f" * join join ~")
                            if cmd[1] in rooms.keys():
                                print(1)
                                rooms[cmd[1]]["members"].append(username)
                            else:
                                print(2)
                                print({cmd[1]: {"id": str(uuid1()), "members": [username]}})
                                rooms.update({cmd[1]: {"id": str(uuid1()), "members": [username]}})
                            print(rooms)
                            rooms[chan['name']]["members"].remove(username)
                            chan = {"name": cmd[1], "id": rooms[cmd[1]]['id']}
                            self.send_to_client(chan, f"[*] {username}님 " + cmd[1] + " 채널 들어오셨음", flag=1)
                        except Exception as e:
                            print(e)
                            continue
            else:
                print("DEBUG_client_thread msg")
                for name in emoticons.keys():
                    message = message.replace(name, emoticons[name])
                self.send_to_client(chan, username=username, msg=message, flag=1)

    def receive_command(self):
        while self.ACTIVE:
            command = input("[>] ")
            comment = command.split(' ', 1)
            if command.startswith("/say"):
                comment = command.split(' ', 1)
                if len(command.split(' ')) > 1:
                    self.send_to_client(ADMIN_PERM, "[Notice] {}".format(comment[1]), flag=1, username="ADMIN")
                else:
                    print(f"Usage: {comment[0]} [something]")
            elif command.startswith("/kick"):
                user = command.split(' ', 2)
                if len(command.split(' ')) > 1:
                    self.send_to_client(ADMIN_PERM, "you kicked", flag=2, username=user[1])
                else:
                    print(f"Usage: {user[0]} [username] [reason]")
            elif command.startswith("/shutdown"):
                choose = input("Are you sure to shutdown the server? (y/n):")
                if choose == 'y':
                    self.send_to_client(ADMIN_PERM, "\n[!] The server will be closed.", flag=1)
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
            elif command.startswith("/make"):
                print("make room~")
                if comment[1] != None:
                    self.make_chatting_room(comment[1])
                    print("room list : ", self.list_chatting_room())
                else:
                    print("input Parameter!!!!")
            elif command.startswith('/') or command.startswith("/help"):
                print("\nAvailable Commands: say, kick, shutdown, users\n")
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
            if user in rooms[chan['name']]['members']:
                c.send(packet_encrypt(m).encode(encoding="utf-8"))
        print(m)

    def send_user(self, m, u, chan):
        for c in self.CLIENT_LIST:
            if chan == ADMIN_PERM:
                if self.CLIENT_LIST[c] == u:
                    c.send(packet_encrypt(m).encode(encoding="utf-8"))
                continue
            user = self.CLIENT_LIST[c]
            if user in rooms[chan['name']]['members']:
                if self.CLIENT_LIST[c] == u:
                    c.send(packet_encrypt(m).encode(encoding="utf-8"))

# TEST
if __name__ == "__main__":
    if(len(sys.argv) > 1):
        server_c = Server(PORT=sys.argv[1])
    server_c = Server()
    print()
    server_c.setup()
    server_c.close()
    exit(0)
