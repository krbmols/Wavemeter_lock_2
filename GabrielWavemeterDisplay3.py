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
        self.data = [0,0,0]

        self.t = []
        self.f = []
        self.rangeY=[0,1]
        self.plotPoints = 100

        
        self.label = QLabel()
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.graph.setYRange(self.rangeY[0],self.rangeY[1])

        self.line = self.graph.plot(self.t, self.f, pen=None, symbolPen='w')

        self.channelTimer = QTimer()
        self.channelTimer.setInterval(100)
        self.channelTimer.timeout.connect(self.updateChannel)
        self.channelTimer.start()


    def updateLabel(self, name):
        self.label.setText("%s" % name)

    def updateGraph(self):
        if len(self.t) >= self.plotPoints:
            self.t = self.t[1:]
            self.f = self.f[1:]
        else:
            pass
        self.t.append(self.data[-1])
        self.f.append(self.data[0])
        self.line.setData(self.t, self.f)

    def updateChannel(self):
        self.updateGraph()
        self.std=np.std(self.f)
        self.mean=np.mean(self.f)
        self.updateLabel(f"frequency: {self.mean}. std: {round(self.std, 3)}")


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
        self.wavelength,self.saturation,__,self.time_step= device.get_measurement()
        self.frequency=0
        if self.wavelength >=100:  
            self.frequency=self.speed_of_light/self.wavelength
        self.data=[self.frequency,self.saturation,self.time_step]
        for i in range(8):
            if abs(self.targets[i] -self.frequency)<=self.threshold and abs(1.56E9-self.time_step)<.2E9:
                self.channels[i].data=self.data
            else:
                pass
            
    def updateWidgets(self):
        for i in range(8):
            mean=self.channels[i].mean
            std=self.channels[i].std
            if (mean<=10 or std<=1E-6) and self.onChannels[i]!=0:
                self.onChannels[i]=0
                self.channels[i].label.deleteLater()
                self.channels[i].graph.deleteLater()
                self.channels[i].channelTimer.stop()

            elif (mean>=10 or std>=1E-6) and self.onChannels[i]!=0:
                self.channels[i].graph.setYRange(mean-10,mean+10)
            elif (mean>=10 or std>=1E-6) and self.onChannels[i]==0:
                self.onChannels[i]=1
                self.channels[i].__init__()
                self.channels[i].channelTimer.start()
                self.layout.addWidget(self.channels[i].label,0,i)
                self.layout.addWidget(self.channels[i].graph,1,i)
        print(self.onChannels)



app = QApplication(sys.argv)

w = MainWindow()
w.show()

app.exec()

