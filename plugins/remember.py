"""
remember.py: written by Scaevolus 2010, modified by lahwran 2011
"""

from util import hook
import pyexec
import usertracking
import re
import time

defaultchan = "default"  # TODO: creates a security hole, username "default" can alter global factoids

redirect_re = re.compile(r'([|>])\s*(\S*)\s*$|([<])(.*)')
word_re = re.compile(r'^([+~-]?)(\S+)')
filter_re = re.compile(r'^\s*[<]([^>]*)[>]\s*(.*)\s*$')
cmdfilter_re = re.compile(r'^cmd:(.+)$')
forgotten_re = re.compile(r'^([<]locked[^>]*[>])?[<]forgotten[>].*')
#args is what is left over after removing these
maxdepth = 4


def db_init(db):
    db.execute("create table if not exists memory(chan, word, data, nick,"
               " primary key(chan, word))")
    db.commit()


def get_memory(db, chan, word):
    row = db.execute("select data from memory where chan=? and word=lower(?)",
                      (chan, word)).fetchone()
    if row:
        return row[0]
    else:
        return None


def checkinp(chan, inp, localpm):
    if not inp.split(" ")[0] == "." and ((chan.startswith('#') and localpm) or not localpm):
        chan = defaultchan
        local = False
    elif (chan.startswith('#') and localpm) or not localpm:
        inp = " ".join(inp.split(" ")[1:])
        local = True
    else:
        local = True
    return local, chan, inp.strip()


@hook.command
def no(inp, nick='', chan='', db=None, notice=None, bot=None, modes=None):
    ".no <word> is <data> -- remaps word to data"
    if modes.check("remember.no.no", db):
        return
    local, chan, inp = checkinp(chan, inp, True)

    db_init(db)
    try:
        head, tail = inp.split(" ", 1)
    except ValueError:
        return no.__doc__
    if tail.startswith("is "):
        tail = " ".join(tail.split(" ")[1:])

    if tail.startswith("<locked") and not modes.check("remember.lock", db):
        notice(("[local]" if local else "") + "you may not lock factoids.")
        return

    data = get_memory(db, chan, head)

    if not data:
        notice("but '%s' doesn't exist!" % head.replace("'", "`"))
        return
    if data and data.startswith("<locked") and not modes.check("remember.lock", db):
        notice(("[local]" if local else "") + "that factoid is locked, sorry.")
        return

    db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, head, tail, nick))
    print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, head, tail, nick))
    db.commit()
    notice('forgetting "%s", remembering this instead.' % \
                data.replace('"', "''"))


@hook.command
@hook.command("r")
#@hook.regex("([^ ]*)")
def remember(inp, nick='', chan='', db=None, input=None, notice=None, bot=None):
    ".remember [.] <word> is <data> -- maps word to data in the memory, '.' means here only"
    if input.modes.check("remember.no.remember", db):
        return
    db_init(db)

    local, chan, inp = checkinp(chan, inp, True)

    try:
        head, tail = inp.split(" ", 1)
    except ValueError:
        return remember.__doc__
    if tail.startswith("is "):
        tail = " ".join(tail.split(" ")[1:])

    if tail.startswith("<locked") and not input.modes.check("remember.lock", db):
        notice(("[local]" if local else "") + "you may not lock factoids.")
        return

    data = get_memory(db, chan, head)

    if data and data.startswith("<locked") and not input.modes.check("remember.lock", db):
        input.notice(("[local]" if local else "") + "that factoid is locked.")
        return
    if data and not data.startswith("<forgotten>"):
        notice("but '%s' already means something else!" % head.replace("'", "`"))
        return
    elif data and data.startswith("<forgotten>"):
        input.notice(("[local]" if local else "") + "permanently deleting " + repr(data) + " to accomodate this")

    db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, head, tail, nick))
    print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, head, tail, nick))
    db.commit()
    notice(("[local]" if local else "") + 'done.')


@hook.command
def forget(inp, chan='', db=None, nick='', notice=None, modes=None):
    ".forget [.] <word> -- forgets the mapping that word had, '.' means here only"
    if modes.check("remember.no.forget", db):
        return
    local, chan, inp = checkinp(chan, inp, True)
    db_init(db)

    data = get_memory(db, chan, inp)
    if data and data.startswith("<locked") and not modes.check("remember.lock", db):
        notice(("[local]" if local else "") + "that factoid is locked.")
        return
    if data and not data.startswith("<forgotten>"):
        db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, inp, "<forgotten>" + data, nick))
        print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, inp, "<forgotten>" + data, nick))
        #db.execute("delete from memory where chan=? and word=lower(?)",
        #           (chan, inp))
        db.commit()
        notice(("[local]" if local else "") + ('forgot `%s`' % data.replace('`', "'")))
    elif data:
        notice(("[local]" if local else "") + "I already archived that.")
    else:
        notice(("[local]" if local else "") + "I don't know about that.")


