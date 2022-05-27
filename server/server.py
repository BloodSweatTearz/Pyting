#!/usr/bin/python3
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from cipher import *
import sys
import signal
import json as js
from uuid import *

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

    # login check
    def user_login_check(self, user_info):
        user_id = user_info['msg']['id']
        user_pw = user_info['msg']['pw']

        try:
            if users[user_id] == user_pw:
                return True
            else:
                return False
        except:
            print("login error")
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
        self.SERVER_LOOP.join()

    def listen_incoming(self):
        self.SERVER.listen(self.MAX_CLIENTS)
        print(f"Currently listening for up to {self.MAX_CLIENTS} clients...\n")
        while self.ACTIVE:
            (client, address) = self.SERVER.accept()
            if(not self.ACTIVE):
                return
            print(f" * {address[0]}:{address[1]} has connected.")

            login_info = client.recv(self.RECV_SIZE).decode("utf8")
            login_info = packet_decrypt(login_info)
            login_info = js.loads(login_info)

            # 추후에 recv 값의 cmd를 보고 작동하도록 변경해야함
            # 현재는 login이 작동하도록 만듦.
            # 지금은 여기다 만들어서 connect 완료시 매끄럽지 않게 되는데, client_tread에다가 완성시키면 깔끔하게 나올듯.
            if self.user_login_check(login_info):
                self.send_to_client(c=client, msg=True, flag=0)
                Thread(target=self.client_thread, args=(client, )).start()
                Thread(target=self.receive_command, args=(client, )).start()
            else:
                print("user login error: can't create thread")
                self.send_to_client(c=client, msg=False, flag=0)

    """
     flag:
      0 = c.send
      1 = send_all (chan needed)
      2 = send_user (chan needed)
    """
    def send_to_client(self, chan='', msg='', flag=0, c=[], username=''):
        print(msg)
        print(rooms)
        if flag == 0:
            c.send(packet_encrypt(js.dumps({"rooms": rooms, "msg": msg})).encode(encoding="utf-8"))
        elif flag == 1:
            self.send_all(js.dumps({"rooms": rooms, "msg": msg}), chan)
        elif flag == 2:
            self.send_user(js.dumps({"rooms": rooms, "msg": msg}), username, chan)
        else:
            pass

    def message_format(self, username, text=""):
        return { 'username': username, 'text': text }

    def client_thread(self, c):
        recv_packet = c.recv(self.RECV_SIZE).decode("utf8")
        recv_packet = packet_decrypt(recv_packet)
        recv_packet = js.loads(recv_packet)
        print("recv_packet:" ,recv_packet) # test
        chan = {"name": "general", "id": str(uuid1())}
        username = recv_packet['username']
        self.CLIENT_LIST[c] = username

        rooms["general"]["members"].append(username)

        user_string = "<" + username + "> "
        private_string = "[" + username + "] "
        welcome_message = f" * You have connected to the server at {self.IP_ADDRESS}."

        # flag가 0인 경우, 사실 그냥 welcome_message만 보내도 됨.
        self.send_to_client(c=c, msg=welcome_message, flag=0)
        join_message = f" * {username} has joined the server."
        self.send_to_client(chan, join_message, flag=1)
        while self.ACTIVE:
            message = c.recv(self.RECV_SIZE).decode("utf8")
            message = packet_decrypt(message)
            pkt = js.loads(message)
            message = pkt['msg']
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
                    print(text)
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
                for name in emoticons.keys():
                    message = message.replace(name, emoticons[name])
                message = user_string + message
                self.send_to_client(chan, message, flag=1)

    def receive_command(self, c):
        while self.ACTIVE:
            command = input("[>] ")
            if command.startswith("/say"):
                comment = command.split(' ', 1)
                if len(command.split(' ')) > 1:
                    self.send_to_client(ADMIN_PERM, f"\n[NOTICE] {comment[1]}", flag=1)
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
                    c.close()
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
                print(rooms)
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
