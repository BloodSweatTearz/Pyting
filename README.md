# Pyting
![Pyting Logo](./logo.png)

## Overview

종단간 AES 암호화 통신을 사용하는 단체 채팅 프로그램

[**[시연 영상 - YouTube]**](https://youtu.be/Ehr_PJAap1k)

### Features 

1. 로그인/회원가입
2. 암호화 통신 지원
3. 비밀번호 SHA512 방식 해쉬화
4. 이모티콘
5. 귓속말
6. 채널 생성/접속
7. 관리자 공지
8. 사용자 관리

### Server Usage

  ```bash
  $ ./run_server.py -h
  usage: run_server.py [-h] [--ipaddress IPADDRESS] [--port PORT]
                       [--maxclient MAXCLIENT] [--recvsize RECVSIZE] [--version]
  
  Pything - Server
  
  optional arguments:
    -h, --help            show this help message and exit
    --ipaddress IPADDRESS, -i IPADDRESS
                          Set server ip address
    --port PORT, -p PORT  Set server bind port
    --maxclient MAXCLIENT, -l MAXCLIENT
                          set max client
    --recvsize RECVSIZE, -c RECVSIZE
                          set recvsize
    --version, -v         set version
  ```

### Server Commands
1. /say : 전체 알림 기능
2. /shutdown : 서버 종료
3. /users : 모든 사용자 목록
4. /rooms : 모든 채팅방 목록

## How to install?
### Requirements
#### Common Basic Setup

```bash
$ pip install pycrypto
```

#### Common Client Basic Setup
```bash
$ pip install pyqt
$ pip install qt-material
```

## How to execute?
### Server 
**[리눅스]**

```
python server/run_server.py 
python3 server/run_server.py 
chmod 777 server/run_server.py 
./server/run_server.py 
```
**[윈도우]**

```
python server/run_server.py 
python3 server/run_server.py
```

### Client

**[리눅스]** 

```
python client/main.py 
python3 client/main.py 
chmod 777 client/main.py 
./client/main.py 
```
**[윈도우]**

```
python client/main.py python3 
client/main.py
```
