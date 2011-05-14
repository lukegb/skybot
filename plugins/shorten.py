from util import hook, http
import urllib
import urllib2
import httplib
import time
import urlparse
import re

re_adfly = re.compile(r'var url = \'([^\']+)\'')

@hook.command
def isgd(inp):
    ".isgd <url> -- shorten link using is.gd"

    data = urllib.urlencode(dict(format="simple",url=inp))

    shortened = urllib2.urlopen("http://is.gd/create.php", data).read()

    return shortened

@hook.command
def expand(inp):
    ".expand <shorturl> -- expand link shortened url"

    # try HEAD
    parts = urlparse.urlsplit(inp)
    conn = httplib.HTTPConnection(parts.hostname)
    conn.request('HEAD',parts.path)
    resp = conn.getresponse()
    location = resp.msg.getheader("Location")

    if not location:
        return inp

    expandedparts = urlparse.urlsplit(location)
    quoted = expandedparts._replace(path=urllib.quote(expandedparts.path))
    url = quoted.geturl()

    return url

@hook.command
def deadfly(inp):
    ".deadfly <adf.ly url> -- scrapes link shortened by adf.ly"
    parts = urlparse.urlsplit(inp)
    parts = parts._replace(netloc=parts.netloc + ".nyud.net")
    url = urlparse.urlunsplit(parts)

    try:
        text = urllib2.urlopen(url, timeout=15).read()
    except:
        return "Timeout"

    return re_adfly.search(text).group(1)
