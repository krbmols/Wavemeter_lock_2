# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 09:57:54 2021

@author: Gabriel Patenotte, inspired by Lingbang and Bryant
"""
import sys 
import os 
import csv
import numpy as np 
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel, QVBoxLayout 
from PyQt5.QtCore import QTimer, Qt 
import pyqtgraph as pg
from bristol_RS422 import BristolRS422
from PyQt5.QtGui import QFont
from datetime import datetime
from time import time


global portnumber 
portnumber="COM10" #the usb port to which the wavemeter is connected
global device
device=BristolRS422(portnumber) #the BristolRS422 python file collects measurements from the Bristol 871a wavemeter
pg.setConfigOptions(antialias=True) #antialiasing makes the graphs easier to view

class Channel(QWidget): #a class for the widgets belonging to a particular channel

    def __init__(self,i,parent=None):
        super(Channel, self).__init__(parent)
        self.firstUpdate=True #if true, the object has just been created.
        self.currentStatus=0 #Status of the wavemeter. See self.dictionary to see what each status corresponds to.
        self.data = [0,0,0,0] #initial values for the channel's stored data. In order of frequency, saturation, status, and time.
        self.t = [] #list of the plot datapoint's x-coordinates
        self.f = [] #list of the plot datapoint's y-coordinates
        self.speed_of_light=299792458.
        self.plotPoints = 200 #the max number of points that will be shown on a graph.
        
        self.dictionary={0: 'inactive channel',4: 'reference laser locked',8: 'etalon fringe error',16: 'etalon saturation error', 2048: 'reference laser not stable', 8192: 'temperature high', 16384: 'temperature low',32768: 'pressure high',65536: 'pressure low', 131072: 'wavelength outside instrument specification', 524288: 'etalon fringe error',1048576: 'etalon saturation error', 2097152: 'calibration in progress', 4194304: 'etalon fringe error', 8388608: 'etalon sat',536870912: 'low detector signal', 536870916: 'low detector signal?', 1073741824: 'fringe frequency error'}
        #The dictionary converts between the binary wavemeter signal and what the binary message signifies.
        
        #In the following lines we generate several labels and a plot.
        self.label1 = QLabel() 
        self.label1.setFont(QFont("Arial",50))
        self.label1.setAlignment(Qt.AlignTop)
        
        self.label2 = QLabel()
        self.label2.setFont(QFont("Arial",80))
        self.label2.setAlignment(Qt.AlignBottom)
        
        self.labelPP = QLabel()
        self.labelPP.setFont(QFont("Arial",30))
        self.labelPP.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.labelLambda = QLabel()
        self.labelLambda.setFont(QFont("Arial",15))
        self.labelLambda.setAlignment(Qt.AlignBottom)
        
        self.labelSat = QLabel()
        self.labelSat.setFont(QFont("Arial",45))
        self.labelSat.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.labelStatus = QLabel()
        self.labelStatus.setFont(QFont("Arial",15))
        self.labelStatus.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.line = self.graph.plot(self.t, self.f, pen=None, symbolPen='w') #graph denotes the axes, and line denotes the datapoints. When we update the plot, we only need to redraw the line.

        #We initialize a QTimer. The setInterval argument specifies how often the argument in connect() occurs.
        self.channelTimer = QTimer()
        self.channelTimer.setInterval(100)
        self.channelTimer.timeout.connect(self.updateChannel)
        self.channelTimer.start()
        
        #We layout the position of the channel's widgets. In addWidget, the four numbers denote y and x position, and height and width of the widget.
        channelLayout=QGridLayout()
        self.setLayout(channelLayout)
        channelLayout.addWidget(self.label1,1,0,1,1)
        channelLayout.addWidget(self.label2,0,1,2,1)
        channelLayout.addWidget(self.labelPP,2,1,1,1)
        channelLayout.addWidget(self.labelLambda,0,0,1,1)
        channelLayout.addWidget(self.labelSat,2,0,1,1)
        channelLayout.addWidget(self.labelStatus,3,0,1,2)
        channelLayout.addWidget(self.graph,0,3,4,1)
        channelLayout.setSpacing(0)
        channelLayout.setContentsMargins(0, 0, 0, 0)
        
  
    def updateLabel(self, name1,name2,name3,name4,name5): #updates the value in the labels. Called upon by updateChannel
        self.label1.setText("%s" % name1)
        self.label2.setText("%s" % name2)
        self.labelPP.setText("%s" % name3)
        self.labelLambda.setText("%s" % name4)
        self.labelSat.setText("%s" % name5)
        #summary of if statement: if the channel is assigned a new status, try matching the status to the dictionary. If the dictionary doesn't know what the status is, print a statement showing the unknown status.
        if self.data[2]!=self.currentStatus:
            self.currentStatus=self.data[2]
            try:
                name6=self.dictionary[self.currentStatus]
            except:
                name6="Unknown status"
                print(f'Unknown status {self.currentStatus} for frequency {self.data[0]}')
            self.labelStatus.setText(f"status: {name6}")

    def updateGraph(self): #redraws the plot's 'line', aka datapoints. Called upon by updateChannel
        ay = self.graph.getAxis('left') #creates an object ay corresponding to the left axis.
        dy = [(value, '{:.3f}'.format(value)) for value in np.linspace(round(min(self.f),3),round(max(self.f),3),5)] #creates the values to go on the left y-axis.
        ay.setTicks([dy, []]) #pyqtgraph's automatic y-axis labels don't show decimal places, so we put in our own labels given by dy.
        self.graph.setYRange(1.5*min(self.f)-0.5*np.mean(self.f)-.001,1.5*max(self.f)-0.5*np.mean(self.f)+.001) #we set the graph range to automatically fit the channel's data. The extra 1 MHz (0.001) space makes the data easier to view.
        self.line.setData(self.t, self.f) #updates the datapoints shown on the graph.

    def updateChannel(self):
        if len(self.t) >= self.plotPoints: #keeps the number of data points at or below plotPoints.
            self.t = self.t[1:]
            self.f = self.f[1:]
        else:
            pass
        self.t.append(self.data[-1]) #makes a new data point, x-coordinate being time.
        self.f.append(self.data[0]) #makes a new data point, y-coordinate being frequency
        self.updateGraph() 

        self.ptp=np.ptp(self.f[-20:]) #calculates peak-to-peak variation of data for the latest 100 data points
        self.mean=np.mean(self.f)
        
        #below, we generate the name for the two labels corresponding to the laser frequency. The first label gives the THz and GHz information, while the second label gives the MHz scale.
        num, decimal = [int(self.f[-1]),str(round(self.f[-1]-int(self.f[-1]),4))[1:]]
        if self.ptp<=1:
            name3='±'+'{:.1f}'.format(1000*self.ptp)+" MHz"
        elif self.ptp<=1E3:
            name3='±'+'{:.2f}'.format(self.ptp)+" GHz"
        else:
            name3='±'+'{:.2f}'.format(0.001*self.ptp)+" THz"
        self.updateLabel(f"{num}",(f"{decimal}"+"000")[:5],name3,'{:.1f}'.format(self.speed_of_light/self.f[-1])+" nm",'{:.4f}'.format(self.data[1]))
 
        # if self.firstUpdate==True: #We initialize the graph before any data is received by the channel object.
        #     self.target=self.mean
        #     self.rangeY=10*self.ptp
        #     self.graph.setYRange(self.target-self.rangeY/2-.0005,self.target+self.rangeY/2+.0005)
        #     self.firstUpdate=False


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Wavemeter GUI")
        # self.path='N:\wavemeterEightChannelLogs'
        self.path='C:\Bristol'
        # self.path='C:\Users\Krb-Logging\Desktop\Logs'
        # self.path='C:\Users\Krb-Logging\Desktop'
        os.chdir(self.path)
        self.Rb5s6p = 713281.7400  
        self.NaD2=508848.92
        self.red=472158.8
        self.iCalibration=1
        self.wmError=[0]
        self.calibrator=False
        self.offChannels=[]
        self.offTargets=[]
        self.updateWidgetCounter=0
        self.speed_of_light=299792458
        # 713289 lingbang's UV, 295157
        self.targets=[353600,351721,508849,508333.19,325100,472149.8,713289,328966.9]
        self.threshold=200
        self.storedData=[[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
        self.timeStart=time()
        self.fileName='wm8Data25.csv'
        self.timeReference=self.timeStart
        
        self.mainTimer = QTimer()
        self.mainTimer.setInterval(1)
        self.mainTimer.timeout.connect(self.createData)
        self.mainTimer.start()
    
        self.widgetTimer = QTimer()
        self.widgetTimer.setInterval(100)
        self.widgetTimer.timeout.connect(self.writeData)
        self.widgetTimer.start()
        
        self.mainLayout = QVBoxLayout()
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        self.channels = [0,0,0,0,0,0,0,0]
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        

    def createData(self):
        self.wavelength,self.saturation,self.status,self.time_step= device.get_measurement()
        self.time_step=time()
        self.time_step=self.time_step-self.timeStart
        self.frequency=0
        if self.wavelength >=100 and self.wavelength<=2000 and self.saturation>=0 and self.saturation<=1:  
            self.frequency=self.speed_of_light/self.wavelength
            self.validFreqNeedsAttention=True
            if abs(self.frequency-self.NaD2)<=self.threshold:
                    if len(self.wmError)>= 2:
                        self.wmError=self.wmError[1:]
                    self.wmError.append(self.frequency-self.NaD2)
                    self.calibrator=True
                    print(np.mean(self.wmError))
            
            for i in range(8):
                if abs(self.frequency-self.targets[i])<=self.threshold:
                    if self.calibrator==True:
                        self.iCalibration=i
                        self.calibrator=False
                    # if i==1:
                    #     prop=0.68
                    # elif i==4:
                    #     prop=1.48
                    # elif i==8:
                    #     prop=1.37
                    # else:
                    #     prop=self.targets[i]/self.targets[self.iCalibration]
                    prop=self.targets[i]/self.targets[self.iCalibration]
                    # if i==7:
                    self.frequency-=np.mean(self.wmError)*prop
                    self.data=[self.frequency,self.saturation,self.status,self.time_step]
                    self.storedData[i]=self.data[:2]
                    if self.channels[i]==0:
                        self.channels[i]=Channel(i)
                        self.mainLayout.addWidget(self.channels[i])
                        self.adjustSize()
                        self.channels[i].data=self.data
                    else:
                        self.channels[i].data=self.data
                        if abs(self.targets[i]-self.frequency)>=0.5*self.threshold:
                            print(f'target was: {self.targets[i]}')
                            self.targets[i]=np.mean(self.channels[i].f[-10:])
                            print(f'target  is: {self.targets[i]}')
                    self.validFreqNeedsAttention=False
                    break
                else:
                    pass
            
            if self.validFreqNeedsAttention==True:
                print(f'Switching an inactive target to {self.frequency}')
            #     for i in range(8):
            #         if self.channels[i]==0:
            #             self.offTargets.append(self.targets[i])
            #         else:
            #             self.offTargets.append(0)
            #     print(f'self.offTargets={self.offTargets}')
            #     try:
            #         self.closestOffTarget=min(self.offTargets,key=lambda x:(abs(x-self.frequency)))
            #     except:
            #         self.closestOffTarget=[]
            #     print('self.closestOffTarget={self.closestOffTarget}')
            #     try:
            #         self.targets[self.targets.index(self.closestOffTarget)]=self.frequency
            #         self.validFreqNeedsAttention=False
            #         print(f'self.targets.index(self.closestOffTarget)={self.targets.index(self.closestOffTarget)}')
            #     except:
            #         print(f'failure to assign {self.frequency}. The targets are {self.targets} and the offTargets are {self.offTargets}')
            #     self.offChannels=[]
            #     self.offTargets=[]
            self.validFreqNeedsAttention==False
    def writeData(self):
        now=datetime.now()
        dateTimeString=now.strftime("%Y-%m-%d"+"T"+"%H:%M:%S.%f")[:-3]
        outputHeader=["Timestamp"]
        for i in range(8):
            outputHeader.append(f"Channel {i+1} Frequency (GHz)")
            outputHeader.append(f"Channel {i+1} Saturation")
        outputBody=[dateTimeString]
        for i in range(8):
            freq=self.storedData[i][0]
            if self.storedData[i][1]!=0:
                dbSat=round(10*np.log(self.storedData[i][1]),1)
            else:
                dbSat=0
            outputBody.append(freq)
            outputBody.append(dbSat)
        outputBody.append(np.mean(self.wmError))
        outputHeader.append("wmError")
        if os.path.isfile(self.fileName)==False:
             with open(self.fileName,'a', newline='') as f:
                write = csv.writer(f) 
                write.writerow(outputHeader)
        else:
            with open(self.fileName,'a', newline='') as f:
                write = csv.writer(f) 
                write.writerow(outputBody)
        if self.updateWidgetCounter%5==0:
            self.updateWidgets()
        self.updateWidgetCounter+=1 
        
    def updateWidgets(self):
        self.timeReference=self.time_step
        for i in range(8):
            if self.channels[i]!=0:
                if self.time_step-self.channels[i].data[-1]>=1:
                    self.channels[i].deleteLater()
                    self.channels[i]=0
                    self.storedData[i]=[0,0]
                    self.adjustSize()

def closing():
    device.serial_port.close()
    
if __name__ == '__main__':
    app = QApplication(sys.argv)

app.aboutToQuit.connect(closing)
w = MainWindow()
w.show()

app.exec()


