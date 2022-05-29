#!/usr/bin/python3
#-*- coding: utf-8 -*-
import argparse
from server import Server

VERSION = 1.0

def version():
    global VERSION
    print("Pything v%.1f." %VERSION)
    print("Copyright (C) 2022 Free Software Foundation, Inc.")
    print("Made by Team BloodSweatTearz.")
    
def argparse_init():
    parser = argparse.ArgumentParser(description='Pything - Server')
    parser.add_argument('--ipaddress', '-i', help='Set server ip address', default="172.26.1.157")
    parser.add_argument('--port', '-p', help='Set server bind port', default=8000)
    parser.add_argument('--maxclient', '-l', help='set max client', default=100)
    parser.add_argument('--recvsize', '-c', help='set recvsize', default=4096)
    parser.add_argument('--version', '-v', help='set version', action='store_true')
    return parser

if __name__ == "__main__":
    args = argparse_init().parse_args()
    
    if(args.version):
        version()
        exit(0)

    server_c = Server(IP_ADDRESS=args.ipaddress, PORT=args.port, MAX_CLIENTS=args.maxclient, RECV_SIZE=args.recvsize)
    print()
    server_c.setup()
    server_c.close()
    exit(0)
