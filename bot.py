#!/usr/bin/env python

a = 34123

import os
import Queue
import sys
import time
import select

sys.path += ['plugins']  # so 'import hook' works without duplication
sys.path += ['lib']
os.chdir(sys.path[0] or '.')  # do stuff relative to the install directory


class Bot(object):
    pass


bot = Bot()
print 'Loading plugins'

# bootstrap the reloader
eval(compile(open(os.path.join('core', 'reload.py'), 'U').read(),
    os.path.join('core', 'reload.py'), 'exec'))
reload(init=True)

config()
if not hasattr(bot, 'config'):
    exit()

print 'Connecting to IRC'

bot.conns = {}

try:
    for name, conf in bot.config['connections'].iteritems():
        bot.conns[name] = IRC(main, conf['server'], conf['nick'], conf=conf, port=conf.get('port', 6667), channels=conf['channels'])
#        if conf.get('ssl'):
#            bot.conns[name] = SSLIRC(conf['server'], conf['nick'], conf=conf,
#                    port=conf.get('port', 6667), channels=conf['channels'],
#                    ignore_certificate_errors=conf.get('ignore_cert', True))
#        else:
#            bot.conns[name] = IRC(conf['server'], conf['nick'], conf=conf,
#                    port=conf.get('port', 6667), channels=conf['channels'])
except Exception, e:
    print 'ERROR: malformed config file', e
    sys.exit()

bot.persist_dir = os.path.abspath('persist')
if not os.path.exists(bot.persist_dir):
    os.mkdir(bot.persist_dir)

print 'Running main loop'
socks = [s[1].conn.socket for s in bot.conns.iteritems()]
sockmap = {}
for conn in bot.conns.iteritems():
    sockmap[conn[1].conn.socket.fileno()] = conn[1]
while True:
    reload()
    config()
    r, w, x = select.select(socks, [], [], 0.2)
    for c in r:
        if not sockmap[c.fileno()].loop_read():
            socks.remove(c)
            if len(socks) == 0:
                break
    for c in socks:
        sockmap[c.fileno()].loop_write()

#while True:
#    reload()  # these functions only do things
#    config()  # if changes have occured
#
#    for conn in bot.conns.itervalues():
#        try:
#            out = conn.out.get_nowait()
#            main(conn, out)
#        except Queue.Empty:
#            pass
#    while all(conn.out.empty() for conn in bot.conns.itervalues()):
#        time.sleep(.1)
