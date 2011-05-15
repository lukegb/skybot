from util import hook, http
import urlhistory
import re
import repaste

titler = re.compile(r'(?si)<title>(.+?)</title>')

@hook.regex(r".*(minecraftforum\.net/viewtopic\.php\?[\w=&]+)\b.*")
def regex(inp, say=None):
    "titles minecraftforum urls"
    t=title("http://"+inp.group(1)).replace(" - Minecraft Forums","")
    if t=="Login":
        return
    say("mcforum title: "+t)

@hook.command
@hook.command("t")
def title(inp, db=None, chan=None):
    ".title <url> - get title of <url>"
    if inp == '^':
        urlhistory.db_init(db)
        rows = db.execute("select url from urlhistory where chan = ? order by time desc limit 1", (chan,))
        if not rows.rowcount:
            return "No url in history."

        inp = rows.fetchone()[0]

    match = titler.search(http.get(inp))

    if not match:
        return "Error: no title"

    rawtitle = match.group(1)

    title = repaste.decode_html(rawtitle)
    title = " ".join(title.split())

    return title