@hook.command
def unforget(inp, chan='', db=None, nick='', notice=None, modes=None):
    ".unforget [.] <word> -- re-remembers the mapping the word had before, '.' means here only "
    if modes.check("remember.no.unforget", db):
        return
    db_init(db)

    local, chan, inp = checkinp(chan, inp, True)

    data = get_memory(db, chan, inp)
    if data and data.startswith("<locked") and not modes.check("remember.lock", db):
        input.notice(("[local]" if local else "") + "that factoid is locked.")
        return

    if data and data.startswith("<forgotten>"):
        db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, inp, data.replace("<forgotten>", "").strip(), nick))
        print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, inp, data.replace("<forgotten>", "").strip(), nick))
        db.commit()
        notice(("[local]" if local else "") + ('unforgot `%s`' % data.replace('`', "'")))
    elif data:
        notice(("[local]" if local else "") + "I still remember that.")
    else:
        notice(("[local]" if local else "") + "I never knew about that.")


@hook.command
def mem(inp, chan='', db=None, nick='', notice=None, user='', host='', bot=None, modes=None):
    "controls memory."

    def lock(name):
        db_init(db)
        local = name.startswith("l:")
        if name.startswith("l:"):
            name = name[2:]
        facchan = defaultchan if not local else chan
        data = get_memory(db, facchan, name)
        if data and data.startswith("<locked"):
            notice("already locked")
        elif data:
            data = "<locked:%s!%s@%s %s %d>%s" % (nick, user, host, chan, time.time(), data)
            db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (facchan, name, data, nick))
            db.commit()

    def unlock(name):
        db_init(db)
        local = name.startswith("l:")
        if name.startswith("l:"):
            name = name[2:]
        facchan = defaultchan if not local else chan
        data = get_memory(db, facchan, name)
        if data and not data.startswith("<locked"):
            notice("that's not locked..?")
        elif data:
            filtermatch = filter_re.search(data)
            if filtermatch:
                filtername = filtermatch.group(1).lower()
                data = filtermatch.group(2)
                notice("unlocking: " + filtername)
                db.execute("replace into memory(chan, word, data, nick) values"
                   " (?,lower(?),?,?)", (facchan, name, data, nick))
                db.commit()
            else:
                notice("this should never happen, but that doesn't seem to be a valid locked factoid. I'm just gonna delete it and let you recreate it, k?")
                notice("current value: " + repr(data))
                db.execute("delete from memory where chan=? and word=?", (facchan, name))
                db.commit()

    commands = {"lock": [1, lock, "lock"], "unlock": [1, unlock, "lock"]}
    split = inp.split(" ")
    if len(split):
        if not split[0] in commands:
            return "no such command"
        if not modes.check("remember." + commands[split[0]][2], db):
            return "you do not have permission to use that command"
        if len(split) == commands[split[0]][0] + 1:
            func = commands[split[0]][1]
            func(*split[1:])
        else:
            return "wrong number of args for command"
    else:
        return "arguments reqired"


