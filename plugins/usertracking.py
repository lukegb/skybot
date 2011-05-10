from util import hook
import sqlite3
import re
import time
import sys

def query(db, config, user, channel, permission):
    if user in config["admins"]:
        return True
    
    return False

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