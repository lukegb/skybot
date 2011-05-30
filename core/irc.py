import re
import socket
import time
import ssl


irc_prefix_rem = re.compile(r'(.*?) (.*?) (.*)').match
irc_noprefix_rem = re.compile(r'()(.*?) (.*)').match
irc_netmask_rem = re.compile(r':?([^!@]*)!?([^@]*)@?(.*)').match
irc_param_ref = re.compile(r'(?:^|(?<= ))(:.*|[^ ]+)').findall



class IRCDisconnected(Exception):
    pass
#TODO: socket timeouts
class IRCConnection(object):
    def __init__(self, irc, host, port, usessl):
        #FIXME: SSL certificate checking
        self.irc = irc
        self.host = host
        self.port = port
        self.ssl = usessl
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.irc = irc
        self.ibuffer = []
        self.obuffer = []
        self.extras = ""
        self.lastwrite = 0
        self.connect()
    def connect(self):
        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)
        self.socket.connect((self.host, self.port))
    def read(self):
        b = self.extras
        self.extras = ""
        tlen = 4096
        #ensure we are reading all data currently available
        while True:
            b = b + self.socket.recv(4096)
            if b != tlen:
                break
            tlen += 4096
        #did they hang up?
        if b == "":
            raise IRCDisconnected()
        b = b.splitlines(True)
        if not b[-1].endswith("\r\n"):
            self.extras = b[-1]
            b = b[:-1]
        self.ibuffer.extend(b)
    def send(self, what):
        #print "<<< " +  what
        self.obuffer.append(what)
    def write(self):
        if len(self.obuffer) == 0:
            return
        if time.time() - self.lastwrite > 1:
            x = self.obuffer.pop(0).encode('utf-8', 'replace')
            self.socket.send(x + "\r\n")
            self.lastwrite = time.time() 
    def read_all(self):
        self.read()
        x = self.ibuffer
        self.ibuffer = []
        return x
class IRC(object):
    def __init__(self, processor, server, nick, port=6667, channels=[], conf={}):
        self.channels = channels
        self.conf = conf
        self.server = server
        self.port = port
        self.nick = nick
        self.processor = processor
        self.connect()
    def connect(self):
        self.conn = IRCConnection(self, self.server, self.port, self.conf.get("ssl", False))
        self.set_pass(self.conf.get('server_password'))
        self.set_nick(self.nick)
        self.cmd('USER', [conf.get('user', 'skybot'), '3', '*', conf.get('realname', 'skybot 2.0')])
    def process(self, msg):
        msg = decode(msg)
        if msg.startswith(':'):
            prefix, command, params = irc_prefix_rem(msg).groups()
        else:
            prefix, command, params = irc_noprefix_rem(msg).groups()
        nick, user, host = irc_netmask_rem(prefix).groups()
        paramlist = irc_param_ref(params)
        lastparam = ""
        if paramlist:
            if paramlist[-1].startswith(':'):
                paramlist[-1] = paramlist[-1][1:]
            lastparam = paramlist[-1]
        self.processor(self, [msg, prefix, command, params, nick, user, host, paramlist, lastparam])
        if command == "PING":
            self.cmd("PONG", paramlist)
    def send(self, what):
        self.conn.send(what)
    def loop_write(self):
        self.conn.write()
    def loop_read(self):
        try:
            l = self.conn.read_all()
        except IRCDisconnected:
            return False
        for line in l:
            self.process(line)
        return True
    def cmd(self, command, params=None):
        if params:
            params[-1] = ":" + params[-1]
            self.send(command + ' ' + ' '.join(map(censor, params)))
        else:
            self.send(command)
    def join(self, channel):
        self.cmd('JOIN', [channel])
    def msg(self, who, what):
        self.cmd('PRIVMSG', [who, what])
    def set_nick(self, nick):
        self.cmd('NICK', [nick])
    def set_pass(self, passwd):
        if passwd:
            self.cmd('PASS', [passwd])
def decode(txt):
    for codec in ('utf-8', 'iso-8859-1', 'shift_jis', 'cp1252'):
        try:
            return txt.decode(codec)
        except UnicodeDecodeError:
            continue
    return txt.decode('utf-8', 'ignore')

def censor(text):
    replacement = '[censored]'
    if 'censored_strings' in bot.config:
        words = map(re.escape, bot.config['censored_strings'])
        regex = re.compile('(%s)' % "|".join(words))
        text = regex.sub(replacement, text)
    return text


