from util import hook
import sqlite3
import re
import time

def query(db, config, user, channel, permission):
    if user in config["admins"]:
        return True
    
    return False

curvers = 3

class Users(object):
    def __init__(self, version, users={}, channels={}):
        self._version = version
        self.users = dict(users)
        self.channels = dict(channels)

    def __join__(self, nick, user, host, channel, modes=""):
        if nick in self.users.keys():
            userobj = self.users[nick]
        else:
            userobj = User(nick, user, host)
            self.users[nick] = userobj
        
        if channel in self.channels.keys():
            chanobj = self.channels[channel]
        else:
            chanobj = Channel(channel)
            self.channels[channel] = chanobj
        chanobj.users[nick] = userobj
        chanobj.usermodes[nick] = set(modes.replace("@","o").replace("+","v"))

    def __exit__(self, nick, channel):
        "all types of channel-=user events"
        chanobj = self.channels[channel]
        del chanobj.users[nick]
        del chanobj.usermodes[nick]
    
    def __chnick__(self, old, new):
        print "changing nick '%s' to '%s'" % (old, new)
        user = self.users[old]
        del self.users[old]
        self.users[new] = user
        user.nick = new
    
    def __mode__(self, chan, mode, argument=None):
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

class User(object):
    def __init__(self, nick, user, host, nickserv=0, lastmsg=0):
        self.nick=nick
        self.user=user
        self.host=host
        self.nickserv=int(nickserv)
        self.lastmsg=lastmsg or time.time()

class Channel(object):
    def __init__(self, name, topic=None, users={}, usermodes={}, modes={}):
        self.name=name
        self.topic=topic
        self.users=dict(users)
        self.usermodes=dict(usermodes)
        self.modes=dict(modes)

initialized = False
def initlists(conn):
    if hasattr(conn, "users"):
        return
    else:
        conn.users=Users(curvers)

@hook.command
@hook.singlethread
def names(inp, db=None, input=None, bot=None):
    #sends NAMES for all channels, to freshen names
    if query(db, bot.config, input.nick, input.chan, "freshennames"):
        oldusers = input.conn.users
        try:
            chans = input.conn.users.channels.keys()
            del input.conn.users
            initlists(input.conn)
            for i in chans:
                input.conn.send("NAMES "+i)
        except:
            input.conn.users = oldusers

flag_re=re.compile(r"^([@+]*)(.*)$")
@hook.event("353")
@hook.singlethread
def tracking_353(inp, input=None):
    "when the names list comes in"
    chan=inp[2]
    names=inp[3]
    for name in names.split(" "):
        match = flag_re.match(name)
        flags=match.group(1)
        nick=match.group(2)
        input.conn.users.__join__(nick, None, None, chan, flags)

@hook.event("JOIN")
@hook.singlethread
def tracking_join(inp, input=None):
    "when a user joins a channel"
    initlists(input.conn)
    input.conn.users.__join__(input.nick, input.user, input.host, input.chan)

@hook.event("PART")
@hook.singlethread
def tracking_part(inp, input=None):
    "when a user parts a channel"
    initlists(input.conn)
    input.conn.users.__exit__(input.nick, input.chan)

@hook.event("KICK")
@hook.singlethread
def tracking_kick(inp, input=None):
    "when a user gets kicked from a channel"
    initlists(input.conn)
    input.conn.users.__exit__(inp[1], inp[0])

@hook.event("QUIT")
@hook.singlethread
def tracking_quit(inp, input=None):
    "when a user quits"
    initlists(input.conn)
    for channel in input.conn.users.channels.values():
        if input.nick in channel.users:
            input.conn.users.__exit__(input.nick, channel.name)

@hook.event("PRIVMSG")
@hook.singlethread
def tracking_privmsg(inp, input=None):
    "updates last seen time - different from seen plugin"
    initlists(input.conn)
    input.conn.users.users[input.nick].lastmsg=time.time()

@hook.event("MODE")
@hook.singlethread
def tracking_mode(inp, input=None):
    "keeps track of when people change modes of stuff"
    initlists(input.conn)
    input.conn.users.__mode__(*inp)

@hook.event("NICK")
@hook.singlethread
def tracking_nick(inp, input=None):
    "tracks nick changes"
    initlists(input.conn)
    input.conn.users.__chnick__(input.nick, inp[0])
    

@hook.command
def mymodes(inp, input=None):
    modes = input.conn.users.channels[input.chan].usermodes[input.nick]
    if len(modes):
        return "+"+("".join(modes))
    else:
        return "but you have no modes ..."