import lib.DummyDevice as DummyDevice
from lib.bristol_RS422 import BristolRS422
import threading
from enum import Enum
from datetime import datetime
import numpy as np
from time import time, perf_counter, sleep

class Wavemeter(object):
    class WorkerRequest(Enum):
        NoRequest = 0
        Stop = 1

    def __init__(self, port= '', targets=np.array([]), cache_n_measurements = 2000, calibration=None, calibration_cache_n=10, calibration_tol=50):
        self.device = BristolRS422(port)
        print("Initializing wavemeter device")
        # self.device = DummyDevice.DummyDevice(targets)
        self.targets = targets
        self.calib = calibration
        self.calib_cache_size = calibration_cache_n # coded on start. Currently not changeable, since I don't want to deal with resizing the ring buffer
        self.calib_err_cache = np.empty(calibration_cache_n, dtype=np.float64)
        self.calib_cache_loc = 0
        self.calib_cache_first_pass = True
        self.calib_tol = calibration_tol
        self.calib_lock = threading.Lock()

        self.data_lock = threading.Lock()
        self.cache_size = cache_n_measurements
        self.cache_loc = 0
        self.cache_first_pass = True
        self.cache_freqs = np.empty(self.cache_size, dtype=np.float64)
        # The same measurements before the calibration correction.  A lock loop
        # watching the calibration laser itself has to read these: that laser's
        # drift is what builds calib_err_cache, so the correction subtracts the
        # very motion the lock is trying to detect.
        self.cache_raw_freqs = np.empty(self.cache_size, dtype=np.float64)
        self.cache_amps = np.empty(self.cache_size, dtype=np.float64)
        self.cache_times = np.empty(self.cache_size, dtype=np.float64)
        self.cache_statuses = [None for _ in range(cache_n_measurements)]

        self.c = 299792458

        # worker will be grabbing wavemeter data
        # lock for worker request
        self.__worker_lock = threading.Lock()

        with self.__worker_lock:
            self.__worker_req = self.WorkerRequest.NoRequest
        self.__worker = threading.Thread(target = self.__worker_func, daemon=True)
        self.__worker.start()

    def stop_worker(self):
        if hasattr(self, '_Wavemeter__worker'):
            with self.__worker_lock:
                self.__worker_req = self.WorkerRequest.Stop
            self.__worker.join()
        else:
            return
        
    def start_worker(self):
        if hasattr(self, '_Wavemeter__worker'):
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
            wavelength, saturation, status, wmTime = self.device.get_measurement()
            this_time = perf_counter()
            if wavelength > 200:
                now = time()
                raw_freq = self.c / wavelength
                freq = raw_freq
                if self.calib: 
                    if np.abs(raw_freq - self.calib) < self.calib_tol:
                        self.calib_err_cache[self.calib_cache_loc] = raw_freq - self.calib
                        new_loc = self.calib_cache_loc + 1
                        if self.calib_cache_first_pass:
                            avg_err = np.mean(self.calib_err_cache[:new_loc])
                        else:
                            avg_err = np.mean(self.calib_err_cache)
                        if new_loc >= self.calib_cache_size:
                            if self.calib_cache_first_pass:
                                self.calib_cache_first_pass = False
                            self.calib_cache_loc = 0
                        else:
                            self.calib_cache_loc = new_loc
                    else:
                        if self.calib_cache_first_pass and self.calib_cache_loc == 0:
                            # No data has arrived yet
                            avg_err = 0
                        elif self.calib_cache_first_pass:
                            avg_err = np.mean(self.calib_err_cache[:self.calib_cache_loc])
                        else:
                            avg_err = np.mean(self.calib_err_cache)
                    prop = raw_freq / self.calib
                    freq = raw_freq - avg_err * prop
                with self.data_lock:
                    cache_location = self.cache_loc
                    # print(cache_location)
                    self.cache_freqs[cache_location] = freq
                    self.cache_raw_freqs[cache_location] = raw_freq
                    self.cache_amps[cache_location] = saturation
                    self.cache_times[cache_location] = now
                    self.cache_statuses[cache_location] = status
                    if cache_location + 1 >= self.cache_size:
                        # print("Entering reset")
                        if self.cache_first_pass:
                            self.cache_first_pass = False
                        self.cache_loc = 0
                    else:
                        self.cache_loc = cache_location + 1
            cur_time = perf_counter()
            while cur_time - this_time < 0.001:
                cur_time = perf_counter()
        print("Worker finishing")

    def set_calibration(self, calibration, tolerance=None):
        with self.calib_lock:
            self.calib = calibration
            self.calib_cache_loc = 0
            self.calib_cache_first_pass = True
            if tolerance is not None:
                self.calib_tol = tolerance
    
    def get_freqs(self):
        with self.data_lock:
            cache_location = self.cache_loc
            if self.cache_first_pass:
                freqs = self.cache_freqs[:cache_location].copy()
                times = self.cache_times[:cache_location].copy()
            else:
                freqs = self.cache_freqs.copy()
                times = self.cache_times.copy()
        idxs = np.argsort(times)
        return freqs[idxs], times[idxs]
    
    def get_amps(self):
        with self.data_lock:
            cache_location = self.cache_loc
            if self.cache_first_pass:
                amps = self.cache_amps[:cache_location].copy()
                times = self.cache_times[:cache_location].copy()
            else:
                amps = self.cache_amps.copy()
                times = self.cache_times.copy()
        idxs = np.argsort(times)
        if idxs is not None:
            return amps[idxs], times[idxs]
        else:
            return [], []
    
    def get_statuses(self):
        with self.data_lock:
            cache_location = self.cache_loc
            if self.cache_first_pass:
                statuses = self.cache_statuses[:cache_location].copy()
                times = self.cache_times[:cache_location].copy()
            else:
                statuses = self.cache_statuses.copy()
                times = self.cache_times.copy()
        idxs = np.argsort(times)
        res_statuses = [statuses[i] for i in idxs]
        if idxs is not None:
            return res_statuses, times[idxs]
        else:
            return [], []
    
    def get_all_data(self):
        with self.data_lock:
            cache_location = self.cache_loc
            if self.cache_first_pass:
                freqs = self.cache_freqs[:cache_location].copy()
                amps = self.cache_amps[:cache_location].copy()
                statuses = self.cache_statuses[:cache_location].copy()
                times = self.cache_times[:cache_location].copy()
            else:
                freqs = self.cache_freqs.copy()
                amps = self.cache_amps.copy()
                statuses = self.cache_statuses.copy()
                times = self.cache_times.copy()
        idxs = np.argsort(times)
        res_statuses = [statuses[i] for i in idxs]
        if idxs is not None:
            return freqs[idxs], amps[idxs], res_statuses, times[idxs]
        else:
            return [], [], [], []
    
    def get_all_cached(self):
        """get_all_data() plus the uncalibrated frequencies.

        Both frequency arrays come from a single locked read, so they are index
        aligned; calling get_all_data() twice would not be.
        """
        with self.data_lock:
            cache_location = self.cache_loc
            if self.cache_first_pass:
                freqs = self.cache_freqs[:cache_location].copy()
                raw_freqs = self.cache_raw_freqs[:cache_location].copy()
                amps = self.cache_amps[:cache_location].copy()
                statuses = self.cache_statuses[:cache_location].copy()
                times = self.cache_times[:cache_location].copy()
            else:
                freqs = self.cache_freqs.copy()
                raw_freqs = self.cache_raw_freqs.copy()
                amps = self.cache_amps.copy()
                statuses = self.cache_statuses.copy()
                times = self.cache_times.copy()
        idxs = np.argsort(times)
        res_statuses = [statuses[i] for i in idxs]
        return freqs[idxs], raw_freqs[idxs], amps[idxs], res_statuses, times[idxs]

    def get_wavemeter_error(self):
        if self.calib:
            with self.calib_lock:
                if self.calib_cache_first_pass and self.calib_cache_loc == 0:
                    # No data has arrived yet
                    avg_err = None
                elif self.calib_cache_first_pass:
                    avg_err = np.mean(self.calib_err_cache[:self.calib_cache_loc])
                else:
                    avg_err = np.mean(self.calib_err_cache)
                return avg_err
        return None


    def __del__(self):
        print("Wavemeter is being deleted")
        self.stop_worker()
