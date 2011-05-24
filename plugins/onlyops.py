from util import hook
import usertracking
import time

@hook.sieve
def opsonlysieve(bot, input, func, kind, args):
    if kind == "event": #log, usertracking, etc use event
        return input
    if "chan" in input.keys() and input.chan in input.conn.users.channels and not "o" in input.conn.users[input.chan].usermodes[input.nick]:
        return None
    return input
