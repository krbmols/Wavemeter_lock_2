import sys 
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QWindow
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (QApplication,QWidget,QMessageBox,QFormLayout)
import numpy as np
import time 
import random
from Read_Data import *


class Application(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1920,1080)
        self.file_name="alpha"
        
        mainlayout= QGridLayout()
        #where we will save the arrays: array of information will be the long-term log, and mini_array will hold the 10000 cap. 
        #after 10,000 inputs into mini_array, append it onto the main array, reset it, then continue logging. 
        self.array_of_information=[]
        self.mini_array=[]

        #counter for moderating the size of self.mini_array
        self.array_checker=0
        
        self.i=[0,10,20,30,40,50,60,70] #array to store target values for lasers being used for testing: self.i[0] is the value regarding 
        #the first lasers, self.i[1] with second laser, etc.
        self.i_actual=[0,0,0,0,0,0,0,0]
        




        #adding the tab for all of our stuff
        #what we are doing here is just displaying all of the labels
        #actual expected reading
        self.expected_first=QLabel()
        self.expected_first.setText("Expected Reading From 1st Laser(GHz): %f" %self.i[0])
        self.expected_first.setStyleSheet("color:red")
        self.expected_first.setFont(QFont("Arial",24))

        self.expected_second=QLabel()
        self.expected_second.setText("Expected Reading From 2nd Laser(GHz): %f" %self.i[1])
        self.expected_second.setStyleSheet("color:Blue")
        self.expected_second.setFont(QFont("Arial",24))

        self.expected_third=QLabel()
        self.expected_third.setText("Expected Reading From 3rd Laser(GHz): %f" %self.i[2])
        self.expected_third.setStyleSheet("color:purple")
        self.expected_third.setFont(QFont("Arial",24))

        self.expected_fourth=QLabel()
        self.expected_fourth.setText("Expected Reading From 4th Laser(GHz): %f" %self.i[3])
        self.expected_fourth.setStyleSheet("color:green")
        self.expected_fourth.setFont(QFont("Arial",24))

        self.expected_fifth=QLabel()
        self.expected_fifth.setText("Expected Reading From 5th Laser(GHz): %f" %self.i[4])
        self.expected_fifth.setStyleSheet("color:maroon")
        self.expected_fifth.setFont(QFont("Arial",24))

        self.expected_sixth=QLabel()
        self.expected_sixth.setText("Expected Reading From 6th Laser(GHz): %f" %self.i[5])
        self.expected_sixth.setStyleSheet("color:darkslateblue")
        self.expected_sixth.setFont(QFont("Arial",24))

        self.expected_seventh=QLabel()
        self.expected_seventh.setText("Expected Reading From 7th Laser(GHz): %f" %self.i[6])
        self.expected_seventh.setStyleSheet("color:darkgoldenrod")
        self.expected_seventh.setFont(QFont("Arial",24))

        self.expected_eighth=QLabel()
        self.expected_eighth.setText("Expected Reading From 8th Laser(GHz): %f" %self.i[7])
        self.expected_eighth.setStyleSheet("color:orange")
        self.expected_eighth.setFont(QFont("Arial",24))


        #Raw readings that we get from wavemeter
        self.first_reading=QLabel()
        self.first_reading.setText("Reading of First Laser(GHz): %f" %self.i_actual[0])
        self.first_reading.setGeometry(100,20,40,40)
        self.first_reading.setStyleSheet("color:red")
        self.first_reading.setFont(QFont("Arial",24))

        self.second_reading=QLabel()
        self.second_reading.setText("Reading of Second Laser(GHz): %f"%self.i_actual[1])
        self.second_reading.setStyleSheet("color:Blue")
        self.second_reading.setFont(QFont("Arial",24))


        self.third_reading=QLabel()
        self.third_reading.setText("Reading of Third Laser(GHz): %f" %self.i_actual[2])
        self.third_reading.setStyleSheet("color:purple")
        self.third_reading.setFont(QFont("Arial",24))

        self.fourth_reading=QLabel()
        self.fourth_reading.setText("Reading of Fourth Laser(GHz): %f" %self.i_actual[3])
        self.fourth_reading.setStyleSheet("color:green")
        self.fourth_reading.setFont(QFont("Arial",24))


        self.fifth_reading=QLabel()
        self.fifth_reading.setText("Reading of Fifth Laser(GHz): %f" %self.i_actual[4])
        self.fifth_reading.setStyleSheet("color:maroon")
        self.fifth_reading.setFont(QFont("Arial",24))

        self.sixth_reading=QLabel()
        self.sixth_reading.setText("Reading of Sixth Laser(GHz): %f" %self.i_actual[5])
        self.sixth_reading.setStyleSheet("color:darkslateblue")
        self.sixth_reading.setFont(QFont("Arial",24))

        self.seventh_reading=QLabel()
        self.seventh_reading.setText("Reading of Seventh Laser(GHz): %f" %self.i_actual[6])
        self.seventh_reading.setStyleSheet("color:darkgoldenrod")
        self.seventh_reading.setFont(QFont("Arial",24))

        self.eighth_reading=QLabel()
        self.eighth_reading.setText("Reading of Eighth Laser(GHz): %f" %self.i_actual[7])
        self.eighth_reading.setStyleSheet("color:orange")
        self.eighth_reading.setFont(QFont("Arial",24))


 #displaying widgets onto main screen
        mainlayout.addWidget(self.expected_first,0,0)
        mainlayout.addWidget(self.first_reading,0,1)

        mainlayout.addWidget(self.expected_second,1,0)
        mainlayout.addWidget(self.second_reading,1,1)

        mainlayout.addWidget(self.expected_third,2,0)
        mainlayout.addWidget(self.third_reading,2,1)

        mainlayout.addWidget(self.expected_fourth,3,0)
        mainlayout.addWidget(self.fourth_reading,3,1)
        
        mainlayout.addWidget(self.expected_fifth,4,0)
        mainlayout.addWidget(self.fifth_reading,4,1)

        mainlayout.addWidget(self.expected_sixth,5,0)
        mainlayout.addWidget(self.sixth_reading,5,1)

        mainlayout.addWidget(self.expected_seventh,6,0)
        mainlayout.addWidget(self.seventh_reading,6,1)

        mainlayout.addWidget(self.expected_eighth,7,0)
        mainlayout.addWidget(self.eighth_reading,7,1)

       # mainlayout.addWidget(self.close_application)
        self.setLayout(mainlayout)


    #how timing works: I'm setting two timers: qtimer1 and qtimer2. qtimer1 will loop every 5 miliseconds, generating the value,
    #and logging it into the data array. qtimer2 will run every 1 second, and display the current value of the reading into the window.
    #we need two timers such that one controls, the logging, and the other controls the staggered display.

          # make QTimers
        self.qTimer1 = QTimer()
        self.qTimer2= QTimer()
        self.qTimer3=QTimer()
        self.qTimer4=QTimer()
        self.qTimer5=QTimer()
    # set intervals
        self.qTimer1.setInterval(1) # 1 milliseconds
        self.qTimer2.setInterval(200) #200 milliseconds 
        self.qTimer3.setInterval(1000) #1 second
        self.qTimer4.setInterval(30000)#1minute
    # connect timeout signal to signal handlers

        self.qTimer1.timeout.connect(self.getSensorValue)
        self.qTimer2.timeout.connect(self.displaySensorValue)
        self.qTimer3.timeout.connect(self.logSensorValue)
        self.qTimer4.timeout.connect(self.autoSave)

    # start timers
        self.qTimer1.start()
        self.qTimer2.start()
        self.qTimer3.start()
        self.qTimer4.start()
     

    

    


    #how this sensor will work is that it will give one input of of whatever laser is activated. So we have to make a way to discern which laser is displayed, 
    # and then correctly associate it. For now, lets say each of the level is in increments of 10. Loop through the values that we should, expect, and store them in an array
    # Make a loop that go throughs each of the values, if the difference between the found reading, and whatever target value is between 0 and 9 (ex: to get 70s we only 
    # want 70-79, display that with the correct value)
        #self.rand_variable=

    def getSensorValue(self):
        self.random_value=random.uniform(0,80)

    def displaySensorValue(self): 
        for checking in range(len(self.i)):
            self.difference=self.random_value-self.i[checking]
            if 0<=self.difference and self.difference <10: 
                self.i_actual[checking]=self.random_value
                if checking==0:
                    self.first_reading.setText("Reading of First Laser(GHz): %f" %self.i_actual[0])
                elif checking==1:
                    self.second_reading.setText("Reading of Second Laser(GHz): %f" %self.i_actual[1])
                elif checking==2:
                    self.third_reading.setText("Reading of Third Laser(GHz): %f" %self.i_actual[2])
                elif checking==3:
                    self.fourth_reading.setText("Reading of Fourth Laser(GHz): %f" %self.i_actual[3])
                elif checking==4: 
                    self.fifth_reading.setText("Reading of Fifth Laser(GHz): %f" %self.i_actual[4])
                elif checking==5:
                    self.sixth_reading.setText("Reading of Sixth Laser (GHz): %f" %self.i_actual[5])
                elif checking==6: 
                    self.seventh_reading.setText("Reading of Seventh Laser(GHz): %f" %self.i_actual[6])
                else:
                    self.eighth_reading.setText("Reading of Eighth Laser(GHz): %f" %self.i_actual[7])
            else:
                pass

    def logSensorValue(self):
       ##    self.mini_array.append(self.random_value)
        
        self.array_of_information.append(self.random_value)
        
        

        print(self.random_value)
        print("Length of Final Array: "+str(len(self.array_of_information)))

    def autoSave(self):
        save_data_array(self.array_of_information,self.file_name)

    def closeEvent(self,event): 
        reply=QMessageBox.question(self,"Window Close","Are you sure you want to exit  ?",
        QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if reply==QMessageBox.Yes:
            save_data_array(self.array_of_information,self.file_name)
            
        else: 
            event.ignore()




app=QApplication(sys.argv)

demo=Application()
demo.show()

sys.exit(app.exec())

