from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import functools

# TODO
# Server print
# Server logs
# Private messages
# Security
# High scalability
# federation
# special emoticons
# web client
# mobile client

WELCOME_STR = "Welcome to the XYZ chat server"
WELCOME_USER_STR = "Welcome, %s!"
ASK_LOGIN_STR = "Login Name?"
NAME_TAKEN_STR = "Sorry, name taken."
NAME_RESERVED_STR = "Sorry, name reserved."
USER_JOINED_ROOM_STR = "* new user joined {}: {}"
USER_LEFT_ROOM_STR = "* user has left {}: {}"
SHOW_USER_STR = "* %s\n"
SHOW_ROOMS_STR = "Active rooms are:\n"
SHOW_ROOM_STR = "* {} ({})\n"
END_OF_LIST_STR = "end of list"
JOIN_ROOM_STR = "Entering room: %s"
DEFAULT_ROOM_STR = "DEFAULT"
QUIT_STR = "BYE"
JOIN_ROOM_ERR_STR = "You are not in a room.\nType /join <room> to join a room.\nType /rooms to see the available rooms"

class Chat(LineReceiver):

    def __init__(self, rooms):
        self.rooms = rooms
        self.currentRoom = None
        self.name = None
        self.state = "GETNAME"
        self.actions = {"/users": self.handle_USERS, "/quit": self.handle_QUIT, "/leave": self.handle_LEAVE, "/rooms": self.handle_ROOMS, "/join": self.handle_JOIN}
    def connectionMade(self):
        self.sendLine("%s\n%s" % (WELCOME_STR, ASK_LOGIN_STR))

    def connectionLost(self, reason):
        if self.currentRoom:
            if self.name in self.getUsers():
                del self.getUsers()[self.name]

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
        if not self.nameIsFree(name):
            self.sendLine(NAME_TAKEN_STR)
        elif name in self.actions.keys():
            self.sendLine(NAME_RESERVED_STR)
        else:
            self.name = name
            self.sendLine(WELCOME_USER_STR % self.name)
            self.handle_JOIN(DEFAULT_ROOM_STR)
            self.state = "CHAT"

    def handle_CHAT(self, message):
        if message in self.actions:
            self.actions[message](message)
            return
        words = message.split()
        if len(words) > 1 and words[0] in self.actions:
            self.actions[words[0]](" ".join(words[1:]))
            return
        else:
            self.sendMessage(message)

    def handle_USERS(self, message = None):
        if self.currentRoom:
            usersStr = ""
            for name, protocol in self.getUsers().iteritems():
                usersStr += SHOW_USER_STR % self.formatUsername(name)
            usersStr += END_OF_LIST_STR
            self.sendLine(usersStr)
        else:
            self.sendLine(JOIN_ROOM_ERR_STR)

    def handle_ROOMS(self, message = None):
        roomsStr = SHOW_ROOMS_STR
        for room in self.rooms:
            roomsStr += SHOW_ROOM_STR.format(room, len(self.rooms[room]))
        roomsStr += END_OF_LIST_STR
        self.sendLine(roomsStr)

    def handle_QUIT(self, message = None):
        self.send_everyone(USER_LEFT_ROOM_STR.format(self.currentRoom, self.name))
        if self.currentRoom:
            if self.name in self.getUsers():
                del self.getUsers()[self.name]
        self.sendLine(QUIT_STR)
        self.transport.loseConnection()

    def handle_JOIN(self, message):
        if self.currentRoom:
            self.handle_LEAVE()

        room = message
        self.currentRoom = room
        if room not in self.rooms:
            self.rooms[room] = {}
        self.getUsers()[self.name] = self
        self.sendLine(JOIN_ROOM_STR % room)
        self.send_everyone(USER_JOINED_ROOM_STR.format(self.currentRoom, self.name))

        self.handle_USERS()

    def handle_LEAVE(self, message = None):
        self.send_everyone(USER_LEFT_ROOM_STR.format(self.currentRoom, self.name))
        self.sendLine(USER_LEFT_ROOM_STR.format(self.currentRoom, self.formatUsername(self.name)))
        if self.name in self.getUsers():
            del self.getUsers()[self.name]
            if len(self.getUsers()) == 0:
                del self.rooms[self.currentRoom]
        self.currentRoom = None

    def sendMessage(self, message):
        message = "%s: %s" % (self.name, message)
        self.send_everyone(message)

    def send_everyone(self, message):
        if not self.currentRoom:
            self.sendLine(JOIN_ROOM_ERR_STR)
        else:
            for name, protocol in self.getUsers().iteritems():
                if protocol != self:
                    protocol.sendLine(message)

    def formatUsername(self, username):
        if username == self.name:
            return "%s (** This is you)" % username
        else:
            return "%s" % username

    def getUsers(self):
        return self.rooms[self.currentRoom]

    def nameIsFree(self, name):
        for room in self.rooms.values():
            if name in room:
                return False
        return True

class ChatFactory(Factory):

    def __init__(self):
        self.rooms = {DEFAULT_ROOM_STR : {}}

    def buildProtocol(self, addr):
        return Chat(self.rooms)

PORT = 8007
reactor.listenTCP(PORT, ChatFactory())
reactor.run()