import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
headers=['Timestamp', 'Channel 1 Frequency (GHz)', 'Channel 1 Saturation',
       'Channel 2 Frequency (GHz)', 'Channel 2 Saturation',
       'Channel 3 Frequency (GHz)', 'Channel 3 Saturation',
       'Channel 4 Frequency (GHz)', 'Channel 4 Saturation',
       'Channel 5 Frequency (GHz)', 'Channel 5 Saturation',
       'Channel 6 Frequency (GHz)', 'Channel 6 Saturation',
       'Channel 7 Frequency (GHz)', 'Channel 7 Saturation',
       'Channel 8 Frequency (GHz)', 'Channel 8 Saturation']
df = pd.read_csv('C:\Bristol\wm8Data30.csv',usecols=['Timestamp','Channel 6 Frequency (GHz)'],skiprows=lambda x: (x != 0) and x % 30)
df.replace(0,np.nan,inplace=True)
df['Timestamp']=df['Timestamp'].map(lambda x: datetime.strptime(str(x), '%Y-%m-%dT%H:%M:%S.%f'))
x=df['Timestamp']
y=df['Channel 6 Frequency (GHz)']
plt.plot(x,y)
plt.ylim([472155.17, 472160.22])