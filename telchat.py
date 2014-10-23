from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import functools
import sys

WELCOME_STR = "Welcome to the XYZ chat server"
WELCOME_USER_STR = "Welcome, {}!"
ASK_LOGIN_STR = "Login Name?"
NAME_TAKEN_STR = "Sorry, name taken."
NAME_RESERVED_STR = "Sorry, name reserved."
USER_JOINED_ROOM_STR = "* new user joined {0}: {1}"
USER_LEFT_ROOM_STR = "* user has left {0}: {1}"
SHOW_USER_STR = "* {0}\n"
SHOW_ROOMS_STR = "Active rooms are:\n"
SHOW_ROOM_STR = "* {0} ({1})\n"
END_OF_LIST_STR = "end of list"
JOIN_ROOM_STR = "Entering room: {0}"
DEFAULT_ROOM_STR = "DEFAULT"
QUIT_STR = "BYE"
JOIN_ROOM_ERR_STR = "You are not in a room.\nType /join <room> to join a room.\nType /rooms to see the available rooms"
NO_USER_NAMED_STR = "There is no user {0}."
WRONG_SYNTAX_SEND_PM_STR = 'Type "/pm username message" to write a private message.'
PRIVATE_MSG_STR = "*PM* {0}: {1}"
INVALID_NAME_STR = "Sorry, invalid name."
HELP_STR = "* Type the following comands:\n/users\tSee the users in the room\n/rooms\tSee the available rooms\n/join\tJoin a room\n/pm\tSend a private message to another user\n/help\tShow the help\n/leave\tLeave the current room\n/quit\tQuit"
USAGE_STR = "usage: python telchat.py <port>"

class Chat(LineReceiver):

    def __init__(self, rooms):
        self.rooms = rooms
        self.currentRoom = None
        self.name = None
        self.state = "GETNAME"
        self.actions = {"/users": self.handle_USERS,
                        "/quit": self.handle_QUIT,
                        "/leave": self.handle_LEAVE,
                        "/rooms": self.handle_ROOMS,
                        "/join": self.handle_JOIN,
                        "/pm": self.handle_PM,
                        "/help": self.handle_HELP}

    def connectionMade(self):
        self.log("A connection was made with.")
        self.sendLine("{0}\n{1}".format(WELCOME_STR, ASK_LOGIN_STR))

    def connectionLost(self, reason):
        self.log("A connection was closed.")
        if self.currentRoom:
            if self.name in self.getUsers():
                del self.getUsers()[self.name]

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
        name = name.strip()
        if not name:
            self.sendLine(INVALID_NAME_STR)
            return
        name = name.split(" ")[0]
        if not self.nameIsFree(name):
            self.sendLine(NAME_TAKEN_STR)
        elif name in self.actions.keys():
            self.sendLine(NAME_RESERVED_STR)
        else:
            self.name = name
            self.sendLine(WELCOME_USER_STR.format(self.name))
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
                usersStr += SHOW_USER_STR.format(self.formatUsername(name))
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
        self.sendEveryone(USER_LEFT_ROOM_STR.format(self.currentRoom, self.name))
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
            self.log("{0} room was created.".format(self.currentRoom))
        self.getUsers()[self.name] = self
        self.sendLine(JOIN_ROOM_STR.format(room))
        self.sendEveryone(USER_JOINED_ROOM_STR.format(self.currentRoom, self.name))
        self.log("{0} joined room {1}".format(self.name, self.currentRoom))

        self.handle_USERS()

    def handle_LEAVE(self, message = None):
        self.sendEveryone(USER_LEFT_ROOM_STR.format(self.currentRoom, self.name))
        self.sendLine(USER_LEFT_ROOM_STR.format(self.currentRoom, self.formatUsername(self.name)))
        self.log("{0} left room {1}".format(self.name, self.currentRoom))
        if self.name in self.getUsers():
            del self.getUsers()[self.name]
            if len(self.getUsers()) == 0:
                del self.rooms[self.currentRoom]
                self.log("{0} room was removed.".format(self.currentRoom))
        self.currentRoom = None

    def handle_PM(self, message):
        user = None

        splitted = message.split(" ")
        if len(splitted) == 1:
            self.sendLine(WRONG_SYNTAX_SEND_PM_STR)
            return
        else:
            user = splitted[0].strip()
            message = " ".join(splitted[1:])

        for room in self.rooms.values():
            for name, protocol in room.iteritems():
                if name == user:
                    protocol.sendLine(PRIVATE_MSG_STR.format(self.name, message))
                    return
        self.sendLine(NO_USER_NAMED_STR.format(user))

    def handle_HELP(self, message = None):
        self.sendLine(HELP_STR)

    def sendMessage(self, message):
        message = "{0}: {1}".format(self.name, message)
        self.sendEveryone(message)

    def sendEveryone(self, message):
        if not self.currentRoom:
            self.sendLine(JOIN_ROOM_ERR_STR)
        else:
            for name, protocol in self.getUsers().iteritems():
                if protocol != self:
                    protocol.sendLine(message)

    def formatUsername(self, username):
        if username == self.name:
            return "{0} (** This is you)".format(username)
        else:
            return "{0}".format(username)

    def getUsers(self):
        return self.rooms[self.currentRoom]

    def nameIsFree(self, name):
        for room in self.rooms.values():
            if name in room:
                return False
        return True

    def log(self, s):
        # Stub
        print s

class ChatFactory(Factory):

    def __init__(self):
        self.rooms = {DEFAULT_ROOM_STR : {}}

    def buildProtocol(self, addr):
        return Chat(self.rooms)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        try:
            port = int(sys.argv[1])
        except:
            print USAGE_STR
            exit(1)
        reactor.listenTCP(port, ChatFactory())
        reactor.run()
    else:
        print USAGE_STR