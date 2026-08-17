# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 09:57:54 2021

@author: Krb-Logging
"""
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QLabel, QVBoxLayout,QHBoxLayout
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from bristol_RS422 import BristolRS422
from Read_Data import *

global portnumber 
portnumber="COM10"
global device


global weights
global targets
global threshold

device=BristolRS422(portnumber)
weights=[0]
targets=[0]
threshold=1
def collectData():
    data=device.get_measurement()
    
    print(data)
    for i in range(len(targets)):
        if abs(data[0]-targets[i])<=threshold:
            weights[i]+=1
            break
        else:
            targets.append(data[0])
            weights.append(1)
    print(weights)
    print(targets)