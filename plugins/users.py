
from util import hook

import yaml, json
import os

thedict = {"users": {"test": {"perms": ["test"]}}}

def load(persistdir):
	"loads ... it."
	 global thedict
	 thedict = {}
	 f = persistdir + "/users"
	 if os.path.exists(f+".yml"):
		 thedict = yaml.load(open(f+".yml"))
		 elif os.path.exists(f+".json"):
			 thedict = json.load(open(f+".json"))
			 def save(persistdir):
				 "opposite of save? (I mean load)"
				 os.makedirs(persistdir) #should be do-nothing?
				 yaml.dump(thedict, open(persistdirs + "/users.yml"))

#load()

				 def check(user, perm):
					 if user == "lahwran":
					 return True
					 elif user in thedict["users"].keys():
						 usr = thedict["users"][user]
						 if "perms" in usr and perm in usr["perms"]:
						 return True
						 elif "groups" in usr:
						 grps=usr["groups"]
						 for i in grps:
						 if "groups" in thedict and i in thedict["groups"] and "perms" in thedict["groups"] and perm in thedict["groups"]["perms"]:
						 return True

						 return False

						 @hook.command
						 def users(inp, bot=None, input=None, say=None, notice=None, nick=None):
							 ".users [command] - control and query permissions system. .users help for help."
							   spl = inp.split(" ")
							   if not len(spl):
								   spl=["help"]
	c = spl[0]
		  #say(c)
		  if c == "help":
		  return "yeah uh no help yet"
		  elif c == "info":
		  if not check(nick, "users.info"):
			  return "imadamabadabada"
			  u = spl[1]
			  outlines = []
			  outlines.append("User "+u+":")
			  for ttype in ["perms", "groups"]:
			  outlines.append(ttype+":")
			  if u in thedict["users"] and ttype in thedict["users"][u]:
			  lst = thedict["users"][u][ttype]
			  outlines.extend(["+ "+(", ".join(lst[i:i+8])) for i in range(0,len(lst),8)])

			  for i in outlines:
notice(i)
	else:
	say("whahuh?")
