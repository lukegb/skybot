from util import hook, http

import urllib
import random
import urllib2
import htmlentitydefs
import re

def unescape_html(text):
    return re.sub("&("+"|".join(htmlentitydefs.entitydefs.keys())+");",
                  lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), text)

def scrape_mibpaste(url):
    pagesource = http.get(url)
    rawpaste = re.search(r'(?s)(?<=<body>\n).+(?=<hr>)', pagesource).group(0)
    filterbr = rawpaste.replace("<br />", "")
    unescaped = unescape_html(filterbr)
    stripped = unescaped.strip()

    return stripped

def scrape_pastebin(url):
    id = re.search(r'http://(?:www\.)?pastebin.com/([a-zA-Z0-9]+)$', url).group(1)
    rawurl = "http://pastebin.com/raw.php?i="+id
    text = http.get(rawurl)

    return text

scrapers = {
    r'mibpaste\.com': scrape_mibpaste,
    r'pastebin\.com': scrape_pastebin
}

def paste_sprunge(text, syntax=None, user=None):
    data = urllib.urlencode({"sprunge":text})
    url = urllib2.urlopen("http://sprunge.us/", data).read().strip()

    if syntax:
        url += "?"+syntax

    return url

def paste_ubuntu(text, user=None, syntax='text'):
    data = urllib.urlencode({"poster": user,
                             "syntax": syntax,
                             "content":text})

    return urllib2.urlopen("http://paste.ubuntu.com/", data).url

def paste_gist(text, user=None, syntax=None, description=None):
    data = {
        'file_contents[gistfile1]': text,
        'action_button': "private"
    }

    if description:
        data['description'] = description

    if syntax:
        data['file_ext[gistfile1]'] = "."+syntax

    req = urllib2.urlopen('https://gist.github.com/gists', urllib.urlencode(data).encode('utf8'))
    return req.url

def paste_strictfp(text, user=None, syntax="plain"):
    data = urllib.urlencode(dict(
        language = syntax,
        paste = text,
        private = "private",
        submit="Paste"))
    req = urllib2.urlopen("http://paste.strictfp.com/", data)
    return req.url


pasters = dict(
    ubuntu=paste_ubuntu,
    sprunge=paste_sprunge,
    gist=paste_gist,
    strictfp=paste_strictfp
)


@hook.command
def repaste(inp, user=None):
    ".repaste list|[provider] [syntax] <mibpasteurl> -- scrape mibpaste, reupload on given pastebin"

    parts = inp.split()

    if parts[0] == 'list':
        return " ".join(pasters.keys())

    paster = paste_gist
    args = {}

    if not parts[0].startswith("http"):
        p = parts[0].lower()

        if p in pasters:
            paster = pasters[p]
            parts = parts[1:]

    if not parts[0].startswith("http"):
        p = parts[0].lower()
        parts = parts[1:]

        args["syntax"] = p

    if len(parts) > 1:
        return "PEBKAC"

    args["user"] = user
    
    url = parts[0]

    for pat, scraper in scrapers.iteritems():
        print "matching "+repr(pat)+" "+url
        if re.search(pat, url):
            break
    else:
        return "No scraper for given url"

    args["text"] = scraper(url)
    pasted = paster(**args)

    return pasted


