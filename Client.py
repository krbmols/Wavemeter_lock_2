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
                    bTimeout = True
                    return None
                rep = []
                bTimeout = False
                for i in recv_type:
                    if self.__sock.poll(timeout) == 0:
                        rep.append(None)
                        bTimeout = True
                    else:
                        if i == 0:
                            rep.append(self.__sock.recv(flag))
                        else:
                            rep.append(self.__sock.recv_string(flag))
                return rep, bTimeout
            return f
        return deco
    
    def send_get_frequencies(self):
        @Client.poll_recv([0, 0, 0], timeout=10000)
        def _send_get_frequencies(self):
            self.__sock.send_string('get_frequencies')
        rep, bTimeout = _send_get_frequencies(self)
        if not bTimeout:
            nfreqs = int.from_bytes(rep[0], 'little')
            # print(rep[0])
            # print(rep[1])
            if nfreqs == 0:
                return np.array([]), []
            else:
                freqs = np.frombuffer(rep[1], dtype=np.float64, count=nfreqs)
                time_data = rep[2]
                times = time_data.split(b'\x00')[:-1]
                times = [t.decode('utf-8') for t in times]
                return freqs, times
        else:
            return np.array([]), []
    
    def send_get_saturations(self):
        @Client.poll_recv([0, 0, 0], timeout=10000)
        def _send_get_saturations(self):
            self.__sock.send_string('get_saturations')
        rep, bTimeout = _send_get_saturations(self)
        if not bTimeout:
            nfreqs = int.from_bytes(rep[0], 'little')
            # print(rep[0])
            # print(rep[1])
            if nfreqs == 0:
                return np.array([]), []
            else:
                freqs = np.frombuffer(rep[1], dtype=np.float64, count=nfreqs)
                time_data = rep[2]
                times = time_data.split(b'\x00')[:-1]
                times = [t.decode('utf-8') for t in times]
                return freqs, times
        else:
            return np.array([]), []
        
    def send_get_data(self):
        @Client.poll_recv([0, 0, 0, 0], timeout=10000)
        def _send_get_data(self):
            self.__sock.send_string('get_data')
        rep, bTimeout = _send_get_data(self)
        if not bTimeout:
            nfreqs = int.from_bytes(rep[0], 'little')
            # print(rep[0])
            # print(rep[1])
            if nfreqs == 0:
                return np.array([]), np.array([]), []
            else:
                freqs = np.frombuffer(rep[1], dtype=np.float64, count=nfreqs)
                saturations = np.frombuffer(rep[2], dtype=np.float64, count=nfreqs)
                time_data = rep[3]
                times = time_data.split(b'\x00')[:-1]
                times = [t.decode('utf-8') for t in times]
                return freqs, saturations, times
        else:
            return np.array([]), np.array([]), []