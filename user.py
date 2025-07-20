from double_ratchet import DoubleRatchet
import select
import signal
import time
import sys


class User:
    def __init__(self, __name: str, __msgs: list, __pipe_send: str, __pipe_receive, msg_to_new_dh):
        self.__name = __name

        self.__pipez = Pipez(__pipe_send, __pipe_receive)

        self.__d_ratchet = DoubleRatchet(__name, self.__pipez, msg_to_new_dh)
        self.__msgs = __msgs
        self.__running = True

    def __send_msg(self, msg):
        print("Sending b'" + msg + "'")
        self.__d_ratchet.send_msg(msg)

    def __receive_msg(self):
        ans = self.__d_ratchet.receive_msg()
        if ans is None or len(ans) == 0:
            return False
        print("Received", ans)
        return True

    def start(self):
        print(self.__name, 'starting loop')
        if self.__name == 'Alice':
            if len(self.__msgs) != 0:
                self.__send_msg(self.__msgs.pop(0))

        time.sleep(1)
        while self.__running:
            r = self.__receive_msg()
            if r and len(self.__msgs) != 0:
                self.__send_msg(self.__msgs.pop(0))
            time.sleep(1)

    def shutdown(self):
        self.__running = False
        self.__pipez.close()


class Pipez:
    def __init__(self, __pipe_send: str, __pipe_receive):
        self.__pipe_send = open(__pipe_send, 'wb')
        self.__pipe_receive = open(__pipe_receive, 'rb')

    def send(self, data: bytes):
        if len(data) == 0:
            return
        if data[-1] != b'\n':
            data += b'\n'
        self.__pipe_send.write(data)
        self.__pipe_send.flush()

    def receive(self, block=False):
        if block:
            return self.__pipe_receive.readline()
        readable, _, _ = select.select([self.__pipe_receive], [], [], 0)
        if self.__pipe_receive in readable:
            return self.__pipe_receive.readline()
        return b''

    def close(self):
        self.__pipe_send.close()
        self.__pipe_receive.close()


alice_msgs = [
    "Hi Bob, how are you?",
    "That's good to hear!",
    "What did you do today?",
    "Sounds interesting.",
    "I worked on our project a bit.",
    "Did you see the latest update?",
    "I think we’re making progress.",
    "We should test it tomorrow.",
    "Can you handle the setup?",
    "Perfect. I'll prepare the data.",
    "Let’s aim for 10 AM?",
    "Alright, works for me.",
    "Have you checked the logs?",
    "I noticed some warnings.",
    "Maybe we need more error checks.",
    "Should we add logging?",
    "I’ll write a wrapper.",
    "Let’s review it later.",
    "Thanks for the help!",
    "Talk to you soon."
]

bob_msgs = [
    "Hey Alice! I'm doing well, thanks.",
    "How about you?",
    "Just finished some coding.",
    "Fixed a couple of bugs.",
    "Oh nice! Which part?",
    "Yes, I checked the repo.",
    "Agreed, it's looking good.",
    "Sure, tomorrow is fine.",
    "Yes, I’ll take care of it.",
    "Got it. Thanks!",
    "10 AM is perfect.",
    "I’ll be there on time.",
    "Yes, I reviewed them.",
    "I saw those too.",
    "Good point.",
    "Yes, logging would help.",
    "Great, that’ll make it cleaner.",
    "Sounds good.",
    "Always happy to help.",
    "Bye!"
]

if __name__ == '__main__':
    arg = sys.argv[1]

    if arg == 'a':
        name = 'Alice'
        msgs = alice_msgs
        pipe_send = 'pipe_a_to_server'
        pipe_receive = 'pipe_server_to_a'
        msg_to_new_dh = 5
    elif arg == 'b':
        name = 'Bob'
        msgs = bob_msgs
        pipe_send = 'pipe_b_to_server'
        pipe_receive = 'pipe_server_to_b'
        msg_to_new_dh = 3
    else:
        print('Missing Argument')
        exit(0)
    user = User(name, msgs, pipe_send, pipe_receive, msg_to_new_dh)


    def signal_handler(s, f):
        user.shutdown()
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)
    user.start()
