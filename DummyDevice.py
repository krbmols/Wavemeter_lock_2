import random
import time

class DummyDevice:
    class DummySerialPort:
        def __init__(self):
            self.port = 'test'
        def close(self):
            pass
    def __init__(self, targets):
        self.targets = targets
        self.serial_port = DummyDevice.DummySerialPort()
        self.c = 299792458
    
    def get_measurement(self):
        # Simulate a measurement. Don't read from the last two targets
        time.sleep(0.1)
        these_targets = self.targets[:-2]
        these_targets = self.c / these_targets
        this_target = random.choice(these_targets) + random.uniform(-0.00001, 0.00001)
        return this_target, random.uniform(0.1, 0.5), 4, 0
