import zmq

import numpy as np

class Client(object):
    def recreate_sock(self):
        if self.__sock is not None:
            self.__sock.close()
        self.__sock = self.__ctx.socket(zmq.REQ)
        self.__sock.connect(self.__url)
    
    def __init__(self, url: str):
        self.__url = url
        self.__ctx = zmq.Context()
        self.__sock = None
        self.recreate_sock()
        self.timeout = 500

    def poll_recv(recv_type = [1], timeout=1000, flag=0):
        def deco(func):
            def f(self, *args): #timeout in milliseconds
                try:
                    func(self, *args)
                except Exception as e:
                    print('Error in client function: ' + str(e))
                    return None
                rep = []
                for i in recv_type:
                    if self.__sock.poll(timeout) == 0:
                        rep.append(None)
                    else:
                        if i == 0:
                            rep.append(self.__sock.recv(flag))
                        else:
                            rep.append(self.__sock.recv_string(flag))
                return rep
            return f
        return deco
    
    def send_get_frequencies(self):
        @Client.poll_recv([0, 0])
        def _send_get_frequencies(self):
            self.__sock.send_string('get_frequencies')
        rep = _send_get_frequencies(self)
        nfreqs = int.from_bytes(rep[0], 'little')
        # print(rep[0])
        # print(rep[1])
        if nfreqs == 0:
            return np.array([])
        else:
            freqs = np.frombuffer(rep[1], dtype=np.float64, count=nfreqs)
            return freqs
