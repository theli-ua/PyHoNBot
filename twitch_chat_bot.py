import logging

import irc.client

import irc.bot
import irc.strings

from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

irc.client.log.addHandler(logging.StreamHandler())
irc.client.log.setLevel(logging.DEBUG)

class TwitchChatBot(irc.bot.SingleServerIRCBot):

    _pubmsgCallbacks = []
    _joinCallbacks = []
    _partCallbacks = []

    def __init__(self, channel, nickname, server, password, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def send_to_channel(self, msg):
        self.channel_connection.privmsg(self.channel, msg)

    # test
    def send_names(self, c=None):
        connection_to_use = c if c is not None else self.channel_connection
        connection_to_use.names([self.channel])
        #connection_to_use.send_raw("/NAMES " + self.channel)

    # test
    def on_join(self, c, e):
        print("Twitch: got join from " + e.source + "!")
        for handler in self._joinCallbacks:
            handler(c, e)
        if e.source == '{0}!{1}@{2}.tmi.twitch.tv'.format(self._nickname, self._nickname, self._nickname):
            self.send_names(c)
            # c.names() # [self.channel]

    #test
    def on_part(self, c, e):
        print("Twitch: got part from " + e.source + "!")
        for handler in self._partCallbacks:
            handler(c, e)

    #test
    def on_namreply(self, c, e):
        print("Twitch: got namreply! Names are: " + str(e.arguments))

    #test
    def on_cap(self, c, e):
        print("Twitch: got cap!")
        c.join(self.channel)

    def on_welcome(self, c, e):
        self.channel_connection = c
        print("Twitch: got welcome!")
        c.cap('REQ', ":twitch.tv/membership")

    def on_privmsg(self, c, e):
        print("got privmsg")
        self.do_command(e, e.arguments[0])

    def add_on_pubmsg(self, h):
        self._pubmsgCallbacks.append(h)

    def add_on_join(self, h):
        self._joinCallbacks.append(h)

    def add_on_part(self, h):
        self._partCallbacks.append(h)

    def on_pubmsg(self, c, e):
        print("got pubmsg")
        a = e.arguments[0].split(":", 1)
        for handler in self._pubmsgCallbacks:
            handler(c, e)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def on_dccmsg(self, c, e):
        # non-chat DCC messages are raw bytes; decode as text
        text = e.arguments[0].decode('utf-8')
        c.privmsg("You said: " + text)

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        print("do command "+cmd)
        nick = e.source.nick
        c = self.connection

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = sorted(chobj.users())
                c.notice(nick, "Users: " + ", ".join(users))
                opers = sorted(chobj.opers())
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = sorted(chobj.voiced())
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        elif cmd == "dcc":
            dcc = self.dcc_listen()
            c.ctcp("DCC", nick, "CHAT chat %s %d" % (
                ip_quad_to_numstr(dcc.localaddress),
                dcc.localport))
        else:
            c.notice(nick, "Not understood: " + cmd)
