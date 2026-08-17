from __future__ import print_function
import sys 
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QWindow
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (QApplication,QWidget,QMessageBox,QFormLayout)
import numpy as np
import time 
import random
import threading
from datetime import date

#importing to read from wavemeter and to save the data

from bristol_RS422 import BristolRS422
from sys import exit
from Read_Data import *
global portnumber 
portnumber="COM10"
global device
device=BristolRS422(portnumber)

global num_cycle
num_cycle = 0
### Stop the code when it is on


class Application(QWidget):
    def __init__(self):
        super().__init__()
        
        self.resize(1920,1080)
        #here is where you can write your filename as a string: no need to add .csv to the end
        today = date.today()
        self.file_name=today.strftime("%b-%d-%Y")
        
        #converting wavelength to frequency by c=lv, where l is wavelength
        self.speed_of_light=299792458       
        mainlayout= QGridLayout()
        #where we will save the arrays: array_of_frequencies will store the frequencies of all stored lasers,
       #array of time steps will store the time step the reading was done
        self.array_of_frequencies=[]
        self.array_of_timesteps=[]
        self.array_of_wavelengths=[]
        
        #variable to set a threshold for monitoring different wavelengths
        self.threshold=300 #gHz

    
        
        #port in order to access readings from wavemeter 

        #global portnumber 
        #self.device=BristolRS422(portnumber)
        #self.device1=self.device    
        
        
        self.i=[351679,713281,508332,508849,400000,500000,295500,700000] #array to store target values for lasers being used for testing: self.i[0] is the value regarding 
        #the first lasers, self.i[1] with second laser, etc.
        self.i_actual=[0,0,0,0,0,0,0,0]
        #array to display saturation from 0% to 100%
        self.saturation_levels=[0,0,0,0,0,0,0,0]
        
        global Font_sizes
        Font_sizes = 30


        #adding the tab for all of our stuff
        #what we are doing here is just displaying all of the labels
        #actual expected reading
        self.expected_first=QLabel()
        self.expected_first.setText("Target: %f" %self.i[0])
        self.expected_first.setStyleSheet("color:red")
        self.expected_first.setFont(QFont("Arial",Font_sizes))

        self.expected_second=QLabel()
        self.expected_second.setText("Target: %f" %self.i[1])
        self.expected_second.setStyleSheet("color:Blue")
        self.expected_second.setFont(QFont("Arial",Font_sizes))

        self.expected_third=QLabel()
        self.expected_third.setText("Target: %f" %self.i[2])
        self.expected_third.setStyleSheet("color:purple")
        self.expected_third.setFont(QFont("Arial",Font_sizes))

        self.expected_fourth=QLabel()
        self.expected_fourth.setText("Target: %f" %self.i[3])
        self.expected_fourth.setStyleSheet("color:green")
        self.expected_fourth.setFont(QFont("Arial",Font_sizes))

        self.expected_fifth=QLabel()
        self.expected_fifth.setText("Target: %f" %self.i[4])
        self.expected_fifth.setStyleSheet("color:maroon")
        self.expected_fifth.setFont(QFont("Arial",Font_sizes))

        self.expected_sixth=QLabel()
        self.expected_sixth.setText("Target: %f" %self.i[5])
        self.expected_sixth.setStyleSheet("color:darkslateblue")
        self.expected_sixth.setFont(QFont("Arial",Font_sizes))

        self.expected_seventh=QLabel()
        self.expected_seventh.setText("Target: %f" %self.i[6])
        self.expected_seventh.setStyleSheet("color:darkgoldenrod")
        self.expected_seventh.setFont(QFont("Arial",Font_sizes))

        self.expected_eighth=QLabel()
        self.expected_eighth.setText("Target: %f" %self.i[7])
        self.expected_eighth.setStyleSheet("color:orange")
        self.expected_eighth.setFont(QFont("Arial",Font_sizes))


        #Raw readings that we get from wavemeter
        self.first_reading=QLabel()
        self.first_reading.setText("1st Laser(GHz): %f" %self.i_actual[0])
        self.first_reading.setGeometry(100,20,40,40)
        self.first_reading.setStyleSheet("color:red")
        self.first_reading.setFont(QFont("Arial",Font_sizes))

        self.second_reading=QLabel()
        self.second_reading.setText("2nd Laser(GHz): %f"%self.i_actual[1])
        self.second_reading.setStyleSheet("color:Blue")
        self.second_reading.setFont(QFont("Arial",Font_sizes))


        self.third_reading=QLabel()
        self.third_reading.setText("3rd Laser(GHz): %f" %self.i_actual[2])
        self.third_reading.setStyleSheet("color:purple")
        self.third_reading.setFont(QFont("Arial",Font_sizes))

        self.fourth_reading=QLabel()
        self.fourth_reading.setText("4th Laser(GHz): %f" %self.i_actual[3])
        self.fourth_reading.setStyleSheet("color:green")
        self.fourth_reading.setFont(QFont("Arial",Font_sizes))


        self.fifth_reading=QLabel()
        self.fifth_reading.setText("5th Laser(GHz): %f" %self.i_actual[4])
        self.fifth_reading.setStyleSheet("color:maroon")
        self.fifth_reading.setFont(QFont("Arial",Font_sizes))

        self.sixth_reading=QLabel()
        self.sixth_reading.setText("6th Laser(GHz): %f" %self.i_actual[5])
        self.sixth_reading.setStyleSheet("color:darkslateblue")
        self.sixth_reading.setFont(QFont("Arial",Font_sizes))

        self.seventh_reading=QLabel()
        self.seventh_reading.setText("7th Laser(GHz): %f" %self.i_actual[6])
        self.seventh_reading.setStyleSheet("color:darkgoldenrod")
        self.seventh_reading.setFont(QFont("Arial",Font_sizes))

        self.eighth_reading=QLabel()
        self.eighth_reading.setText("8th Laser(GHz): %f" %self.i_actual[7])
        self.eighth_reading.setStyleSheet("color:orange")
        self.eighth_reading.setFont(QFont("Arial",Font_sizes))
        
        #windows to add saturations
        
        self.first_sat=QLabel()
        self.first_sat.setText("Saturation: %f"%self.saturation_levels[0])
        self.first_sat.setStyleSheet("color:red")
        self.first_sat.setFont(QFont("Arial",Font_sizes))
        
        self.second_sat=QLabel()
        self.second_sat.setText("Saturation: %f"%self.saturation_levels[1])
        self.second_sat.setStyleSheet("color:Blue")
        self.second_sat.setFont(QFont("Arial",Font_sizes))
        
        self.third_sat=QLabel()
        self.third_sat.setText("Saturation: %f"%self.saturation_levels[2])
        self.third_sat.setStyleSheet("color:purple")
        self.third_sat.setFont(QFont("Arial",Font_sizes))
        
        self.fourth_sat=QLabel()
        self.fourth_sat.setText("Saturation: %f"%self.saturation_levels[3])
        self.fourth_sat.setStyleSheet("color:green")
        self.fourth_sat.setFont(QFont("Arial",Font_sizes))
        
        self.fifth_sat=QLabel()
        self.fifth_sat.setText("Saturation: %f"%self.saturation_levels[4])
        self.fifth_sat.setStyleSheet("color:maroon")
        self.fifth_sat.setFont(QFont("Arial",Font_sizes))
        
        self.sixth_sat=QLabel()
        self.sixth_sat.setText("Saturation: %f"%self.saturation_levels[5])
        self.sixth_sat.setStyleSheet("color:darkslateblue")
        self.sixth_sat.setFont(QFont("Arial",Font_sizes))
        
        self.seventh_sat=QLabel()
        self.seventh_sat.setText("Saturation: %f"%self.saturation_levels[6])
        self.seventh_sat.setStyleSheet("color:darkgoldenrod")
        self.seventh_sat.setFont(QFont("Arial",Font_sizes))
        
        self.eighth_sat=QLabel()
        self.eighth_sat.setText("Saturation: %f"%self.saturation_levels[7])
        self.eighth_sat.setStyleSheet("color:orange")
        self.eighth_sat.setFont(QFont("Arial",Font_sizes))
        


 #displaying widgets onto main screen
        mainlayout.addWidget(self.expected_first,0,0)
        mainlayout.addWidget(self.first_reading,0,1)
        mainlayout.addWidget(self.first_sat,0,2)

        mainlayout.addWidget(self.expected_second,1,0)
        mainlayout.addWidget(self.second_reading,1,1)
        mainlayout.addWidget(self.second_sat,1,2)

        mainlayout.addWidget(self.expected_third,2,0)
        mainlayout.addWidget(self.third_reading,2,1)
        mainlayout.addWidget(self.third_sat,2,2)

        mainlayout.addWidget(self.expected_fourth,3,0)
        mainlayout.addWidget(self.fourth_reading,3,1)
        mainlayout.addWidget(self.fourth_sat,3,2)
        
        mainlayout.addWidget(self.expected_fifth,4,0)
        mainlayout.addWidget(self.fifth_reading,4,1)
        mainlayout.addWidget(self.fifth_sat,4,2)

        mainlayout.addWidget(self.expected_sixth,5,0)
        mainlayout.addWidget(self.sixth_reading,5,1)
        mainlayout.addWidget(self.sixth_sat,5,2)

        mainlayout.addWidget(self.expected_seventh,6,0)
        mainlayout.addWidget(self.seventh_reading,6,1)
        mainlayout.addWidget(self.seventh_sat, 6, 2)

        mainlayout.addWidget(self.expected_eighth,7,0)
        mainlayout.addWidget(self.eighth_reading,7,1)
        mainlayout.addWidget(self.eighth_sat,7,2)

       # mainlayout.addWidget(self.close_application)
        self.setLayout(mainlayout)


    #how timing works: I'm setting two timers: qtimer1 and qtimer2. qtimer1 will loop every 5 miliseconds, generating the value,
    #and logging it into the data array. qtimer2 will run every 1 second, and display the current value of the reading into the window.
    #we need two timers such that one controls, the logging, and the other controls the staggered display.

          # make QTimers
        self.qTimer1= QTimer()
        #self.qTimer2= QTimer()
        #self.qTimer3= QTimer()
        #self.qTimer4= QTimer()
    # set intervals
        self.qTimer1.setInterval(2) # 16 milliseconds
        #self.qTimer2.setInterval(160)#1 secon
        #self.qTimer3.setInterval(1600) #1 second
        #self.qTimer4.setInterval(32000)#30 seconds
    # connect timeout signal to signal handlers

        self.qTimer1.timeout.connect(self.Main_function)
        #self.qTimer2.timeout.connect(self.displaySensorValue)
        #self.qTimer3.timeout.connect(self.logSensorValue)
        #self.qTimer4.timeout.connect(self.autoSave)

    # start timers
        self.qTimer1.start()
        #self.qTimer2.start()
        #self.qTimer3.start()
        #self.qTimer4.start()
    
    #Additional code by LBZ    
    def Main_function(self):
        global num_cycle
        num_cycle += 1
        # the original get sensor value code
        global device
        
        self.wavelength,self.saturation,__,self.time_step=device.get_measurement()
        self.frequency=0
        if self.wavelength <=100: 
            self.frequency = 0
            self.saturation = 0
        else:     
            self.frequency=self.speed_of_light/self.wavelength
        
        ### Run displaySensorValue
        
        for checking in range(8):
            self.difference=self.frequency-self.i[checking]
            if  0<= abs(self.difference) <self.threshold: 
                self.i_actual[checking]=self.frequency
                self.saturation_levels[checking]=self.saturation
                '''
                if checking==0:
                    self.first_reading.setText("Reading of 1st Laser(GHz): %f" %self.i_actual[0])
                    self.first_sat.setText("Saturation of 1st Laser: %f"%self.saturation_levels[0])
                elif checking==1:
                    self.second_reading.setText("Reading of 2nd Laser(GHz): %f" %self.i_actual[1])
                    self.second_sat.setText("Saturation of 2nd Laser: %f"%self.saturation_levels[1])
                elif checking==2:
                    self.third_reading.setText("Reading of 3rd Laser(GHz): %f" %self.i_actual[2])
                    self.third_sat.setText("Saturation of 3rd Laser: %f"%self.saturation_levels[2])
                elif checking==3:

                    self.fourth_reading.setText("Reading of 4th Laser(GHz): %f" %self.i_actual[3])
                    self.fourth_sat.setText("Saturation of 4th Laser: %f"%self.saturation_levels[3])
                elif checking==4: 
                    self.fifth_reading.setText("Reading of 5th Laser(GHz): %f" %self.i_actual[4])
                    self.fifth_sat.setText("Saturation of 5th Laser:%f"%self.saturation_levels[4])
                elif checking==5:
                    self.sixth_reading.setText("Reading of 6th Laser (GHz): %f" %self.i_actual[5])
                    self.sixth_sat_sat.setText("Saturation of 6th Laser:%f"%self.saturation_levels[5])
                elif checking==6: 
                    self.seventh_reading.setText("Reading of 7th Laser(GHz): %f" %self.i_actual[6])
                    self.seventh_sat_sat.setText("Saturation of 7th Laser:%f"%self.saturation_levels[6])
                else:
                    self.eighth_reading.setText("Reading of 8th Laser(GHz): %f" %self.i_actual[7])
                    self.eighth_sat.setText("Saturation of 8th Laser:%f"%self.saturation_levels[7])
                '''    
            else:
                pass
        #print(self.frequency, self.saturation)
        
        ## display the values
        if num_cycle%160 == 0:
            self.first_reading.setText("1st Laser(GHz): %f" %self.i_actual[0])
            self.first_sat.setText("Saturation: %f"%self.saturation_levels[0])
            self.second_reading.setText("2nd Laser(GHz): %f" %self.i_actual[1])
            self.second_sat.setText("Saturation: %f"%self.saturation_levels[1])
            self.third_reading.setText("3rd Laser(GHz): %f" %self.i_actual[2])
            self.third_sat.setText("Saturation: %f"%self.saturation_levels[2])
            self.fourth_reading.setText("4th Laser(GHz): %f" %self.i_actual[3])
            self.fourth_sat.setText("Saturation: %f"%self.saturation_levels[3])
            self.fifth_reading.setText("5th Laser(GHz): %f" %self.i_actual[4])
            self.fifth_sat.setText("Saturation:%f"%self.saturation_levels[4])
            self.sixth_reading.setText("6th Laser (GHz): %f" %self.i_actual[5])
            self.sixth_sat.setText("Saturation:%f"%self.saturation_levels[5])
            self.seventh_reading.setText("7th Laser(GHz): %f" %self.i_actual[6])
            self.seventh_sat.setText("Saturation:%f"%self.saturation_levels[6])
            self.eighth_reading.setText("8th Laser(GHz): %f" %self.i_actual[7])
            self.eighth_sat.setText("Saturation:%f"%self.saturation_levels[7])
        ### Save data  
        if num_cycle%1600 == 0:
            self.i_actual_temp = []
            for ii in self.i_actual:
                self.i_actual_temp.append(ii)
            self.array_of_frequencies.append(self.i_actual_temp)
            self.array_of_timesteps.append(self.time_step)
            #print(self.array_of_frequencies)
        ## Autosave    
        if num_cycle%16000 == 0:
            saving_data_set(self.array_of_timesteps,self.array_of_frequencies,self.file_name)
            self.i_actual = [0,0,0,0,0,0,0,0]
    


    #how this sensor will work is that it will give one input of of whatever laser is activated. So we have to make a way to discern which laser is displayed, 
    # and then correctly associate it. For now, lets say each of the level is in increments of 10. Loop through the values that we should, expect, and store them in an array
    # Make a loop that go throughs each of the values, if the difference between the found reading, and whatever target value is between 0 and 9 (ex: to get 70s we only 
    # want 70-79, display that with the correct value)
    '''
    def getSensorValue(self):
        global device
        
        self.wavelength,self.saturation,__,self.time_step=device.get_measurement()
        self.frequency=0
        if self.wavelength <=100: 
            self.frequency = 0
            self.saturation = 0
        else:     
            self.frequency=self.speed_of_light/self.wavelength

    def displaySensorValue(self): 
        for checking in range(len(self.i)):
            self.difference=self.frequency-self.i[checking]
            if  0<= abs(self.difference) <self.threshold: 
                self.i_actual[checking]=self.frequency
                self.saturation_levels[checking]=self.saturation
                if checking==0:
                    self.first_reading.setText("Reading of 1st Laser(GHz): %f" %self.i_actual[0])
                    self.first_sat.setText("Saturation of 1st Laser: %f"%self.saturation_levels[0])
                elif checking==1:
                    self.second_reading.setText("Reading of 2nd Laser(GHz): %f" %self.i_actual[1])
                    self.second_sat.setText("Saturation of 2nd Laser: %f"%self.saturation_levels[1])
                elif checking==2:
                    self.third_reading.setText("Reading of 3rd Laser(GHz): %f" %self.i_actual[2])
                    self.third_sat.setText("Saturation of 3rd Laser: %f"%self.saturation_levels[2])
                elif checking==3:

                    self.fourth_reading.setText("Reading of 4th Laser(GHz): %f" %self.i_actual[3])
                    self.fourth_sat.setText("Saturation of 4th Laser: %f"%self.saturation_levels[3])
                elif checking==4: 
                    self.fifth_reading.setText("Reading of 5th Laser(GHz): %f" %self.i_actual[4])
                    self.fifth_sat.setText("Saturation of 5th Laser:%f"%self.saturation_levels[4])
                elif checking==5:
                    self.sixth_reading.setText("Reading of 6th Laser (GHz): %f" %self.i_actual[5])
                    self.sixth_sat_sat.setText("Saturation of 6th Laser:%f"%self.saturation_levels[5])
                elif checking==6: 
                    self.seventh_reading.setText("Reading of 7th Laser(GHz): %f" %self.i_actual[6])
                    self.seventh_sat_sat.setText("Saturation of 7th Laser:%f"%self.saturation_levels[6])
                else:
                    self.eighth_reading.setText("Reading of 8th Laser(GHz): %f" %self.i_actual[7])
                    self.eighth_sat.setText("Saturation of 8th Laser:%f"%self.saturation_levels[7])
                    
            else:
                pass

    def logSensorValue(self):
       ##    self.mini_array.append(self.random_value)
        
        self.array_of_frequencies.append(self.frequency)
        self.array_of_timesteps.append(self.time_step)
        #self.array_of_saturation.append(self.saturation)
       # print(self.array_of_frequencies)
        
        

       # print(self.frequency)
      #  print("Length of Final Array: "+str(len(self.array_of_frequencies)))

    def autoSave(self):
        saving_data_set(self.array_of_timesteps,self.array_of_frequencies,self.file_name)
    '''
    def closeEvent(self,event): 
        


        
        reply=QMessageBox.question(self,"Window Close","Are you sure you want to exit  ?",
        QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if reply==QMessageBox.Yes:
            saving_data_set(self.array_of_timesteps,self.array_of_frequencies,self.file_name)
            global device
            del device
            self.qTimer1.stop()
            #self.qTimer2.stop()
            #self.qTimer3.stop()
            #self.qTimer4.stop()
            
            
        else: 
            event.ignore()
            
            #Here we'll thread the application so that it only runs in the background
            




app=QApplication(sys.argv)

demo=Application()
demo.show()

sys.exit(app.exec())


