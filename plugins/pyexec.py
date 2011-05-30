import re

from util import hook, http
import usertracking
import sys

re_lineends = re.compile(r'[\r\n]*')


@hook.command
def python(inp):
    ".python <prog> -- executes python code <prog>"
    inp = inp.replace("~~n", "adsfervbthbfhyujgyjugkikjgqwedawdfrefgdrgrdthg")
    inp = inp.replace("~n", "\n")
    inp = inp.replace("adsfervbthbfhyujgyjugkikjgqwedawdfrefgdrgrdthg", "~n")
    res = http.get("http://eval.appspot.com/eval", statement=inp).splitlines()

    if len(res) == 0:
        return
    res[0] = re_lineends.split(res[0])[0]
    if not res[0] == 'Traceback (most recent call last):':
        return res[0].decode('utf8', 'ignore')
    else:
        return res[-1].decode('utf8', 'ignore')


def rexec(s, bot, input, db):
    exec(s)


@hook.command
def ply(inp, bot=None, input=None, nick=None, db=None, chan=None):
    "execute local python - only admins can use this"
    if not usertracking.query(db, bot.config, nick, chan, "ply"):
        return "nope"
    asdf = inp.split(" ")
    asdfa = asdf[0]
    if asdfa == "eval":
        return eval(" ".join(asdf[1:]))
    elif asdfa == "exec":
        rexec(" ".join(asdf[1:]), bot, input, db)
