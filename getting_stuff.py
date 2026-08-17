# -*- coding: utf-8 -*-
"""
Created on Thu Aug 12 16:29:14 2021

@author: Krb-Logging
"""
import csv
import numpy as np
import matplotlib.pyplot as plt 


threshold=50
with open("Data Log 8.12.21.csv","r") as f: 
    data=list(csv.reader(f,delimiter=","))

values=[852,420]    
final_val=np.array(data)
speed_of_light=299792458 
expected_values=np.array(values)
chan1_times=[]
chan1_wave=[]
chan2_times=[]
chan2_wave=[]
#sort through data, same as in matlab

times,frequencies=final_val[:,0],final_val[:,1]

wavelengths=[]

for val in range(len(frequencies)):
    if float(frequencies[val])!=0:
        wavelengths.append(speed_of_light/float(frequencies[val]))
    else: 
        pass


for check in range(len(wavelengths)):
    for cross in range(len(expected_values)):
        y=abs(wavelengths[check]-expected_values[cross])
        print(y)
        if 0<y<threshold:
            if cross==0: 
                chan1_times.append(times[check])
                chan1_wave.append(wavelengths[check])
            elif cross==1:
                chan2_times.append(times[check])
                chan2_wave.append(wavelengths[check])
            
            
        else: 
            pass
print(chan1_times)
print(chan1_wave)

#plotting 
plt.subplot(2,1,1)
plt.plot(chan1_times,chan1_wave)

plt.subplot(2,1,2)
plt.plot(chan2_times,chan2_wave)
plt.show()
        