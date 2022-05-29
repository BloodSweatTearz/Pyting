#!/usr/bin/python3
#-*- coding: utf-8 -*-
import json as js

def main():
        message = {}
        message["(grin)"] = "😁"
        message["(joy)"] = "😂"
        message["(owl)"] = "🦉"
        message["(poo)"] = "💩"
        message["(omg)"] = "🤦"
        message["(music)"] = "🎶"
        message["(thinking_face)"] = "🤔"
        f = open("emoticons.json", "w")
        f.write(js.dumps(message))

main()
