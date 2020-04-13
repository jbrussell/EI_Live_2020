# %% markdown
# # Plot Average Daily Ground Motion
# %% codecell
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
% matplotlib inline
plt.rcParams.update({'font.size': 18})

# Set x-axis limits for plotting
# datetime(YEAR, MONTH, DAY)
tmin = datetime(2020, 2, 7)
tmax = datetime(2020, 4, 10)

# %% Plots!
# fname = 'Data/CI.USC.2020-02-09.2020-04-08.1_19Hz.BHZ.csv'
fname = 'Data/LD.CPNY.2020-02-09.2020-04-09.5_15Hz.BHZ.csv'
# fname = 'Data/LD.PAL.2020-02-09.2020-04-08.5_15Hz.BHZ.csv'
# fname = 'Data/'+network+'.'+station+'.'+str(t1)[0:10]+'.'+str(t2)[0:10]+'.'+str(fmin)+'_'+str(fmax)+'Hz'+'.'+comp+'.csv'
df = pd.read_csv(fname,parse_dates=['t_cent'])

# NYC stay at home 2020/3/22 8pm EST (UTC - 4)
nyc_SAH = datetime(2020,3,22,20,0) + timedelta(0,4*60*60)

fig = plt.figure(figsize=(15,10))
plt.plot(df.t_cent,df.disp_avg*1e9,'-',linewidth=2.5,label='Hourly')

# Calculate daily averages using boxcar window
dt_hr = (df.t_cent[1]-df.t_cent[0]).seconds/60/60  # Hours between samples
daily_average = df.disp_avg.rolling(int(24/dt_hr),win_type='boxcar').mean()*1e9
plt.plot(df.t_cent,daily_average,'-',linewidth=4,color='tab:red',label='Daily')

# plt.plot([nyc_SAH, nyc_SAH],[0, 2],'--r')
plt.ylabel('Average Ground Displacement (nm)',fontsize=23)
plt.xlabel('Date',fontsize=23)
# plt.title('Central Park LD.CPNY.BHZ (5-15 Hz)')
# plt.grid(True)
plt.xlim([tmin, tmax])
plt.tick_params('both', length=10, which='major')
plt.legend()

# Rotate tick marks on x-axis
plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

plt.tight_layout()
plt.show()
fig.savefig('CPNY.5_15Hz.pdf')

