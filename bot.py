#!usr/env/python3.4
# -*- encoding: utf-8
# Licensed under MIT License (c) 2015
"""Bot for irc"""
import socket
from functools import partial
import logging
import requests
import threading

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG,
    filename='botlog.txt')
logging.info("New session")
# Fix parsing for better compatability with input
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
format = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(format)
logging.getLogger('').addHandler(console)


class IRCBot:
    sPASS = partial("PASS {} \r\n".format)
    sNICK = partial("NICK {} \r\n".format)
    sUSER = partial("USER {} 0 * :{}\r\n".format)
    sMODE = partial("MODE {} {}\r\n".format)
    sJOIN = partial("JOIN {} {}\r\n".format)
    sPRIVMSG = partial("PRIVMSG {} :{}\r\n".format)
    sPONG = partial("PONG {} \r\n".format)
    cIgnore = []

    def __init__(self, addr, pass_=None, nick='BotEMILG', rname='Bot Gardström',
                 user='Py Bot'):
        self.addr = addr
        self.nick = nick
        self.rname = rname
        self.user = user
        self.connected = False
        self.host = "ts01.forsmarksskola.se"  # TODO Get from NOTICE Auth

        self.irc_sock = socket.socket()
        self.irc_sock.connect(self.addr)
        self.buffer_ = ""
        if pass_:
            self.send_line(self.sPASS(pass_))
        self.send_line(self.sNICK(nick))
        self.send_line(self.sUSER(user, rname))

    def run(self):
        def run_listen_server():
            self.data_received(self.irc_sock.recv(4096).decode('utf-8'))

        def run_listen_console():
            self.handle_console(input("> "))
            pass
        while True:
            t_server_input = threading.Thread(target=run_listen_server)
            t_console_input = threading.Thread(target=run_listen_console)
            t_server_input.daemon = True
            t_console_input.deamon = True
            t_server_input.start()
            t_console_input.start()

    def send_line(self, str_):
        logging.debug("Sent: {}".format(str_))
        return self.irc_sock.send(str_.encode('utf-8'))

    def rpl_001(self, prefix, params):
        self.connected = True
        self.on_connect()

    def irc_PRIVMSG(self, prefix, params):
        sent_from = prefix.split("!")[0]
        reply_to = params[0] if params[0] != self.nick else sent_from
        logging.info("{:9} to {} :{}".format(sent_from, params[0], params[0]))
        if params[1].startswith("!"):
            function = getattr(self, "cmd_{}".format(params[1].split()[0][1:]),
                               None)
            if function:
                function(prefix, params)
        if params[1].startswith("!docommand"):  # TODO Make to function cmd_
            self.send_line(params[1][11:])
            print(params[1][11:])
        if params[1] == "!joke":  # TODO Make to function cmd_
            r = requests.get("http://api.icndb.com/jokes/random")
            self.send_line(self.sPRIVMSG(reply_to, r.json()['value']['joke']))

    def irc_PING(self, prefix, params):
        print(params)
        self.send_line(self.sPONG(self.host, params[0]))

    def on_connect(self):
        self.send_line(self.sJOIN("#42", "livet"))
        logging.info("Joined channel #42")

    def handle_command(self, prefix, command, params):
        method = getattr(self, "irc_{}".format(command.upper()), None)
        if command in self.cIgnore:
            return
        if method:
            logging.debug(
                "irc_{:9} called from {} with {}".format(
                    command,
                    prefix,
                    params))
            method(prefix, params)
            return
        elif command.isdigit():
            response = getattr(self, "rpl_{}".format(command), None)
            if response:
                logging.debug("rpl_{:9} called with {}".format(command, params))
                response(prefix, params)
                return
        elif command not in self.cIgnore:
            logging.debug(
                "{:9} received with {}".format(command, params))
            return

    def handle_console(self, input_):
        print("< {}".format(input_))

    def data_received(self, data):
        self.buffer_ = self.buffer_ + data
        buffer_into = list(self.buffer_.rpartition("\r\n"))
        lines = buffer_into[0].split("\r\n")
        self.buffer_ = buffer_into[2]
        for line in lines:
            self.handle_command(*parsemsg(line))
        lines.append("/n")
        with open("bothistory.txt", "a") as file:
            file.write("\n".join(lines))


def parsemsg(s):
    """Breaks line from an IRC server into its prefix, command, and arguments.
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
        params = s.split()
        params.append(trailing)
    else:
        params = s.split()
    command = params.pop(0)
    return str(prefix), str(command), params
bot = None
global bot
if __name__ == "__main__":
    bot = IRCBot(("irc.fbin.org", 6667))
    bot.run()
