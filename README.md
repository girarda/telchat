# __telchat__
__telchat__ is a chat server implemented using Python and Twisted.

## Installation steps (Ubuntu)
1. Install Python 2.7 or 2.6.8 (Only Python 2.7.5+ and 2.6.8 were tested) `apt-get install python` (Python 2.7 should already be installed)
2. Install the Twisted framework `sudo apt-get purge python-twisted`
3. Run the script `python telchat.py <port>`

### How to use
* Connect: `telnet <IP ADDRESS> 8888`
* Show available rooms: `/rooms`
* Show users in current room: `/users`
* Send a private message: `/pm <username> <message>`
* Join a room: `/join <room name> (A new room will be created if it does not exist)
* Leave a room: `/leave` (The room will be removed if the last user leaves it)
* Quit: `/quit`
