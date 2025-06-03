import threading
from enum import Enum
from datetime import datetime
import numpy as np
import os
import time
import csv

class DataSaver(object):
    class WorkerRequest(Enum):
        NoRequest = 0
        Stop = 1

    def __init__(self, wm, dir):
        self.wm = wm
        self.dir = dir

        # worker will be grabbing wavemeter data
        # lock for worker request
        self.__worker_lock = threading.Lock()

        with self.__worker_lock:
            self.__worker_req = self.WorkerRequest.NoRequest
        self.__worker = threading.Thread(target = self.__worker_func, daemon=True)
        self.__worker.start()

    def stop_worker(self):
        if hasattr(self, '_DataSaver__worker'):
            with self.__worker_lock:
                self.__worker_req = self.WorkerRequest.Stop
            self.__worker.join()
        else:
            return
        
    def start_worker(self):
        if hasattr(self, '_DataSaver__worker'):
            if self.__worker.is_active():
                return
        with self.__worker_lock:
            self.__worker_req = self.WorkerRequest.NoRequest
        self.__worker = threading.Thread(target = self.__worker_func)
        self.__worker.start()

    def __check_worker_req(self):
        with self.__worker_lock:
            return self.__worker_req

    def __worker_func(self):
        # worker function
        while self.__check_worker_req() != self.WorkerRequest.Stop:
            freqs, amps, statuses, times = self.wm.get_all_data()
            err = self.wm.get_wavemeter_error()
            if len(times) == 0:
                time.sleep(0.1)
                continue
            final_time = times[-1]
            first_idx = 0
            for idx, this_time in enumerate(times):
                first_idx = idx
                if final_time - this_time < 0.1:
                    break
            freqs = freqs[first_idx:]
            amps = amps[first_idx:]
            times = times[first_idx:]
            use_freqs = []
            use_amps = []
            use_times = []
            for idx, freq in enumerate(freqs):
                if amps[idx] > 0.05:
                    known = False
                    ampdB =  round(10 * np.log(amps[idx]), 1)
                    for iidx, comp_freq in enumerate(use_freqs):
                        if np.abs(freq - comp_freq) < 0.01: # Within 10 MHz
                            use_freqs[iidx] = freq
                            use_amps[iidx] = ampdB
                            use_times[iidx] = times[idx]
                            known = True
                            break
                    if not known:
                        use_freqs.append(freq)
                        use_amps.append(ampdB)
                        use_times.append(times[idx])
            if len(use_times) == 0:
                time.sleep(0.1)
                continue
            idxs = np.argsort(use_freqs)
            write_freqs = [use_freqs[idx] for idx in idxs]
            write_amps = [use_amps[idx] for idx in idxs]
            now = datetime.now()
            path = self.dir + "\\" + now.strftime("%Y%m%d") + "_fast_wm.csv"
            if os.path.isfile(path) == False:
                outputHeader = ['Timestamp', 'Frequency', 'Saturation', 'wmError']
                with open(path, 'a', newline='') as f:
                    write = csv.writer(f)
                    write.writerow(outputHeader)
            else:
                dt = datetime.fromtimestamp(times[-1])
                formatted = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"
                outputBody = [formatted]
                for idx, freq in enumerate(write_freqs):
                    outputBody.append(freq)
                    outputBody.append(write_amps[idx])
                if err is None:
                    outputBody.append(0)
                else:
                    outputBody.append(err * 1e3)
                with open(path, 'a', newline='') as f:
                    write = csv.writer(f)
                    write.writerow(outputBody)
            time.sleep(0.1)
        print("Worker finishing")

    def __del__(self):
        print("Wavemeter is being deleted")
        self.stop_worker()