import select
import sys
import signal

def read_pipe(pipe):
    readable, _, _ = select.select([pipe], [], [], 0)
    if pipe in readable:
        return pipe.readline()
    return b''

def write_pipe(pipe, line):
    pipe.write(line)
    pipe.flush()

class Server:
    def __init__(self):
        self.a_to_p = None
        self.b_to_p = None
        self.p_to_a = None
        self.p_to_b = None

        self.running = True

        self.populate_pipes()

    def populate_pipes(self):
        print('Populating Pipes')
        self.a_to_p = open('pipe_a_to_server', 'rb')
        self.p_to_a = open('pipe_server_to_a', 'wb')

        self.b_to_p = open('pipe_b_to_server', 'rb')
        self.p_to_b = open('pipe_server_to_b', 'wb')

    def start(self):
        print('Starting MITM')
        while self.running:
            line = read_pipe(self.a_to_p)
            if len(line) != 0:
                print('Alice\t', line)
                write_pipe(self.p_to_b, line)

            line = read_pipe(self.b_to_p)
            if len(line) != 0:
                print('Bob\t', line)
                write_pipe(self.p_to_a, line)


    def shutdown(self):
        self.running = False


if __name__ == '__main__':
    server = Server()


    def signal_handler(s, f):
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)
    server.start()

