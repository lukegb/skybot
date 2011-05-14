from util import hook, http

import urllib
import mechanize
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

def paste_gist(text, user=None, syntax="", description=""):
    br = mechanize.Browser()
    br.open('https://gist.github.com')

    br.select_form(nr=1)
    br.form.find_control('file_contents[gistfile1]').value = text

    if syntax:
        br.form.find_control('file_name[gistfile1]').value = "repaste."+syntax
    if description:
        br.form.find_control('description').value = description
    br.submit(nr=0)

    return br.geturl()

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
        return " ".join(sorted(pasters.keys()))

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
    
    args["text"] = scrape_mibpaste(parts[0])
    pasted = paster(**args)

    return pasted


