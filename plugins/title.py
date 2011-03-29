from util import hook, http
import re
titler = re.compile(r'<title>(.+?)</title>')

@hook.regex(r".*(minecraftforum\.net/viewtopic\.php\?[\w=&]+)\b.*")
def regex(inp, say=None):
    "titles minecraftforum urls"
    t=title("http://"+inp.group(1)).replace(" - Minecraft Forums","")
    if t=="Login":
        return
    say("mcforum title: "+t)

@hook.command
@hook.command("t")
def title(inp):
    ".title <url> - get title of <url>"
    return titler.search(http.get(inp)).group(1)
