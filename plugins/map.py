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


for row in csv.reader(open("mc_1.6.2.csv")):
    if len(row) < 3:
        continue
    #if row[2] == '*' or row[1] == '*':
        #continue
    old[row[1]] = row[2]
    new[row[2]] = row[1]
    names[row[2]] = row[0]
    rnames[row[0].lower()] = row[2]
    descrs[row[2]] = row[5] if len(row) == 6 else row[3] if len(row) == 4 else '*'


@hook.command
def mapo(text, notice=None):
    "old client to new"
    try:
        o = text.strip()
        n = old[o]

        descr = descrs[n]
        name = names[n]
        notice("%s: %s -> %s: %s" % (name, o, n, descr))
    except Exception, e:
        print e
        notice("None")


@hook.command
def mapn(text, notice=None):
    "new client to old"
    try:
        n = text.strip()
        o = new[n]
        descr = descrs[n]
        name = names[n]
        notice("%s: %s -> %s: %s" % (name, o, n, descr))
    except Exception, e:
        print e
        notice("None")


@hook.command
def map(text, notice=None):
    "names to old and new"
    try:
        rname = text.strip().lower()
        n = rnames[rname]
        name = names[n]
        o = new[n]
        descr = descrs[n]

        notice("%s: %s -> %s: %s" % (name, o, n, descr))
    except Exception, e:
        print e
        notice("None")


@hook.command
def grep(text, notice=None):
    "calls grep on javamap for 1.5 to 1.6.4 - thanks mcp!"
    try:
        p = subprocess.Popen(["egrep", "-e", text, "15-164"], stdout=subprocess.PIPE)
        lines = p.stdout.readlines()
        if len(lines) > 6:
            notice("Only displaying first 6.")
        for line in itertools.islice(lines, 6):
            notice(line.strip())
            time.sleep(1)
    except:
        notice("Error")
