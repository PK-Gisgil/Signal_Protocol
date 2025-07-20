from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from pyDH import DiffieHellman
import base64
import os


def kdf(t1: bytes, p1: bytes = None):
    h = hashes.XOFHash(hashes.SHAKE128(digest_size=64))
    h.update(t1)
    if p1 is not None:
        h.update(p1)
    t2 = h.squeeze(32)
    p2 = h.squeeze(32)
    del h
    return t2, p2


def encrypt(mk, plaintext, associated_data):
    # print(mk)
    aesgcm = AESGCM(mk)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), associated_data)
    return nonce, ct


def decrypt(mk, nonce, ciphertext, associated_data):
    # print(mk)
    aesgcm = AESGCM(mk)
    pt = aesgcm.decrypt(nonce, ciphertext, associated_data)
    return pt


MAX_SKIP = 3
REQUEST = b'REQUEST_PUBLIC_KEY'


class DoubleRatchet:
    def __init__(self, name: str, pipez, __msg_to_new_dh):
        self.__name = 'Protocol'
        self.__pipez = pipez

        # used to send
        self.__dh_s = DiffieHellman()
        # used to receive
        self.__dh_r = None
        self.__dh_secret = None

        self.__msg_to_new_dh = __msg_to_new_dh

        self.__rk = b'root_key'

        # used to send
        self.__ck_s = None
        # used to receive
        self.__ck_r = None

        # used to send
        self.__no_s = 0
        # used to receive
        self.__no_r = 0

        # number of msgs in previous sending chain
        self.__pn = 0

        # dict to store keys for messages which have not yet arrived
        self.__msg_skipped = {}

    # START - DH MANAGEMENT
    # sending chain key
    def __update_own_dh(self):
        #print('New DH Pair')
        self.__pn = self.__no_s
        self.__no_s = 0
        self.__no_r = 0

        self.__dh_s = DiffieHellman()
        secret = self.__dh_s.gen_shared_key(self.__dh_r)
        chain_key = self.__update_root_key(secret)
        self.__update_chain_key(chain_key, True)
        #print('Secret', secret)

    # receiving chain key
    def __update_remote_dh(self, dh_r, first_remote=False):
        if type(dh_r) == bytes:
            dh_r = dh_r.decode()
            dh_r = int(dh_r)
        if self.__dh_r == dh_r:
            return

        #print('New Remote DH')

        self.__pn = self.__no_r
        self.__no_s = 0
        self.__no_r = 0

        self.__dh_r = dh_r
        secret = self.__dh_s.gen_shared_key(self.__dh_r)
        chain_key = self.__update_root_key(secret)
        #print('Secret', secret)
        if first_remote:
            self.__update_chain_key(chain_key, sending=True)
        else:
            self.__update_chain_key(chain_key, False)

    # END - DH MANAGEMENT

    # START - ROOT KEY MANAGEMENT
    def __update_root_key(self, dh_out):
        self.__rk, chain_key = kdf(self.__rk, dh_out.encode())
        return chain_key

    # END - ROOT KEY MANAGEMENT

    # START - CHAIN KEY MANAGEMENT
    def __update_chain_key(self, chain_key, sending):
        if sending:
            self.__ck_s = chain_key
        else:
            self.__ck_r = chain_key

    def __get_send_chain_key(self):
        #print("CK S", base64.b64encode(self.__ck_s))
        self.__ck_s, mk = kdf(self.__ck_s)
        return mk

    def __get_receive_chain_key(self):
        #print("CK R", base64.b64encode(self.__ck_r))
        self.__ck_r, mk = kdf(self.__ck_r)
        return mk

    # END - CHAIN KEY MANAGEMENT

    def __header(self):
        header = (b'' + str(self.__dh_s.gen_public_key()).encode() +
                  b';' + str(self.__pn).encode() +
                  b';' + str(self.__no_s).encode())
        return header

    def __concat(self, ad, header):
        pass

    def send_msg(self, msg):
        # check if we have a dh session running
        if self.__dh_r is None:
            # start Session
            self.__pipez.send(REQUEST)
            self.__receive_public_key()

        if self.__no_s >= self.__msg_to_new_dh or self.__ck_s == None:
            self.__update_own_dh()

        # get sending msg key
        mk = self.__get_send_chain_key()
        headers = self.__header()
        self.__no_s += 1

        # encrypt msg
        nonce, ciphertext = encrypt(mk, msg, headers)
        nonce = base64.b64encode(nonce)
        ciphertext = base64.b64encode(ciphertext)
        res = headers + b";" + nonce + b';' + ciphertext
        self.__pipez.send(res)

    def __receive_public_key(self):
        r = self.__pipez.receive(block=True)
        print(self.__name, 'received public key')
        self.__update_remote_dh(r, True)

    def receive_msg(self):
        ans = self.__pipez.receive()
        if len(ans) == 0:
            return

        if ans.strip() == REQUEST:
            print('Communication Partner requested DH Public Key')
            self.__pipez.send(str(self.__dh_s.gen_public_key()).encode())
            return

        # assume normal signal protocol
        ans = ans.split(b';')
        header = b';'.join(ans[0:3])
        public_key, prev_chain, msg_no = int(ans[0].decode()), int(ans[1].decode()), int(ans[2].decode())

        self.__update_remote_dh(public_key)

        nonce, cipher = ans[3], ans[4]
        cipher = cipher[:-1]  # remove trailling newline
        nonce = base64.b64decode(nonce)
        cipher = base64.b64decode(cipher)

        if prev_chain != self.__pn:
            print('ERROR - Previous Chain Value wrong', self.__pn, prev_chain)
            return
        if msg_no != self.__no_r:
            print('Skipped Messages between', self.__no_r, 'and', msg_no)

        self.__update_remote_dh(public_key)

        mk = self.__get_receive_chain_key()
        plaintext = decrypt(mk, nonce, cipher, header)
        self.__no_r += 1
        return plaintext
