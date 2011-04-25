# vim: encoding=utf8 :
from util import hook
import subprocess
import itertools
import time
import csv
from collections import defaultdict

old = defaultdict(lambda: '*')
new = defaultdict(lambda: '*')
descrs = defaultdict(lambda: '*')
names = defaultdict(lambda: '*')
rnames = defaultdict(lambda: '*')

#old13 = {}
#new13 = {}


for row in csv.reader(open("1.3.csv")):
    if len(row) < 3:
        continue
    #if row[2] == '*' or row[1] == '*':
        #continue
    old[row[1]] = row[2]
    new[row[2]] = row[1]
    names[row[2]] = row[0]
    rnames[row[0].lower()] = row[2]
    descrs[row[2]] = row[5] if len(row)==6 else row[3] if len(row) == 4 else '*'

#for line in open("121_131_classes").readlines():
    #on = line.strip().split(" ")
    #if len(on) != 2:
        #print repr(on)
    #else:
        #o,n = on
        #old13[o] = n
        #new13[n] = o

#@hook.command
#def mapo(input):
    #"client 1.2_02 -> 1.3_01"
    #try:
        #o = input.strip()
        #n = old[o]
        #new = old13[o]

        #descr = descrs[n]
        #name=names[n]
        #return "%s: %s -> %s: %s" % (name, o,new,descr)
    #except:
        #return "None"

@hook.command
def mapo(text, notice=None):
    "old client to new"
    try:
        o = text.strip()
        n = old[o]

        descr = descrs[n]
        name=names[n]
        notice( "%s: %s -> %s: %s" % (name, o,n,descr))
    except Exception, e:
        print e
        notice( "None")

@hook.command
def mapn(text, notice=None):
    "new client to old"
    try:
        n = text.strip()
        o = new[n]
        descr = descrs[n]
        name = names[n]
        notice( "%s: %s -> %s: %s"%(name, o,n,descr))
    except Exception, e:
        print e
        notice( "None")

#@hook.command
#def mapn(input):
    #"client 1.3_01 -> 1.2_02"
    #try:
        #new1 = input.strip()
        #o1 = new13[new1]
        #n = old[o1]
        #descr = descrs[n]
        #name = names[n]
        #return "%s: %s -> %s: %s"%(name, o1,new1,descr)
    #except:
        #return "None"

@hook.command
def map(text, notice=None):
    "MCP names to 1.2_02 and 1.3_01"
    try:
        rname = text.strip().lower()
        n = rnames[rname]
        name = names[n]
        o = new[n]
        descr = descrs[n]

        notice( "%s: %s -> %s: %s" % (name, o,n,descr))
    except Exception, e:
        print e
        notice("None")

@hook.command
def grep(text, notice=None):
    "maps "
    try:
        p = subprocess.Popen(["egrep", "-e", text, "141-151"], stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        if len(lines) > 6:
            notice("Only displaying first 6.")
        for line in itertools.islice(lines, 6):
            notice(line.strip())
            time.sleep(1)
    except:
        notice("Error")
        


#@hook.command
#def map(input):
    #"mcp names to obfuscated"
    #try:
        #rname = input.strip().lower()
        #n = rnames[rname]
        #name = names[n]
        #o = new[n]
        #descr = descrs[n]

        #return "%s: %s -> %s: %s" % (name, o,n,descr)
    #except:
        #return "None"
