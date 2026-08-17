#the goal of this code will be that we are given a list of data, hopefully from the wavemeter. We will get a matrix of information
#the first row will be the times recorded, second will be the wavemeter values, third will be pressure, fourth will be temperature 


import numpy as np
from numpy import asarray
from numpy import savetxt 


global frequency_of_machine
frequency_of_machine= 500


def saving_data_set(time,wave_val,name): 
    time_part=asarray(time,"f")
    #set first time reading to be zero,what we could do is just record the input of the first reading, and subtract it from the 
    #others, then convert the frequency to actual times that it occured
    start_time=time_part[0]
    for spot in range (len(time_part)):
        time_part[spot]=time_part[spot]-start_time        
        time_part[spot]=time_part[spot]/frequency_of_machine    
    wavemeter=asarray(wave_val,dtype=np.float64) ### Frequencies need higher precision than float32
    #this is the matrix we are going to store
    information=np.c_[time_part,wavemeter]
    #print(wavemeter)
    #convert the matrix to .csv
    savetxt(name+".csv",information,delimiter=",")
    print("File Saved As:"+name)    
    
#def load_data_set(filename):
    #reading out the sheets#
 #   global final_readings
  #  final_readings=pk.load(open(filename,"rb"))
    #global temperatures 
   # temperatures=final_readings[3]

def save_data_array(saved_array,filename):
    final_array=saved_array
    final_file=asarray(final_array,"f")
    savetxt(filename+'.csv',final_file,delimiter=",")
    print("File Saved As: "+ filename)
    



