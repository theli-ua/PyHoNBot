#!/usr/bin/env python
"""

honbot - A Heroes Of Newerth chatserver Bot
Copyright 2011, Anton Romanov

Heavily inspired by phenny:

__init__.py - Phenny Init Module
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

"""

import sys, os, time, threading, signal,traceback
import bot
from hon import packets

from twitch_chat_bot import TwitchChatBot

class Watcher(object): 
   # Cf. http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
   def __init__(self):
      self.child = os.fork()
      if self.child != 0: 
         self.watch()

   def watch(self):
      try: os.wait()
      except KeyboardInterrupt:
         self.kill()
      sys.exit()

   def kill(self):
      try: os.kill(self.child, signal.SIGKILL)
      except OSError: pass

def twitch_source_to_nick(source):
   return source.split('@')[0].split('!')[0]

def run_honbot(config): 
   if hasattr(config, 'delay'): 
      delay = config.delay
   else: delay = 20

   try: Watcher()
   except Exception, e: 
      print >> sys.stderr, 'Warning:', e, '(in __init__.py)'

   twitch_bot = TwitchChatBot('#'+config.twitch_nick.lower(), config.twitch_nick, "irc.twitch.tv", config.twitch_oauth_password, 6667)

   p = None

   def post_to_twitch(msg):
      twitch_bot.send_to_channel(msg)
   
   def connect(config): 
      p = bot.Bot(config, post_to_twitch)
      #t = threading.Thread(target=p.run)
      #t.start()
      p.run()
      print "done with connect!"
      return p
   
   def handle_pubmsg(c, e):
      print("Twitch: got pubmsg with c="+str(c)+", e="+str(e)+" with type="+e.type+", source="+e.source+", target="+e.target+", arguments="+str(e.arguments))
      p.write_packet(packets.ID.HON_SC_WHISPER, p.config.owner, twitch_source_to_nick(e.source) + ": " + ";".join(e.arguments))

   def handle_join(c, e):
      # print("Twitch: got pubmsg with c="+str(c)+", e="+str(e)+" with type="+e.type+", source="+e.source+", target="+e.target+", arguments="+str(e.arguments))
      p.write_packet(packets.ID.HON_SC_WHISPER, p.config.owner, twitch_source_to_nick(e.source) + " joined your channel!")

   def handle_part(c, e):
      # print("Twitch: got pubmsg with c="+str(c)+", e="+str(e)+" with type="+e.type+", source="+e.source+", target="+e.target+", arguments="+str(e.arguments))
      p.write_packet(packets.ID.HON_SC_WHISPER, p.config.owner, twitch_source_to_nick(e.source) + " left your channel!")

   twitch_bot.add_on_pubmsg(handle_pubmsg)
   twitch_bot.add_on_join(handle_join)
   twitch_bot.add_on_part(handle_part)
   twitch_bot._connect()
  
   while True: 
      try: 
          print("connecting!")
          p = connect(config)
          #names_sent = time.time()
          while True:
              #end = time.time()
              #if (end - names_sent) > 10:
              #    twitch_bot.send_names()
              #    names_sent = time.time()
              p.loop()
              twitch_bot.reactor.process_once(timeout=1)
		  
      except KeyboardInterrupt: 
          sys.exit()
      except:
          print(sys.exc_type,sys.exc_value)
          print(sys.exc_traceback)
          print(sys.exc_info())
          traceback.print_exc(file=sys.stdout)
          pass

      if not isinstance(delay, int): 
         break

      warning = 'Warning: Disconnected. Reconnecting in %s seconds...' % delay
      print >> sys.stderr, warning
      time.sleep(delay)

def run(config): 
   t = threading.Thread(target=run_honbot, args=(config,))
   if hasattr(t, 'run'): 
      t.run()
   else: t.start()

if __name__ == '__main__': 
   print __doc__
