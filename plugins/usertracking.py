from util import hook
import sqlite3
import re
import time
import sys

def query(db, config, user, channel, permission):
    if user in config["admins"]:
        return True
    
    return False

class Users(object):
    def __init__(self, users={}, channels={}):
        self.users = dict(users)
        self.channels = dict(channels)
    
    def __getitem__(self, item):
        try:
            return self.users[item]
        except KeyError:
            return self.channels[item]

    def _join(self, nick, user, host, channel, modes=""):
        userobj = self._user(nick, user, host)
        
        if channel in self.channels.keys():
            chanobj = self.channels[channel]
        else:
            chanobj = Channel(channel, self.users)
            self.channels[channel] = chanobj
        chanobj.users[nick] = userobj
        chanobj.usermodes[nick] = set(modes.replace("@","o").replace("+","v"))

    def _exit(self, nick, channel):
        "all types of channel-=user events"
        chanobj = self.channels[channel]
        del chanobj.users[nick]
        del chanobj.usermodes[nick]
    
    def _chnick(self, old, new):
        print "changing nick '%s' to '%s'" % (old, new)
        user = self.users[old]
        del self.users[old]
        self.users[new] = user
        user.nick = new
    
    def _mode(self, chan, mode, argument=None):
        if not self.channels.has_key(chan):
            return
        changetype = mode[0]
        modeid = mode[1]
        if modeid in "ov":
            if changetype == "+":
                self.channels[chan].usermodes[argument].add(modeid)
            else:
                self.channels[chan].usermodes[argument].remove(modeid)
        else:
            if changetype == "+":
                self.channels[chan].modes[modeid]=argument
            else:
                del self.channels[chan].modes[modeid]
    
    def _trydelete(self, nick):
        for i in self.channels.values():
            if i.users.has_key(nick):
                return
        del self.users[nick]
    
    def _user(self, nick, user, host):
        if nick in self.users.keys():
            userobj = self.users[nick]
        else:
            userobj = User(nick, user, host)
            self.users[nick] = userobj
        return userobj

class User(object):
    def __init__(self, nick, user, host, lastmsg=0):
        self.nick=nick
        self.user=user
        self.host=host
        self.realname=None
        self.channels=None
        self.server=None
        self.authed=None
        self.lastmsg=lastmsg or time.time()

class Channel(object):
    def __init__(self, name, users, topic=None):
        self.name=name
        self.topic=topic
        self.users=Userdict(users)
        self.usermodes=Userdict(users)
        self.modes=dict()

class Userdict(dict):
    def __init__(self, users, *args, **named):
        self.users = users
        dict.__init__(self, *args, **named)

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, self.users[item]) 
        except KeyError:
            return dict.__getitem__(self, item)
    
    def __setitem__(self, item, value):
        try:
            return dict.__setitem__(self, self.users[item], value)
        except KeyError:
            return dict.__setitem__(self, item, value)

@hook.sieve
@hook.singlethread
def valueadd(bot, input, func, kind, args):
    if not hasattr(input.conn, "users"):
        input.conn.users = Users()
        input.conn.users.users[input.nick] = User(input.nick, input.nick, "127.0.0.1")
        
    input["users"]=input.conn.users
    return input

flag_re=re.compile(r"^([@+]*)(.*)$")
@hook.event("353")
@hook.singlethread
def tracking_353(inp, input=None, users=None):
    "when the names list comes in"
    chan=inp[2]
    names=inp[3]
    for name in names.split(" "):
        match = flag_re.match(name)
        flags=match.group(1)
        nick=match.group(2)
        users._join(nick, None, None, chan, flags)

@hook.event("311")
@hook.singlethread
def tracking_311(inp, input=None, users=None):
    "whois: nick, user, host, realname"
    nick=inp[1]
    user=inp[2]
    host=inp[3]
    if nick not in input.conn.users.users.keys():
        users._user(nick, user, host)
    users[nick].realname=inp[5]

@hook.event("319")
@hook.singlethread
def tracking_319(inp, input=None, users=None):
    "whois: channel list"
    users[inp[1]].channels=inp[2].split(" ")

@hook.event("312")
@hook.singlethread
def tracking_312(inp, input=None, users=None):
    "whois: server"
    users[inp[1]].server=inp[2]

@hook.event("330")
@hook.singlethread
def tracking_330(inp, input=None, users=None):
    "user logged in"
    users[inp[1]].nickserv = 1

@hook.event("318")
@hook.singlethread
def tracking_318(inp, input=None, users=None):
    "end of whois"
    user = users[inp[1]]
    user.nickserv = user.nickserv or -1

@hook.event("JOIN")
@hook.singlethread
def tracking_join(inp, input=None, users=None):
    "when a user joins a channel"
    users._join(input.nick, input.user, input.host, input.chan)

@hook.event("PART")
@hook.event("KICK")
@hook.event("QUIT")
@hook.singlethread
def tracking_quit(inp, input=None, users=None):
    "when a user quits"
    for channel in users.channels.values():
        if input.nick in channel.users:
            users._exit(input.nick, channel.name)
    users._trydelete(input.nick)

@hook.event("PRIVMSG")
@hook.singlethread
def tracking_privmsg(inp, input=None, users=None):
    "updates last seen time - different from seen plugin"
    users[input.nick].lastmsg=time.time()

@hook.event("MODE")
@hook.singlethread
def tracking_mode(inp, input=None, users=None):
    "keeps track of when people change modes of stuff"
    users._mode(*inp)

@hook.event("NICK")
@hook.singlethread
def tracking_nick(inp, input=None, users=None):
    "tracks nick changes"
    users._chnick(input.nick, inp[0])



@hook.command
def mymodes(inp, input=None, users=None):
    modes = users[input.chan].usermodes[input.nick]
    if len(modes):
        return "+"+("".join(modes))
    else:
        return "but you have no modes ..."