@hook.regex(r'^[?!](.+)')  # groups: (mode,word,args,redirectmode,redirectto)
def question(inp, chan='', say=None, db=None, input=None, nick="", me=None, bot=None, notice=None):
    "!factoid -- shows what data is associated with word"
    filterhistory = []  # loop detection, maximum recursion depth(s)
    if input.modes.check("remember.no.question", db):
        return

    def varreplace(orig, variables):
        for i in variables.keys():
            orig = orig.replace("$" + i, variables[i])
        return orig

    def filters(retrieved, variables, filterhistory):
        orig = retrieved[0]
        setternick = retrieved[1]
        if not orig:
            return ""
        if len(filterhistory) + 1 > 10:
            return "Hit max recursion depth: [" + orig[:30] + "...]"
        if orig in filterhistory:
            return "Going in a circle: [" + orig[:30] + "...]"
        filterhistory.append(orig)
        filtermatch = filter_re.search(orig)
        if filtermatch:
            filtername = filtermatch.group(1).lower()
            filterinp = filtermatch.group(2)
            if filtername == "alias":
                return filters(retrieve(varreplace(filterinp, variables), chan), variables, filterhistory)
            elif filtername == "reply":
                return varreplace(filterinp, variables)
            elif filtername == "action":
                return (varreplace(filterinp, variables), me)
            elif filtername == "noreply":
                return ""
            elif filtername == "pyexec":
                preargs = ""
                for i in variables.keys():
                    preargs+=i+"="+repr(unicode(variables[i]).encode('utf8'))+";"
                print preargs+filterinp
                return filters([pyexec.python(preargs+filterinp), setternick], variables, filterhistory)
            elif filtername.startswith("locked"):
                return filters([filterinp, setternick], variables, filterhistory)
            cmd = cmdfilter_re.search(filtername)
            if cmd:
                trigger = cmd.group(1).lower()
                cmdfunc, cmdargs = bot.commands[trigger]
                if trigger in ["no", "remember", "forget", "unforget", "python"]:
                    return "I'm sorry, I can't let you do that, dave"
                outputlines = []

                def cmdsay(o):
                    print "cmdsay out:", repr(o)
                    if filter_re.search(o):
                        outputlines.append(o)
                    else:
                        outputlines.append("<reply>" + o)

                def cmdme(o):
                    outputlines.append("<action>" + o)

                newinput = bot.Input(input.conn, input.raw, input.prefix, input.command, input.params,
                    setternick, "user", "host", input.paraml, input.msg)
                newinput.say = cmdsay
                newinput.reply = cmdsay
                newinput.me = cmdme
                newinput.inp = varreplace(filterinp, variables)
                newinput.trigger = trigger
                bot.dispatch(newinput, "command", cmdfunc, cmdargs, autohelp=False)
                time.sleep(3.5)  # WRONG.. but meh
                outputlines = [filters([line, setternick], variables, filterhistory) for line in outputlines]
                return outputlines
        else:
            return variables["word"] + " is " + varreplace(orig, variables)

    def retrieve(word, chan):
        ret = db.execute("select data, nick from memory where chan=? and word=lower(?)",
                      (chan, word)).fetchone()
        if ret and not forgotten_re.match(ret[0]):
            return ret
        ret = db.execute("select data, nick from memory where chan=? and word=lower(?)",
                      (defaultchan, word)).fetchone()
        if ret and not forgotten_re.match(ret[0]):
            return ret
        return ["", ""]

    db_init(db)
    whole = False

    def splitgroups(inp):
        "returns (mode, word, args, redir, redirto)"
        words = inp.group(1)
        ret = []
        wordmatch = word_re.search(words)
        words = words[wordmatch.end():]
        ret.append(wordmatch.group(1))
        ret.append(wordmatch.group(2).lower())

        redirect = ''
        redirectto = ''
        redirectmatch = redirect_re.search(words)
        if redirectmatch:
            redirect = redirectmatch.group(1)
            redirectto = redirectmatch.group(2)
            words = words[:redirectmatch.start()]
        ret.append(words.strip())
        ret.append(redirect)
        ret.append(redirectto)
        return ret

    (mode, word, args, redir, redirto) = splitgroups(inp)

    def finaloutput(s, redir, redirto, input, special=None):
        if not s:
            return
        if redirto.startswith("#"):
            redirto = nick
            s = "Fuck no, you spamwhore (if you are not a spamwhore, please ignore this message)"
        if redir == ">" and not special:
            input.conn.cmd('NOTICE', [redirto, nick + " sent: " + s])
        elif redir == "|" and not special:
            input.say(redirto + ": " + s)
        elif redir == "<" and not special:
            input.notice(s)
        elif special:
            special(s)
        else:
            input.say(s)

    def output(data):
        if type(data) == list:
            for i in data:
                output(i)
        elif type(data) == tuple:
            finaloutput(data[0], redir, redirto, input, data[1])  # special for things like /me
        else:
            finaloutput(data, redir, redirto, input)

    variables = {"chan": chan,
                 "user": nick,
                 "nick": input.conn.nick,
                 "target": redirto,
                 "inp": args,
                 "word": word}
    if mode == "-":   # information
        message = word + " is "
        local = db.execute("select nick from memory where chan=? and word=lower(?)", (chan, word)).fetchone()
        if local:
            message += "locally set by " + local[0]
        default = db.execute("select nick from memory where chan=? and word=lower(?)", (defaultchan, word)).fetchone()
        if local and default:
            message += " and "
        if default:
            message += "globally set by " + default[0]
        if local or default:
            output(message)
    elif mode == "+":  # raw
        local = get_memory(db, chan, word)
        default = get_memory(db, defaultchan, word)
        if local:
            output("[local] " + local)
        if default:
            output("[global] " + default)
    else:
        output(filters(retrieve(word, chan), variables, filterhistory))
