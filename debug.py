#!/usr/bin/python3
DEBUG_PRINT = False
class debug:
    def debug_print(*msg):
        if DEBUG_PRINT == True:
            print(msg)
