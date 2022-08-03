# Bristol 871 sample code
#
# This file contains a simple Python module to encapsulate connecting to the
# Bristol Wavemeter over the RS-422 interface and reading data from it.
import serial
import Threading

class LEONIRS322(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event
        self.portnumber = "COM4"  # the usb port to which the wavemeter is connected

        self.ser = serial.Serial(
            port=portnumber,
            baudrate=57600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS)

        self.switchChannels = 1


        send = f'ch{self.switchChannel}\r\n'
            self.switchChannels = self.switchChannels % 10 + 1
            ser.open()
            ser.write(b'send')
            print(ser.read_until())
            ser.close()


# class LEONIRS322(object):
#     def __init__(self):
#         self.portnumber = "COM4"  # the usb port to which the wavemeter is connected
#
#         self.ser = serial.Serial(
#             port=portnumber,
#             baudrate=57600,
#             parity=serial.PARITY_NONE,
#             stopbits=serial.STOPBITS_ONE,
#             bytesize=serial.EIGHTBITS)
#
#
#         self.fiberSwitchTimer = QTimer()
#         self.fiberSwitchTimer.setInterval(1000)
#         self.fiberSwitchTimer.timeout.connect(print('hi'))
#         self.fiberSwitchTimer.start()
#
#         self.switchChannels=1
#
#
#     def updateSwitch(self):
#         print('hi')
#         send=f'ch{self.switchChannel}\r\n'
#         self.switchChannels=self.switchChannels%10+1
#         ser.open()
#         ser.write(b'send')
#         print(ser.read_until())
#         ser.close()
#
