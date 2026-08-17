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
from PyQt5.QtWidgets import QApplication, QDoubleSpinBox, QMainWindow, QGridLayout, QListWidget, QWidget, QCheckBox, \
    QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QDesktopWidget
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

global writeFile
global saveData
global dir
global path
dir="N:\\wavemeterEightChannelLogs"
path=dir+"\\20220323_fast_wm.csv"
saveData=True
if saveData:
    writeFile = open(path, 'a', newline='')

class Channel(QWidget):  # a class for the widgets belonging to a particular channel

    def __init__(self, target, threshold, parent=None):
        super(Channel, self).__init__(parent)

        self.target = target
        self.threshold=threshold
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
        self.plotPoints = 100  # the max number of points that will be shown on a graph.

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
        self.label1.setFont(QFont("Arial", 70))
        self.label1.setAlignment(Qt.AlignVCenter)

        self.label2 = QLabel()
        self.label2.setFont(QFont("Arial", 100))
        self.label2.setAlignment(Qt.AlignTop)

        self.labelUnit = QLabel()
        self.labelUnit.setFont(QFont("Arial", 15))
        self.labelUnit.setAlignment(Qt.AlignLeft)
        self.labelUnit.setText("%s" % "GHz")

        self.labelPP = QLabel()
        self.labelPP.setFont(QFont("Arial", 30))
        self.labelPP.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.labelLambda = QLabel()
        self.labelLambda.setFont(QFont("Arial", 15))
        self.labelLambda.setAlignment(Qt.AlignBottom)

        self.labelSat = QLabel()
        self.labelSat.setFont(QFont("Arial", 40))
        self.labelSat.setAlignment(Qt.AlignCenter | Qt.AlignTop)

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
        self.targetMarker = pg.InfiniteLine(pos=self.target, angle=0, pen=pg.mkPen(color=(255, 0, 0), width=2))
        self.upperThresholdMarker = pg.InfiniteLine(pos=self.target+self.threshold, angle=0, pen=pg.mkPen('b', width=2))
        self.lowerThresholdMarker = pg.InfiniteLine(pos=self.target-self.threshold, angle=0, pen=pg.mkPen('b', width=2))

        self.graph.addItem(self.targetMarker)
        self.graph.addItem(self.upperThresholdMarker)
        self.graph.addItem(self.lowerThresholdMarker)

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
        self.channelLayout.addWidget(self.labelUnit, 1, 3, 1, 1)
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
        self.graph.setXRange(max(0,timeStep-10),timeStep)
        ay = self.graph.getAxis('left')  # creates an object ay corresponding to the left axis.

        dy = [(value, '{:.3f}'.format(value)) for value in np.linspace(round(min(self.f), 3), round(max(self.f), 3),
                                                                       8)]  # creates the values to go on the left y-axis.
        ay.setTicks([dy,
                     []])  # pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
        if self.isLocked==True or timeStep-self.data[-1]>3:
            self.graph.setYRange(np.mean(self.f)-self.threshold, np.mean(self.f)+self.threshold)
            dy = [(value, '{:.3f}'.format(value)) for value in
                  np.linspace(round(np.mean(self.f)-self.threshold, 3), round(np.mean(self.f)+self.threshold, 3), 8)]
            ay.setTicks([dy,[]])
        else:
            self.graph.setYRange(min(self.f)-0.002,max(self.f)+0.002)
            dy = [(value, '{:.3f}'.format(value)) for value in
                  np.linspace(round(min(self.f),3), round(max(self.f), 3), 8)]
            ay.setTicks([dy,[]])
        self.line.setData(self.t, self.f)  # updates the datapoints shown on the graph.
        self.targetMarker.setValue(self.target)
        self.upperThresholdMarker.setValue(self.target + self.threshold)
        self.lowerThresholdMarker.setValue(self.target - self.threshold)

    def updateChannel(self):
        if timeStep-self.data[-1]>3:
            self.graph.setBackground((255,153,153))
        else:
            self.graph.setBackground('w')


        if (0.04<self.data[1]<0.1 or 0.70<self.data[1]<1.0):
            self.labelSat.setStyleSheet("background-color: yellow")
        else:
            self.labelSat.setStyleSheet("background-color: white");

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
                self.updateGraph()

            if self.counter % 90 == 1:
                self.stillLocked()

            if self.counter % 5760 == 1:
                self.counter = 1
            self.std = np.std(self.f[-20:])  # calculates peak-to-peak variation of data for the latest 100 data points
            self.mean = np.mean(self.f)

            # below, we generate the name for the two labels corresponding to the laser frequency. The first label gives the THz and GHz information, while the second label gives the MHz scale.
            num, decimal = [int(self.f[-1]), str(round(float(self.f[-1]) - int(self.f[-1]), 3))[1:]]
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
        self.plotPoints = 1000
        self.calibrateQ = True

        # self.path = 'C:\Bristol'
        # self.path='C:\Users\Krb-Logging\Desktop\Logs'
        # self.path='C:\Users\Krb-Logging\Desktop'
        if saveData:
            os.chdir(dir)
        self.t = []  # list of the plot datapoint's x-coordinates
        self.f = []  # list of the plot datapoint's y-coordinates
        self.Rb5s6p = 713281.7400
        self.NaD2 = 508848.9217
        self.KRbSTIRAP690=434922.3375 #empirically determined by using the Na D2for callibration
        self.calibF=self.NaD2
        self.red = 472158.8
        self.iCalibration = 1
        self.wmError = [0]
        #self.fileName = "N:\\fastWavemeterLogs\\test.csv"
        self.calibrator = False
        self.counter = 1
        self.speed_of_light = 299792458
        # 713289 lingbang's UV, 295157

        # self.f = open(self.fileName, 'a', newline='')

        # self.wmErrorGraph = pg.PlotWidget(title='Wavemeter Error')
        # self.wmErrorGraph.setBackground('w')

        # self.line = self.wmErrorGraph.plot(self.t, self.f, pen=None,
        #                            symbolPen='w')  # graph denotes the axes, and line denotes the datapoints. When we update the plot, we only need to redraw the line.
        #472158.192->STIRAP NaCs Red


        self.targets = [508848.9217, 508332.609, 295170, 434922.3375, 713289, 320013.168,
                        328966, 282683.8]
        self.thresholds=[10.0]*len(self.targets)
        self.targets.sort(reverse=True)
        self.wmErrorAvgNo = 5
        self.storedData = [[0, 0]] * len(self.targets)
        self.timeStart = time()
        self.rogueFreqs = []
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
        self.thresholdLayout = QHBoxLayout()
        self.targetWidgets = [0] * len(self.targets);
        self.thresholdWidgets = [0] * len(self.thresholds);
        for i in range(len(self.targets)):
            self.targetWidgets[i] = QDoubleSpinBox(self)
            self.targetWidgets[i].setFont(QFont("Arial", 14))
            self.targetWidgets[i].setDecimals(3)
            self.targetWidgets[i].setRange(200000, 900000)
            self.targetWidgets[i].setValue(self.targets[i])
            self.targetWidgets[i].setSingleStep(0.001)
            #self.targetWidgets[i].setSuffix(" GHz")
            self.targetWidgets[i].valueChanged.connect(self.targetChange)
            self.targetLayout.addWidget(self.targetWidgets[i])

            self.thresholdWidgets[i] = QDoubleSpinBox(self)
            self.thresholdWidgets[i].setFont(QFont("Arial", 14))
            self.thresholdWidgets[i].setDecimals(3)
            self.thresholdWidgets[i].setRange(0.001, 5000)
            self.thresholdWidgets[i].setValue(self.thresholds[i])
            self.thresholdWidgets[i].setSingleStep(0.001)
            self.thresholdWidgets[i].setPrefix("±")
            self.thresholdWidgets[i].setSuffix(" GHz")
            self.thresholdWidgets[i].valueChanged.connect(self.thresholdChange)
            self.thresholdLayout.addWidget(self.thresholdWidgets[i])
        self.endLayout = QHBoxLayout()
        self.endLayout.setSpacing(0)
        self.endLayout.setContentsMargins(0, 0, 0, 0)

        self.listWidget = QListWidget(self)
        self.listWidget.setMaximumSize(250, 200)

        self.wmErrorLabel = QLabel()
        self.wmErrorLabel.setFont(QFont("Arial", 15))

        self.calCombo = QComboBox()
        self.calCombo.addItem("Na D2")
        self.calCombo.addItem("KRb STIRAP")
        self.calCombo.addItem("No calibration")
        self.calCombo.currentIndexChanged.connect(self.changeCalibration)

        self.wmErrorAvging = QDoubleSpinBox(self)
        self.wmErrorAvging.setFont(QFont("Arial", 15))
        self.wmErrorAvging.setRange(1, 100)
        self.wmErrorAvging.setValue(self.wmErrorAvgNo)
        self.wmErrorAvging.setSingleStep(1)
        self.wmErrorAvging.valueChanged.connect(self.wmErrorAvgNoChange)

        self.endLayout.addWidget(self.listWidget)
        self.endLayout.addWidget(self.wmErrorLabel)
        self.endLayout.addWidget(self.calCombo)

        self.endLayout.addWidget(self.wmErrorAvging)

        self.mainLayout = QVBoxLayout()
        self.mainWidget = QWidget()
        self.mainLayout.addLayout(self.targetLayout)
        self.mainLayout.addLayout(self.thresholdLayout)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        self.channels = [0] * len(self.targets)
        for i in range(len(self.targets)):
            self.channels[i] = Channel(self.targets[i],self.thresholds[i])
            self.mainLayout.addWidget(self.channels[i])
            self.channels[i].data = [self.targets[i],0,0,1]
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
                #self.thresholds = [i for _, i in sorted(zip(self.thresholds,self.targets))].reverse
                self.targets.sort(reverse=True)
                self.channels[i].target = self.targets[i]
    def thresholdChange(self, i):

        for i in range(len(self.thresholdWidgets)):
            if self.thresholds[i] == self.thresholdWidgets[i].value():
                pass
            else:
                self.thresholds[i] = self.thresholdWidgets[i].value()
                self.channels[i].threshold = self.thresholds[i]

    def wmErrorAvgNoChange(self, no):
        self.wmErrorAvgNo = int(no)

    def createData(self):
        self.wavelength, self.saturation, self.status, self.wmTime = device.get_measurement()
        #if(1050<self.wavelength<1100):
         #   print(f"test: {float(self.speed_of_light / self.wavelength)}")

        global timeStep
        timeStep = time()-self.timeStart
        self.frequency = 0
        if self.wavelength >= 300 and self.wavelength <= 2000 and self.saturation >= 0.05 and self.saturation <= 1:
            self.frequency = float(self.speed_of_light / self.wavelength)
            self.validFreqNeedsAttention = True
            if (self.calibF-50.<self.frequency<self.calibF+50.0):
                if len(self.wmError) >= self.wmErrorAvgNo:
                    deviation = len(self.wmError) - self.wmErrorAvgNo + 1
                    self.wmError = self.wmError[deviation:]
                self.wmError.append(self.frequency - self.calibF)
                self.calibrator = True
            if self.calibrateQ==True:
                prop=self.frequency/self.calibF
                self.frequency-=np.mean(self.wmError)*prop
            for i in range(len(self.targets)):
                if (self.targets[i]-self.thresholds[i]<self.frequency<self.targets[i]+self.thresholds[i]):
                    self.data = [self.frequency, self.saturation, self.status,timeStep]
                    self.storedData[i] = self.data[:2]
                    self.channels[i].data = self.data
                    if abs(self.targets[i] - self.frequency) >= 0.5 * self.thresholds[i]:
                        print(f'target was: {self.targets[i]}')
                        self.targets[i] = np.mean(self.channels[i].f[-10:])
                        print(f'target  is: {self.targets[i]}')
                    self.validFreqNeedsAttention = False
                    break
                else:
                    pass


    def changeCalibration(self, calib):
        if calib==0:
            self.calibF=float(self.NaD2)
            self.calibrateQ = True
        elif calib==1:
            self.calibF=float(self.KRbSTIRAP690)
            self.calibrateQ = True
        elif calib==2:
            self.calibrateQ=False

    def updateCalibrator(self):
        #see if calibF frequency has been called recenty, or anything near it (recall, if the wmError range is larger
        # than 1 then the frequency of the calibration channel will drift.
        ok=False
        for i in range(8):
            data=self.channels[i].data
            if (self.calibF-self.thresholds[i]<data[0]<self.targets[i]+self.thresholds[i]):
                if abs(data[-1]-timeStep)<=3:
                    ok=True
                    break
                else:
                    index=self.calCombo.currentIndex()
                    count=self.calCombo.count()
                    if index==count-2:
                        self.calCombo.setCurrentIndex(0)
                        ok=True
                    else:
                        self.calCombo.setCurrentIndex(index+1)
                        print("New value:"+str(self.calCombo.currentIndex()))
                        ok=True
                    break
        if ok==False:
            print("I am not ok. Current index:" + str(self.calCombo.currentIndex()))
            index = self.calCombo.currentIndex()
            count = self.calCombo.count()
            if index == count - 2:
                self.calCombo.setCurrentIndex(0)
            else:
                self.calCombo.setCurrentIndex(index + 1)

        #if calibF has not been called recently, change to the other calibF, excluding the final entry of the list
        # because that corresponds to being uncalibrated. Remember to change the combo box value.

    def writeData(self):
        #self.updateCalibrator()
        if self.validFreqNeedsAttention == True:
            now = datetime.now()
            dateTimeString = now.strftime("%H:%M:%S.%f")[:-5]
            self.rogueFreqs.append(f"t={dateTimeString}, f: {round(self.frequency, 0)} GHz, sat: {round(100*self.saturation,1)}%")
            self.listWidget.clear()
            self.listWidget.addItems(self.rogueFreqs)
            if len(self.rogueFreqs) == 4:
                self.rogueFreqs = self.rogueFreqs[1:]
            # print(self.frequency)
        self.validFreqNeedsAttention == False
        now = datetime.now()
        dateTimeString = now.strftime("%Y-%m-%d" + "T" + "%H:%M:%S.%f")[:-3]
        ####THIS WOULD RESET THE FILE NAME AT MIDNIGHT; PROBLEMATIC FOR OVERNIGHT SCANS.####
        # self.fileName = now.strftime("%Y-%m-%d") + ".csv"
        self.wmErrorLabel.setText(f"wmError: {round(1000 * self.wmError[-1])} MHz")
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
            if self.storedData[i][1] != 0:
                    outputBody.append(freq)
                    outputBody.append(dbSat)
        outputBody.append(np.mean(self.wmError))
        outputHeader.append("wmError")
        if saveData:
            if os.path.isfile(path) == False:
                with open(path, 'a', newline='') as f:
                    write = csv.writer(writeFile)
                    write.writerow(outputHeader)
            else:
                with open(path, 'a', newline='') as f:
                    write = csv.writer(writeFile)
                    write.writerow(outputBody)
                    print(f"Output:{outputBody}")


def closing():
    device.serial_port.close()
    writeFile.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

app.aboutToQuit.connect(closing)
w = MainWindow()
monitor = QDesktopWidget().screenGeometry(2)
w.move(monitor.left(), monitor.top())
w.show()

app.exec()
