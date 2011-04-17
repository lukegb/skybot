"""
remember.py: written by Scaevolus 2010, modified by lahwran 2011
"""

from util import hook
import pyexec
import users
import re

defaultchan = "default" #TODO: creates a security hole, username "default" can alter global factoids

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
        chan = defaultchan
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
    
redirect_re = re.compile(r'([|><])\s*(\S*)\s*$')
word_re = re.compile(r'^([+-]?)(\S+)')
filter_re = re.compile(r'^\s*[<]([^>]*)[>]\s*(.*)\s*$')
#args is what is left over after removing these

maxdepth=4

@hook.regex(r'^[?!](.+)') #groups: (mode,word,args,redirectmode,redirectto)
def question(inp, chan='', say=None, db=None, input=None, nick="", me=None, bot=None, notice=None):
    "!factoid -- shows what data is associated with word"
        
    filterhistory = [] #loop detection, maximum recursion depth(s)
    
    def varreplace(orig, variables):
        for i in variables.keys():
            orig = orig.replace("$"+i,variables[i])
        return orig
            
            
    def filters(orig, variables, filterhistory):
        if len(filterhistory)+1 > 4:
            return "Hit max recursion depth: ["+orig[:30]+"...]"
        if orig in filterhistory:
            return "Going in a circle: ["+orig[:30]+"...]"
        filterhistory.append(orig)
        
        filtermatch = filter_re.search(orig)
        if filtermatch:
            filtername = filtermatch.group(1).lower()
            filterinp = filtermatch.group(2)
            if filtername == "alias":
                return filters(retrieve(filterinp, chan), variables, filterhistory)
            elif filtername == "reply":
                return varreplace(filterinp, variables)
            elif filtername == "action":
                return (varreplace(filterinp, variables), me)
            elif filtername == "pyexec":
                preargs = ""
                for i in variables.keys():
                    preargs+=i+"="+repr(str(variables[i]))+".encode('utf8');"
                print preargs+filterinp
                return filters(pyexec.python(preargs+filterinp), variables, filterhistory)
        else:
            return variables["word"]+" is "+varreplace(orig, variables)
            
            
    def retrieve(word, chan):
        ret = get_memory(db, chan, word)
        if ret and not ret.startswith("<forgotten>"):
            return ret
        ret = get_memory(db, defaultchan, word)
        if ret and not ret.startswith("<forgotten>"):
            return ret
        return ""
            
    #TODO: hardcoded permission
    if nick=="citricsquid" and chan.startswith("#"):
        return
    db_init(db)
    whole=False
    
    def splitgroups(inp):
        "returns (mode, word, args, redir, redirto)"
        words = inp.group(1)
        ret = []
        wordmatch = word_re.search(words)
        words=words[wordmatch.end():]
        ret.append(wordmatch.group(1))
        ret.append(wordmatch.group(2).lower())
        
        redirect = ''
        redirectto = ''
        redirectmatch = redirect_re.search(words)
        if redirectmatch:
            redirect = redirectmatch.group(1)
            redirectto = redirectmatch.group(2)
            words=words[:redirectmatch.start()]
        ret.append(words.strip())
        ret.append(redirect)
        ret.append(redirectto)
        return ret
    (mode, word, args, redir, redirto) = splitgroups(inp)
    def output(s, redir, redirto, input, special=None):
        if redir==">" and not special:
            input.conn.cmd('NOTICE', [redirto, nick+" sent:"+s])
        elif redir == "|" and not special:
            input.say(redirto+": "+s)
        elif redir == "<" and not special:
            input.notice(s)
        elif special:
            special(s)
        else:
            input.say(s)
    variables = {"chan":    chan, 
                 "user":    nick, 
                 "nick":    input.conn.nick,
                 "target":  redirto,
                 "inp":     args,
                 "word":    word}
    if mode == "-": #information
        message = word+" is "
        local = db.execute("select nick from memory where chan=? and word=lower(?)",(chan, word)).fetchone()
        if local:
            message += "locally set by "+local[0]
        default = db.execute("select nick from memory where chan=? and word=lower(?)",(defaultchan, word)).fetchone()
        if local and default:
            message += " and "
        if default:
            message += "globally set by "+default[0]
        if local or default:
            output(message, redir, redirto, input)
    elif mode == "+": #raw
        local = get_memory(db, chan, word)
        default = get_memory(db, defaultchan, word)
        if local:
            output("[local] "+local, redir, redirto, input)
        if default:
            output("[global] "+default, redir, redirto, input)
    else:
        result = filters(retrieve(word, chan), variables, filterhistory)
        if type(result) == tuple:
            output(result[0], redir, redirto, input, result[1]) #special for things like /me
        else:
            output(result, redir, redirto, input)
        
        
        
    
"""
    def output(s):
        
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
        if data:
            mainout("["+chan+"]"+str(data))
        recurse()
        return
    counter = 0
    pyarg =" ".join(match.strip().split(" ")[1:])
    while data and data.startswith("<pyexec>") and counter<=3:
        counter += 1
        data=pyexec.python("inp="+repr(pyarg)+".encode('utf8');"+data[len("<pyexec>"):].strip())
    if data == None:
        recurse()
        return


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
    #    say("Sorry, I don't know anything about "+match)"""
