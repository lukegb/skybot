import feedparser
import time
try:
    import cPickle as pickle
except ImportError:
    import pickle

def get_bukkit(maxents=5, onlynew=True):
    feed = 'http://leaky.bukkit.org/projects/bukkit/activity.atom'
    fd = feedparser.parse(feed)
    fd.entries = fd.entries[:maxents]
    if onlynew:
        return get_new_entries(fd)
    else:
        return fd

storeplace = '/home/ircbot/lastid.txt'

def get_new_entries(feed):
    try:
        with open(storeplace, 'r') as f:
            pdf = pickle.load(f)
    except:
        pdf = {}
    import hashlib
    mh =hashlib.sha256()
    mh.update(feed.feed.id)
    feeduid = mh.hexdigest()
    if feeduid not in pdf:
        pdf[feeduid] = 0
    maxout = newout = pdf[feeduid]
    outentries = []
    for ent in feed.entries[:5]:
        nt = time.mktime(ent.updated_parsed)
        if nt > maxout:
            if nt > newout:
                newout = nt
            outentries.append(ent) 
    pdf[feeduid] = newout
    with open(storeplace, 'w') as f:
        pickle.dump(pdf, f)
    feed.entries = outentries
    return feed


def pretty_ents(inp):
    import pretty, datetime
    outa = []
    for ent in inp.entries:
        username = ent.author[ent.author.find('(')+1:ent.author.find(')')]
        thistime = datetime.datetime.fromtimestamp(time.mktime(ent.updated_parsed))
        prettytime = pretty.date(thistime)
        form = 'Leaky Bukkit: %s (%s) - %s - %s' % (ent.title, username, prettytime, ent.links[0].url)
        outa.append(form)
    return outa

    
if __name__ == '__main__':
    print pretty_ents(get_bukkit())

