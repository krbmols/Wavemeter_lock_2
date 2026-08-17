import sys

import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from random import randint
from csv import writer
from bristol_RS422 import BristolRS422
from sys import exit
from Read_Data import *
from bristol_RS422 import BristolRS422
from sys import exit
from Read_Data import *
global portnumber 
portnumber="COM10"
global device
device=BristolRS422(portnumber)

class Channel:

    def __init__(self):
        self.data = [0]

        self.x = []
        self.y = []
        self.avg = []
        self.plotPoints = 100
        self.rangeY = [0, 8]
        
        self.label = QLabel()
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')

        self.line = self.graph.plot(self.x, self.y, pen=None, symbolPen='w')

        self.timeCounter = 0
        self.channelTimer = QTimer()
        self.channelTimer.setInterval(100)
        self.channelTimer.timeout.connect(self.updateChannel)
        self.channelTimer.start()


    def updateLabel(self, name):
        self.label.setText("%s" % name)

    def updateGraph(self):
        if len(self.x) >= self.plotPoints:
            self.x = self.x[1:]
            self.y = self.y[1:]
        else:
            pass
        self.x.append(self.timeCounter)
        self.y.append(self.data[-1])
        self.line.setData(self.x, self.y)

    def updateChannel(self):
        self.timeCounter += 1
        self.updateGraph()
        self.std=np.std(self.y)
        self.updateLabel(f"frequency: {self.data[-1]}. std: {round(self.std, 3)}")


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Wavemeter GUI")
        self.layout = QGridLayout()
        
        self.speed_of_light=299792458
        self.targets=[381679,713281,508332,0,0,0,295500,700000]
        self.threshold=10000
        self.onChannels=[1,1,1,1,1,1,1,1]
        
        
        self.mainTimer = QTimer()
        self.mainTimer.setInterval(5)
        self.mainTimer.timeout.connect(self.createData)
        self.mainTimer.start()
        
        self.widgetTimer = QTimer()
        self.widgetTimer.setInterval(1000)
        self.widgetTimer.timeout.connect(self.updateWidgets)
        self.widgetTimer.start()
        
        
        self.channels = [Channel() for i in range(8)]
        
        for i in range(8):
            self.layout.addWidget(self.channels[i].label, 0, i)
            self.layout.addWidget(self.channels[i].graph, 1, i)
            
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

    def createData(self):
        self.wavelength,self.saturation,__,self.time_step= device.get_measurement()[0]
        self.frequency=0
        if self.wavelength >=100:  
            self.frequency=self.speed_of_light/self.wavelength

        for i in range(8):
            if abs(self.targets[i] -self.frequency) <=self.threshold:
                
                self.channels[i].data.append(self.frequency)
                self.channels[i].data = self.channels[i].data[1:]
            else:
                pass
        print(self.channels[2].data[-1])
    def updateWidgets(self):
        for i in range(8):
            if (np.mean(self.channels[i].data)<=10 or self.channels[i].std<=1E-6) and self.onChannels[i]!=0:
                self.onChannels[i]=0
                self.channels[i].label.deleteLater()
                self.channels[i].graph.deleteLater()
                self.channels[i].channelTimer.stop()
            elif np.mean(self.channels[i].data)>=10 and np.std(self.channels[i].data)>=1E-6 and self.onChannels[i]==0:
                self.layout.addWidget(self.channels[i].label, 0, i)
                self.layout.addWidget(self.channels[i].graph, 1, i)
            else:
                pass
        print(self.onChannels)
        print(np.mean(self.channels[2].data))
        print(self.channels[2].std)


app = QApplication(sys.argv)

w = MainWindow()
w.show()

app.exec()
