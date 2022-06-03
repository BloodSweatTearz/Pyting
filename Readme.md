# Pyting

## Requirement
1. pycrypto

### Basic Setup
`1. pip install pycrypto`



## patch

### [22.05.19]

- server.py 클래스화

- 사용법

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
