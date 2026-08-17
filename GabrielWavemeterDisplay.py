import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QGridLayout,QWidget,QDoubleSpinBox,QLabel
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import numpy as np

from bristol_RS422 import BristolRS422
from Read_Data import *
global portnumber 
portnumber="COM10"
global device
global deviation
deviation=50
global fontSize
fontSize=30
device=BristolRS422(portnumber)

pg.setConfigOptions(antialias=True)
  

class MainWindow(QMainWindow):
    
    def __init__(self,*args,**kwargs):
        super(MainWindow,self).__init__(*args,**kwargs)
        self.setWindowTitle("Wavemeter GUI")
        

        self.x1 = []
        self.y1 = []
        self.avg1=[]
        self.x2 = []
        self.y2 = []
        self.avg2=[]
        self.rangeY1=100
        self.rangeY2=100
        self.rangeX1=100
        self.rangeX2=100
        self.speed_of_light=299792458
        self.targetFs=[295177,713281]
        self.f1=[[0.,0.1]]
        self.f2=[[0.,0.]]
        self.f3=[[0.,0.]]
        self.f4=[[0.,0.]]
        self.f5=[[0.,0.]]
        self.f6=[[0.,0.]]
        self.f7=[[0.,0.]]
        self.f8=[[0.,0.]]
        self.fList=[self.f1,self.f2,self.f3,self.f4,self.f5,self.f6,self.f7,self.f8]
        self.error=50000
        
        
        self.graphf1=pg.PlotWidget()
        self.graphf2=pg.PlotWidget()
        self.target1=QDoubleSpinBox()
        self.target1.setSuffix(" GHz")
        self.target1.setMinimum(0)
        self.target1.setMaximum(1000000)
        self.target1.setSingleStep(.01)
        self.target1.setValue(self.targetFs[1-1])
        
        self.rangeGuiY1=QDoubleSpinBox()
        self.rangeGuiY1.setSuffix(" MHz")
        self.rangeGuiY1.setMinimum(1)
        self.rangeGuiY1.setMaximum(1000)
        self.rangeGuiY1.setSingleStep(5)
        self.rangeGuiY1.setValue(self.rangeY1)
        
        self.rangeGuiX1=QDoubleSpinBox()
        self.rangeGuiX1.setSuffix(" points")
        self.rangeGuiX1.setMinimum(1)
        self.rangeGuiX1.setMaximum(10000)
        self.rangeGuiX1.setSingleStep(100)
        self.rangeGuiX1.setValue(self.rangeX1)
        
        self.f1Label=QLabel()
        self.f1Label.setText("%f GHz" %self.f1[-1][0])
        self.f1Label.setFont(QFont("Arial",fontSize))
        self.f2Label=QLabel()
        self.f2Label.setText("%f GHz" %self.f2[-1][0])
        self.f2Label.setFont(QFont("Arial",fontSize))
        
        self.graphf1.setBackground('w')
        self.graphf2.setBackground('w')
        
        styles={"color":"b","font-size":'15pt'}
        self.graphf1.setLabel('left','Frequency - %f (GHz)'%self.targetFs[1-1],**styles)
        self.graphf1.setLabel('bottom','Time (points)',**styles)   
        self.graphf2.setLabel('left','Frequency - %f (GHz)'%self.targetFs[2-1],**styles)
        self.graphf2.setLabel('bottom','Time (points)',**styles) 
        
        self.graphf1.setYRange(-0.001*self.rangeY1,0.001*self.rangeY1)
        self.graphf2.setYRange(-.001*self.rangeY2,0.001*self.rangeY2)
        
        pen=pg.mkPen(color=(255,0,0),width=2,)
        self.linef11=self.graphf1.plot(self.x1,self.y1,pen=None,symbolPen='w')
        self.linef12=self.graphf1.plot(self.x1,self.avg1,pen=pen)        
        
        self.linef21=self.graphf2.plot(self.x2,self.y2,pen=None,symbolPen='w')
        self.linef22=self.graphf2.plot(self.x2,self.avg2,pen=pen)  
        
        
        self.target1.valueChanged.connect(self.updateTarget1)
        self.rangeGuiY1.valueChanged.connect(self.updateRangeY1)
        self.rangeGuiX1.valueChanged.connect(self.updateRangeX1)
        
        self.qTimer1=QtCore.QTimer()
        self.qTimer1.setInterval(3) # 16 milliseconds
        self.qTimer1.timeout.connect(self.mainFunction)
        
        self.qTimer2=QtCore.QTimer()
        self.qTimer2.setInterval(20)
        self.qTimer2.timeout.connect(self.updatePlotData)

        self.qTimer3=QtCore.QTimer()
        self.qTimer3.setInterval(10000)
        "self.qTimer3.timeout.connect(self.updateTargets)"
        
        print(self.targetFs)

        self.qTimer1.start()
        self.qTimer2.start()
        self.qTimer3.start()
        

        layout=QGridLayout()
        layout.addWidget(self.target1,1,0)
        layout.addWidget(self.rangeGuiY1,1,1)
        layout.addWidget(self.rangeGuiX1,1,2)
        layout.addWidget(self.f1Label,0,0,1,3)
        layout.addWidget(self.f2Label,0,3,1,3)
        layout.addWidget(self.graphf1,2,0,1,3)
        layout.addWidget(self.graphf2,2,3,1,3)
        widget=QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
    def updateTarget1(self,newTarget1):
        self.targetFs[1-1]=newTarget1
        print(self.targetFs)
    def updateRangeY1(self,newRangeY1):
        self.rangeY1=newRangeY1
        self.graphf1.setYRange(-0.001*self.rangeY1,0.001*self.rangeY1)
        self.graphf2.setYRange(-.001*self.rangeY1,0.001*self.rangeY1)
    def updateRangeX1(self,newRangeX1):
        self.rangeX1=newRangeX1
        
    def updateTargets(self):
        self.targetFs=[self.f1[-1][1],self.f2[-1][1],self.f3[-1][1],self.f4[-1][1],self.f5[-1][1],self.f6[-1][1],self.f7[-1][1],self.f8[-1][1]]
    def mainFunction(self):

        # the original get sensor value code
        global device
        
        self.wavelength,self.saturation,__,self.time_step=device.get_measurement()
        self.frequency=0
        if (self.wavelength>100 and self.time_step>80000000 and self.time_step<200000000): 
            self.frequency=self.speed_of_light/self.wavelength
            for i in range(len(self.targetFs)):
                if (abs(self.targetFs[i]-self.frequency))<self.error:
                    self.fList[i].append([self.time_step,self.frequency])           
            
    def updatePlotData(self):
        if len(self.x1)>=self.rangeX1:
            self.x1=self.x1[1:]
            self.y1=self.y1[1:]
            self.avg1=self.avg1[1:]
        if len(self.x2)>=self.rangeX2:
            self.x2=self.x2[1:]
            self.y2=self.y2[1:]
            self.avg2=self.avg2[1:]
        else:
            pass
        self.x1.append(self.f1[-1][0])
        self.y1.append((self.f1[-1][1])-self.targetFs[1-1])
        self.avg1.append(sum(self.y1[-20:])/len(self.y1[-20:]))
        
        self.x2.append(self.f2[-1][0])
        self.y2.append((self.f2[-1][1])-self.targetFs[2-1])
        self.avg2.append(sum(self.y2[-20:])/len(self.y2[-20:]))
        
        self.linef11.setData(self.x1,self.y1)
        self.linef12.setData(self.x1[10:],self.avg1[:-10])
        self.linef21.setData(self.x2,self.y2)
        self.linef22.setData(self.x2[10:],self.avg2[:-10])
        
        self.f1Label.setText("%f GHz" %(self.y1[-1]+self.targetFs[1-1]))
        self.f2Label.setText("%f GHz" %(self.y2[-1]+self.targetFs[2-1]))
        styles={"color":"b","font-size":'15pt'}
        self.graphf1.setLabel('left','Frequency - %f (GHz)'%self.targetFs[1-1],**styles)
        self.graphf2.setLabel('left','Frequency - %f (GHz)'%self.targetFs[2-1],**styles)
        
        
app=QApplication(sys.argv)

w=MainWindow()
w.show()

app.exec()
