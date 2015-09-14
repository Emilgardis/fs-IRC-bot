#!usr/env/python3.4
# -*- encoding: utf-8
"""test bot for irc"""
import sys
import socket
from functools import partial


class IRCBot:
    sPASS = partial("PASS {} \r\n".format)
    sNICK = partial("NICK {} \r\n".format)
    sUSER = partial("USER {} 0 * :{}\r\n".format)
    sMODE = partial("MODE {} {}\r\n".format)
    sJOIN = partial("JOIN {} {}\r\n".format)

    def __init__(self, addr, pass_=None, nick='Bot', rname='Bot', user='PyBot'):
        self.nick = nick
        self.rname = rname
        self.user = user

        self.irc_sock = socket.socket()
        self.irc_sock.connect(addr)
        if pass_:
            self.send_line(self.sPASS(pass_))
        self.send_line(self.sNICK(nick))
        self.send_line(self.sUSER(user, rname))

    def send_line(self, str_):
        return self.irc_sock.send(str_.encode())

    def logic_loop(self):
        pass

    def on_server_reply(self, numeric, target):
        pass


def parsemsg(s):
    """Breaks a message from an IRC server into its prefix, command, and arguments.
    Stolen from the twisted project:
    twistedmatrix.com/trac/browser/trunk/twisted/words/protocols/irc.py#54
    """

    prefix = ''
    trailing = []
    if not s:
        raise ValueError("Empty string")
    if s[0] == ':':
        prefix, s = s[1:].split(' ', 1)
    if s.find(' :') != -1:
        s, trailing = s.split(' :', 1)
        args = s.split()
        args.append(trailing)
    else:
        args = s.split()
    command = args.pop(0)
    return prefix, command, args
