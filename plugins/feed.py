from util.feeds import redfeed as rfd
from util import hook

@hook.command
def redfeed(inp, nick='', server='', reply=None, db=None):
    reload(rfd)
    j = rfd.pretty_ents(rfd.get_bukkit(maxents=2, onlynew=False))
    reply(' | '.join(j))

