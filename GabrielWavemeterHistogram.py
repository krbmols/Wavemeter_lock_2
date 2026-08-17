# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 09:57:54 2021

@author: Gabriel Patenotte, inspired by Lingbang and Bryant
"""
import sys
import win32com.client as wincl
import winsound
import threading
import requests
import os
import csv
import numpy as np
from PyQt5.QtWidgets import QApplication, QDoubleSpinBox, QMainWindow, QGridLayout, QListWidget, QWidget, QCheckBox, QLabel, \
    QVBoxLayout, QHBoxLayout, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt, QSize
import pyqtgraph as pg
from bristol_RS422 import BristolRS422
from PyQt5.QtGui import QFont
from datetime import datetime
from time import time

global url
url = 'https://hooks.slack.com/services/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'
global portnumber
portnumber = "COM10"  # the usb port to which the wavemeter is connected
global device
device = BristolRS422(portnumber)  # the BristolRS422 python file collects measurements from the Bristol 871a wavemeter
pg.setConfigOptions(antialias=True)  # antialiasing makes the graphs easier to view
global speak
speak = wincl.Dispatch("SAPI.SpVoice")


class Channel(QWidget):  # a class for the widgets belonging to a particular channel

    def __init__(self, target, parent=None):
        super(Channel, self).__init__(parent)
        self.target = target
        self.firstUpdate = True  # if true, the object has just been created.
        self.currentStatus = 0  # Status of the wavemeter. See self.dictionary to see what each status corresponds to.
        self.data = []  # initial values for the channel's stored data. In order of frequency, saturation, status, and time.
        self.t = []  # list of the plot datapoint's x-coordinates
        self.f = []  # list of the plot datapoint's y-coordinates
        self.tLT = []  # list of the plot datapoint's x-coordinates
        self.fLT = []  # list of the plot datapoint's y-coordinates
        self.tDay = []
        self.fDay = []
        self.isLocked = False
        self.speed_of_light = 299792458.
        self.plotPoints =  100  # the max number of points that will be shown on a graph.

        self.dictionary = {0: 'inactive channel', 4: 'reference laser locked', 8: 'etalon fringe error',
                           16: 'etalon saturation error', 2048: 'reference laser not stable', 8192: 'temperature high',
                           16384: 'temperature low', 32768: 'pressure high', 65536: 'pressure low',
                           131072: 'wavelength outside instrument specification', 524288: 'etalon fringe error',
                           1048576: 'etalon saturation error', 2097152: 'calibration in progress',
                           4194304: 'etalon fringe error', 8388608: 'etalon sat', 536870912: 'low detector signal',
                           536870916: 'low detector signal?', 1073741824: 'fringe frequency error'}
        # The dictionary converts between the binary wavemeter signal and what the binary message signifies.

        # In the following lines we generate several labels and a plot.
        self.label1 = QLabel()
        self.label1.setFont(QFont("Arial", 40))
        self.label1.setAlignment(Qt.AlignVCenter)

        self.label2 = QLabel()
        self.label2.setFont(QFont("Arial", 70))
        self.label2.setAlignment(Qt.AlignTop)

        self.labelPP = QLabel()
        self.labelPP.setFont(QFont("Arial", 30))
        self.labelPP.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.labelLambda = QLabel()
        self.labelLambda.setFont(QFont("Arial", 15))
        self.labelLambda.setAlignment(Qt.AlignBottom)

        self.labelSat = QLabel()
        self.labelSat.setFont(QFont("Arial", 40))
        self.labelSat.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.labelStatus = QLabel()
        self.labelStatus.setFont(QFont("Arial", 15))
        self.labelStatus.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.lockedCheckbox = QCheckBox("Locked")
        self.lockedCheckbox.setChecked(False)
        self.lockedCheckbox.stateChanged.connect(self.changeLock)

        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.line = self.graph.plot(self.t, self.f, pen=None,
                                    symbolPen='w')  # graph denotes the axes, and line denotes the datapoints. When we update the plot, we only need to redraw the line.
        self.targetMarker = pg.InfiniteLine(pos=self.target, angle=0, pen=pg.mkPen('r', width=2))
        self.graph.addItem(self.targetMarker)

        self.graphLT = pg.PlotWidget()
        self.graphLT.setBackground('w')
        self.lineLT = self.graphLT.plot(self.tLT, self.fLT, pen=None, symbolPen='w')
        self.targetMarkerLT = pg.InfiniteLine(pos=self.target, angle=0, pen=pg.mkPen('r', width=2))
        self.graphLT.addItem(self.targetMarkerLT)

        self.graphDay = pg.PlotWidget()
        self.graphDay.setBackground('w')
        self.lineDay = self.graphDay.plot(self.tDay, self.fDay, pen=None, symbolPen='w')
        self.targetMarkerDay = pg.InfiniteLine(pos=self.target, angle=0, pen=pg.mkPen('r', width=2))
        self.graphDay.addItem(self.targetMarkerDay)

        self.counter = 1
        # We initialize a QTimer. The setInterval argument specifies how often the argument in connect() occurs.
        self.channelTimer = QTimer()
        self.channelTimer.setInterval(100)
        self.channelTimer.timeout.connect(self.updateChannel)
        self.channelTimer.start()

        # We layout the position of the channel's widgets. In addWidget, the four numbers denote y and x position, and height and width of the widget.
        self.channelLayout = QGridLayout()
        self.setLayout(self.channelLayout)
        self.channelLayout.addWidget(self.label1, 1, 0, 1, 2)
        self.channelLayout.addWidget(self.label2, 0, 2, 2, 1)
        self.channelLayout.addWidget(self.labelPP, 2, 2, 1, 1)
        self.channelLayout.addWidget(self.labelLambda, 0, 0, 1, 1)
        self.channelLayout.addWidget(self.labelSat, 2, 0, 2, 2)
        self.channelLayout.addWidget(self.lockedCheckbox, 0, 1, 1, 1)
        self.channelLayout.addWidget(self.labelStatus, 3, 2, 1, 2)

        self.channelLayout.setSpacing(0)
        self.channelLayout.setContentsMargins(0, 0, 0, 0)
        # self.setStyleSheet("background-color:white;")

    def stillLocked(self):
        if abs(np.mean(self.f) - self.target) >= 0.01 and self.isLocked == True:
            s = f"{round(self.speed_of_light / self.target, 1)} nanometers."
            # s=s.replace("", " ")[1: -1]
            winsound.Beep(2000, 1000)
            speak.Speak(s)
            winsound.Beep(2000, 1000)
            speak.Speak(s)

            message1 = f"{round(self.speed_of_light / self.target, 1)} nm / {round(self.target, 3)} GHz: unlocked."

            self.lockedCheckbox.setChecked(False)
            data = {'text': message1}

            requests.post(url, json=data, verify=False)
        else:
            pass

    def updateLabel(self, name1, name2, name3, name4,
                    name5):  # updates the value in the labels. Called upon by updateChannel
        self.label1.setText("%s" % name1)
        self.label2.setText("%s" % name2)
        self.labelPP.setText("%s" % name3)
        self.labelLambda.setText("%s" % name4)
        self.labelSat.setText("%s" % name5)
        # summary of if statement: if the channel is assigned a new status, try matching the status to the dictionary. If the dictionary doesn't know what the status is, print a statement showing the unknown status.
        if self.data[2] != self.currentStatus:
            self.currentStatus = self.data[2]
            try:
                name6 = self.dictionary[self.currentStatus]
            except:
                name6 = "Unknown status"
                print(f'Unknown status {self.currentStatus} for frequency {self.data[0]}')
            self.labelStatus.setText(f"{name6}")

    def changeLock(self, checked):
        if checked:
            self.isLocked = True
            message1 = f"{round(self.speed_of_light / self.target, 1)} nm / {round(self.target, 3)} GHz: locked."
            data = {'text': message1}

            requests.post(url, json=data, verify=False)
        else:
            self.isLocked = False

    def updateGraph(self):  # redraws the plot's 'line', aka datapoints. Called upon by updateChannel

        if len(self.t) == 1:
            self.channelLayout.addWidget(self.graph, 0, 4, 4, 1)


        ay = self.graph.getAxis('left')  # creates an object ay corresponding to the left axis.
        dy = [(value, '{:.3f}'.format(value)) for value in np.linspace(round(min(self.f), 3), round(max(self.f), 3),
                                                                       8)]  # creates the values to go on the left y-axis.
        ay.setTicks([dy,
                     []])  # pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
        self.graph.setYRange(min(self.f) - 0.002,
                             max(self.f) + 0.002)  # we set the graph range to automatically fit the channel's data. The extra 1 MHz (0.001) space makes the data easier to view.
        self.line.setData(self.t, self.f)  # updates the datapoints shown on the graph.
        self.targetMarker.setValue(self.target)

    def updateGraphLT(self):  # redraws the plot's 'line', aka datapoints. Called upon by updateChannel

        if len(self.tLT) == 1:
            self.channelLayout.addWidget(self.graphLT, 0, 5, 4, 1)

        ayLT = self.graphLT.getAxis('left')  # creates an object ay corresponding to the left axis.
        dyLT = [(value, '{:.3f}'.format(value)) for value in
                np.linspace(round(min(self.fLT), 3), round(max(self.fLT), 3),
                            8)]  # creates the values to go on the left y-axis.
        ayLT.setTicks([dyLT,
                       []])  # pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
        self.graphLT.setYRange(min(self.fLT) - 0.002,
                               max(self.fLT) + 0.002)  # we set the graph range to automatically fit the channel's data. The extra 1 MHz (0.001) space makes the data easier to view.
        self.lineLT.setData(self.tLT, self.fLT)  # updates the datapoints shown on the graph.
        self.targetMarkerLT.setValue(self.target)

    def updateGraphDay(self):  # redraws the plot's 'line', aka datapoints. Called upon by updateChannel

        if len(self.tDay) == 1:
            self.channelLayout.addWidget(self.graphDay, 0, 6    , 4, 1)

        ayDay = self.graphDay.getAxis('left')  # creates an object ay corresponding to the left axis.
        dyDay = [(value, '{:.3f}'.format(value)) for value in
                 np.linspace(round(min(self.fDay), 3), round(max(self.fDay), 3),
                             8)]  # creates the values to go on the left y-axis.
        ayDay.setTicks([dyDay,
                        []])  # pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
        self.graphDay.setYRange(min(self.fDay) - 0.002,
                                max(self.fDay) + 0.002)  # we set the graph range to automatically fit the channel's data. The extra 1 MHz (0.001) space makes the data easier to view.
        self.lineDay.setData(self.tDay, self.fDay)  # updates the datapoints shown on the graph.
        self.targetMarkerDay.setValue(self.target)

    def updateChannel(self):

        if len(self.data) == 0:
            pass
        else:

            self.counter += 1
            if len(self.t) >= self.plotPoints:  # keeps the number of data points at or below plotPoints.
                self.t = self.t[1:]
                self.f = self.f[1:]

            if len(self.data) != 0:
                self.t.append(self.data[-1])  # makes a new data point, x-coordinate being time.
                self.f.append(self.data[0])  # makes a new data point, y-coordinate being frequency
                threadGraph = threading.Thread(target=self.updateGraph)
                threadGraph.start()
            if self.counter % 90 == 1:
                # self.stdLT = np.std(self.fLT[-20:])
                if len(self.tLT) >= self.plotPoints:  # keeps the number of data points at or below plotPoints.
                    self.tLT = self.tLT[1:]
                    self.fLT = self.fLT[1:]
                if len(self.data) != 0:
                    self.tLT.append(np.mean(self.t))  # makes a new data point, x-coordinate being time.
                    self.fLT.append(np.mean(self.f))  # makes a new data point, y-coordinate being frequency
                    threadGraphLT = threading.Thread(target=self.updateGraphLT)
                    threadGraphLT.start()
                thread = threading.Thread(target=self.stillLocked)
                thread.start()
            if self.counter % 5760 == 1:
                if len(self.tDay) >= self.plotPoints:  # keeps the number of data points at or below plotPoints.
                    self.tDay = self.tDay[1:]
                    self.fDay = self.fDay[1:]
                if len(self.data) != 0:
                    self.tDay.append(np.mean(self.t))  # makes a new data point, x-coordinate being time.
                    self.fDay.append(np.mean(self.f))  # makes a new data point, y-coordinate being frequency
                    threadGraphDay = threading.Thread(target=self.updateGraphDay)
                    threadGraphDay.start()
                self.counter = 1
            self.std = np.std(self.f[-20:])  # calculates peak-to-peak variation of data for the latest 100 data points
            self.mean = np.mean(self.f)

            # below, we generate the name for the two labels corresponding to the laser frequency. The first label gives the THz and GHz information, while the second label gives the MHz scale.
            num, decimal = [int(self.f[-1]), str(round(self.f[-1] - int(self.f[-1]), 3))[1:]]
            if self.std <= 1:
                name3 = '±' + '{:.1f}'.format(1000 * self.std) + " MHz"
            elif self.std <= 1E3:
                name3 = '±' + '{:.2f}'.format(self.std) + " GHz"
            else:
                name3 = '±' + '{:.2f}'.format(0.001 * self.std) + " THz"

            self.updateLabel(f"{num}", (f"{decimal}" + "000")[:4], name3,
                             '{:.1f}'.format(self.speed_of_light / self.f[-1]) + " nm",
                             '{:.1f}'.format(100 * self.data[1]) + "%")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Wavemeter GUI")
        self.showMaximized()
        self.plotPoints=1000
        # self.path='N:\wavemeterEightChannelLogs'
        self.path = 'C:\Bristol'
        # self.path='C:\Users\Krb-Logging\Desktop\Logs'
        # self.path='C:\Users\Krb-Logging\Desktop'
        os.chdir(self.path)
        self.t = []  # list of the plot datapoint's x-coordinates
        self.f = []  # list of the plot datapoint's y-coordinates
        self.Rb5s6p = 713281.7400
        self.NaD2 = 508848.92
        self.red = 472158.8
        self.iCalibration = 1
        self.wmError = [0]
        self.calibrator = False
        self.counter=1
        self.speed_of_light = 299792458
        # 713289 lingbang's UV, 295157

        self.wmErrorGraph = pg.PlotWidget(title='Wavemeter Error')
        self.wmErrorGraph.setBackground('w')

        self.line = self.wmErrorGraph.plot(self.t, self.f, pen=None,
                                    symbolPen='w')  # graph denotes the axes, and line denotes the datapoints. When we update the plot, we only need to redraw the line.

        self.targets = [508848.92, 508332.618, 295170, 472158.192, 713289, 328966.168,
                        352186.333, 282708.8]
        self.targets.sort()
        self.threshold = 100
        self.storedData = [[0, 0]] * len(self.targets)
        self.timeStart = time()
        self.rogueFreqs=[]
        # self.fileName = 'wm8Data32.csv'
        # 32 start 2021-12-02 6:03 pm, corrected, 7/8 lasers.
        # 30 start 2021-11-18 2:44 pm, corrected, outside chamber, 6/7 lasers, most unlocked except Nas
        # 29 start 2021-11-18 1:27 pm, uncorrected, outside chamber, 6/7 lasers, most unlocked except Nas
        self.mainTimer = QTimer()
        self.mainTimer.setInterval(1)
        self.mainTimer.timeout.connect(self.createData)
        self.mainTimer.start()

        self.widgetTimer = QTimer()
        self.widgetTimer.setInterval(100)
        self.widgetTimer.timeout.connect(self.writeData)
        self.widgetTimer.start()
        self.targetLayout = QHBoxLayout()
        self.targetWidgets = [0] * len(self.targets);
        for i in range(len(self.targets)):
            self.targetWidgets[i] = QDoubleSpinBox(self)
            self.targetWidgets[i].setFont(QFont("Arial", 15))
            self.targetWidgets[i].setDecimals(3)
            self.targetWidgets[i].setRange(200000, 900000)
            self.targetWidgets[i].setValue(self.targets[i])
            self.targetWidgets[i].setSingleStep(0.001)
            self.targetWidgets[i].valueChanged.connect(self.targetChange)
            self.targetLayout.addWidget(self.targetWidgets[i])
        self.endLayout=QHBoxLayout()
        self.endLayout.setSpacing(0)
        self.endLayout.setContentsMargins(0, 0, 0, 0)
        self.listWidget=QListWidget(self)
        self.listWidget.setMaximumSize(130,300)


        self.endLayout.addWidget(self.listWidget)

        self.mainLayout = QVBoxLayout()
        self.mainWidget = QWidget()
        self.mainLayout.addLayout(self.targetLayout)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        self.channels = [0] * len(self.targets)
        for i in range(len(self.targets)):
            self.channels[i] = Channel(self.targets[i])
            self.mainLayout.addWidget(self.channels[i])
        self.mainLayout.addLayout(self.endLayout)
        self.adjustSize()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

    def getValue(self, widget):
        return widget.value()

    def targetChange(self, i):

        for i in range(len(self.targetWidgets)):
            if self.targets[i] == self.targetWidgets[i].value():
                pass
            else:
                self.targets[i] = self.targetWidgets[i].value()
                self.targets.sort()
                self.channels[i].target = self.targets[i]

    def createData(self):
        self.wavelength, self.saturation, self.status, self.time_step = device.get_measurement()
        # print(self.wavelength)
        self.time_step = time()
        self.time_step = self.time_step - self.timeStart
        self.frequency = 0
        if self.wavelength >= 300 and self.wavelength <= 2000 and self.saturation >= 0.04 and self.saturation <= 1:
            self.frequency = self.speed_of_light / self.wavelength
            self.validFreqNeedsAttention = True
            if abs(self.frequency - self.NaD2) <= self.threshold:
                if len(self.wmError) >= 10:
                    self.wmError = self.wmError[1:]
                self.wmError.append(self.frequency - self.NaD2)
                self.calibrator = True
                # print(np.mean(self.wmError))

            for i in range(len(self.targets)):
                if abs(self.frequency - self.targets[i]) <= self.threshold:
                    if self.calibrator == True:
                        self.iCalibration = i
                        self.calibrator = False
                    prop = self.targets[i] / self.targets[self.iCalibration]
                    self.frequency -= np.mean(self.wmError) * prop
                    self.data = [self.frequency, self.saturation, self.status, self.time_step]
                    self.storedData[i] = self.data[:2]
                    if self.channels[i] == 0:
                        # self.channels[i] = Channel(i)
                        # self.mainLayout.addWidget(self.channels[i])
                        # self.adjustSize()
                        self.channels[i].data = self.data
                    else:
                        self.channels[i].data = self.data
                        if abs(self.targets[i] - self.frequency) >= 0.5 * self.threshold:
                            print(f'target was: {self.targets[i]}')
                            self.targets[i] = np.mean(self.channels[i].f[-10:])
                            print(f'target  is: {self.targets[i]}')
                    self.validFreqNeedsAttention = False
                    break
                else:
                    pass

            if self.validFreqNeedsAttention == True:
                if len(self.rogueFreqs)==0:
                    self.rogueFreqs.append(f"freq: {round(self.frequency,1)} sat: {round(self.saturation,2)}")
                else:
                    test=True
                    for rogue in self.rogueFreqs:
                        if str(round(self.frequency,1))==rogue[6:14]:
                            test=False
                            break
                    if test==True:
                        self.rogueFreqs.append(f"freq: {round(self.frequency,1)} sat: {round(self.saturation,2)}")
                self.listWidget.clear()
                self.listWidget.addItems(self.rogueFreqs)
                if len(self.rogueFreqs)==12:
                    self.rogueFreqs=self.rogueFreqs[1:]
                #print(self.rogueFreqs)
            self.validFreqNeedsAttention == False


    def updateWmGraph(self):  # redraws the plot's 'line', aka datapoints. Called upon by updateChannel
        if len(self.t) >= self.plotPoints:  # keeps the number of data points at or below plotPoints.
            self.t = self.t[1:]
            self.f = self.f[1:]
        else:
            pass
        if len(self.data) == 0:
            pass
        else:
            if len(self.t) == 1:
                self.endLayout.addWidget(self.wmErrorGraph)
            else:
                pass

            self.t.append(self.time_step)  # makes a new data point, x-coordinate being time.
            self.f.append(self.wmError[-1])  # makes a new data point, y-coordinate being frequency
            ay = self.wmErrorGraph.getAxis('left')  # creates an object ay corresponding to the left axis.
            dy = [(value, '{:.3f}'.format(value)) for value in np.linspace(round(min(self.f), 3), round(max(self.f), 3),
                                                                           8)]  # creates the values to go on the left y-axis.
            ay.setTicks([dy,
                         []])  # pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
            self.wmErrorGraph.setYRange(min(self.f) - 0.002,
                                 max(self.f) + 0.002)  # we set the graph range to automatically fit the channel's data. The extra 1 MHz (0.001) space makes the data easier to view.
            self.line.setData(self.t, self.f)  # updates the datapoints shown on the graph.

    def writeData(self):
        self.counter+=1
        if self.counter % 10 == 1:
            threadWmGraph = threading.Thread(target=self.updateWmGraph)
            threadWmGraph.start()
            self.counter=1
        now = datetime.now()
        dateTimeString = now.strftime("%Y-%m-%d" + "T" + "%H:%M:%S.%f")[:-3]
        self.fileName = now.strftime("%Y-%m-%d") + ".csv"
        outputHeader = ["Timestamp"]

        for i in range(len(self.targets)):
            outputHeader.append(f"Frequency{i + 1}")
            outputHeader.append(f"Saturation{i + 1}")
        outputBody = [dateTimeString]
        for i in range(len(self.targets)):
            freq = self.storedData[i][0]
            if self.storedData[i][1] != 0:
                dbSat = round(10 * np.log(self.storedData[i][1]), 1)
            else:
                dbSat = 0
            outputBody.append(freq)
            outputBody.append(dbSat)
        outputBody.append(np.mean(self.wmError))
        outputHeader.append("wmError")
        if os.path.isfile(self.fileName) == False:
            with open(self.fileName, 'a', newline='') as f:
                write = csv.writer(f)
                write.writerow(outputHeader)
        else:
            with open(self.fileName, 'a', newline='') as f:
                write = csv.writer(f)
                write.writerow(outputBody)


def closing():
    device.serial_port.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

app.aboutToQuit.connect(closing)
w = MainWindow()
monitor = QDesktopWidget().screenGeometry(2)
w.move(monitor.left(), monitor.top())
w.showMaximized()

app.exec()
