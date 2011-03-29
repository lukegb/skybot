"""
remember.py: written by Scaevolus 2010
"""

from util import hook
import pyexec

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
    if not inp.split(" ")[0]=="." and ((chan.startswith('#') and localpm) or not localpm):
        chan = "default"
        local=False
    elif (chan.startswith('#') and localpm) or not localpm:
        inp=" ".join(inp.split(" ")[1:])
        local=True
    else:
        local=True
    return local, chan, inp.strip()
@hook.command
def no(inp, nick='', chan='', db=None):
    ".no <word> is <data> -- remaps word to data"
    
    local, chan, inp = checkinp(chan, inp, True)
    
    db_init(db)
    try:
        head, tail = inp.split(" ", 1)
    except ValueError:
        return no.__doc__
    if tail.startswith("is "):
        tail=" ".join(tail.split(" ")[1:])
    
    

    data = get_memory(db, chan, head)
    
    if not data:
        return "but '%s' doesn't exist!" % head.replace("'", "`")
    
    db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, head, tail, nick))
    print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, head, tail, nick))
    db.commit()
    return 'forgetting "%s", remembering this instead.' % \
                data.replace('"', "''")

@hook.command
#@hook.regex("([^ ]*)")
def remember(inp, nick='', chan='', db=None, input=None):
    ".remember [.] <word> is <data> -- maps word to data in the memory, '.' means here only"
    db_init(db)
    
    local, chan, inp = checkinp(chan, inp, True)
    
        
    try:
        head, tail = inp.split(" ", 1)
    except ValueError:
        return remember.__doc__
    if tail.startswith("is "):
        tail=" ".join(tail.split(" ")[1:])
    
    

    data = get_memory(db, chan, head)
    
    if data and not data.startswith("<forgotten>"):
        return "but '%s' already means something else!" % head.replace("'", "`")
    elif data and data.startswith("<forgotten>"):
        input.notice(("[local]" if local else "") + "permanently deleting "+repr(data)+" to accomodate this")
    
    db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, head, tail, nick))
    print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, head, tail, nick))
    db.commit()
    return ("[local]" if local else "") + 'done.'


@hook.command
def forget(inp, chan='', db=None, nick=''):
    ".forget [.] <word> -- forgets the mapping that word had, '.' means here only"
    local, chan, inp = checkinp(chan, inp, True)
    db_init(db)
    
    
    data = get_memory(db, chan, inp)

    if data and not data.startswith("<forgotten>"):
        db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, inp, "<forgotten>"+data, nick))
        print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, inp, "<forgotten>"+data, nick))
        #db.execute("delete from memory where chan=? and word=lower(?)",
        #           (chan, inp))
        db.commit()
        return ("[local]" if local else "") + ('forgot `%s`' % data.replace('`', "'"))
    elif data:
        return ("[local]" if local else "") + "I already archived that."
    else:
        return ("[local]" if local else "") + "I don't know about that."

@hook.command
def unforget(inp, chan='', db=None, nick=''):
    ".unforget [.] <word> -- re-remembers the mapping the word had before, '.' means here only "
    db_init(db)
    
    local, chan, inp = checkinp(chan, inp, True)
        
    data = get_memory(db, chan, inp)
    
    if data and data.startswith("<forgotten>"):
        db.execute("replace into memory(chan, word, data, nick) values"
               " (?,lower(?),?,?)", (chan, inp, data.replace("<forgotten>","").strip(), nick))
        print "replace into memory(chan, word, data, nick) values (?,lower(?),?,?)", repr((chan, inp, data.replace("<forgotten>","").strip(), nick))
        db.commit()
        return ("[local]" if local else "") + ('unforgot `%s`' % data.replace('`', "'"))
    elif data:
        return ("[local]" if local else "") + "I still remember that."
    else:
        return ("[local]" if local else "") + "I never knew about that."
    

@hook.regex(r'^[?!](.+)')
def question(inp, chan='', say=None, db=None, input=None, nick="", me="", bot=None, oldchan=None):
    "!factoid -- shows what data is associated with word"
    def recurse():
        if chan != "default":
            question(inp, "default", say, db, input, nick, me, bot, chan)
#    if nick == "lahwran":
#        chan = "#risucraft"
    db_init(db)
    whole=False
    #print inp, input
    #if input.msg.startswith("?"):
    #    return "do you mean !"+inp.group(1).strip()
    match = inp.group(1).strip()
    chans = ["#risucraft", "#lahwran"]
    if input.msg.startswith("!") and nick != "lahwran" and chan.lower() not in chans and oldchan.lower() not in chans:
    	
	return
    if match.startswith("+"):
        match=match[1:]
        whole=True
    user=""
    
    mainout = say
    def pipeout(s):
        say(user+": "+s)
    def redirout(s):
        input.conn.cmd('NOTICE', [user, nick+" sent: "+s])
    if "|" in match:
        spl=match.split("|")
        match=spl[0].strip()
        user=spl[1].strip()
        mainout = pipeout
    elif ">" in match:
        spl=match.split(">")
        match=spl[0].strip()
        user=spl[1].strip()
        mainout = redirout
    else:
        match=match.strip()
    
    data = get_memory(db, chan, match.split(" ")[0].strip())
    if whole:
        say("["+chan+"]"+str(data))
        recurse()
        return
    counter = 0
    pyarg =" ".join(match.strip().split(" ")[1:])
    while data and data.startswith("<pyexec>") and counter<=3:
        counter += 1
        data=pyexec.python("inp="+repr(pyarg)+";"+data[len("<pyexec>"):].strip())
    if data == None:
        recurse()
        return
    if chan != "default":
        data = data.replace("$chan", chan)
    elif oldchan != None:
        data = data.replace("$chan", oldchan)
    data = data.replace("$user", nick)


    aliastrail = ["<alias>"+match]
    while data.startswith("<alias>"):
        if data in aliastrail:
            say("'"+match+"' alias trail forms a loop for channel "+chan+"! "+repr(aliastrail))
            recurse()
            return
        aliastrail.append(data)
        data = get_memory(db, chan, data.replace("<alias>","").strip())
        if data == None or data.startswith("<forgotten>"):
            say("oops, we struck out on the last one for channel "+chan+": "+repr(aliastrail))
            recurse()
            return
    if data.startswith("<forgotten>"):
        recurse()
        return
    elif data.startswith("<reply>"):
        mainout(data.replace("<reply>","").strip())
    elif not data.startswith("<action>"):   
        mainout(match.split(" ")[0].strip()+" is "+data)
    elif data.startswith("<action>") and mainout == say:
        me(data.replace("<action>","").strip())
    #else:
    #    say("Sorry, I don't know anything about "+match)
