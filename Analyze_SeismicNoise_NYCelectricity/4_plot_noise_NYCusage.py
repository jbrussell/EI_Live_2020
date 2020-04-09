# %% markdown
# ## Plot ground displacement measured in Central Park with N.Y.C. Electricity consumption
# %% codecell
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
% matplotlib inline
plt.rcParams.update({'font.size': 18})

# %%
# Set x-axis limits for plotting
# datetime(YEAR, MONTH, DAY)
tmin = datetime(2020, 2, 7)
tmax = datetime(2020, 4, 10)

# Load seismic data
# fname = 'Data/CI.USC.2020-02-09.2020-04-08.1_19Hz.BHZ.csv'
fname = 'Data/LD.CPNY.2020-02-09.2020-04-09.5_15Hz.BHZ.csv'
# fname = 'Data/LD.PAL.2020-02-09.2020-04-08.5_15Hz.BHZ.csv'
# fname = 'Data/'+network+'.'+station+'.'+str(t1)[0:10]+'.'+str(t2)[0:10]+'.'+str(fmin)+'_'+str(fmax)+'Hz'+'.'+comp+'.csv'
df_noise = pd.read_csv(fname,parse_dates=['t_cent'])

# Load N.Y.C. electricity data
fname = 'Data/load_reduction_hourly_NYC.csv'
df_load = pd.read_csv(fname,parse_dates=['Date'])

# NYC stay at home 2020/3/22 8pm EST (UTC - 4)
nyc_SAH = datetime(2020,3,22,20,0) + timedelta(0,4*60*60)

# NYC First COVID-19 death 2020/3/14 EST (UTC - 4)
nyc_1st = datetime(2020,3,14,0,0)

# %%
# Plot
fig, ax1 = plt.subplots(figsize=(15,10))
color = 'tab:blue'
ax1.plot(df_noise.t_cent,df_noise.disp_avg*1e9,'-',linewidth=2,color=color)
# ax1.plot(df_noise.t_cent,df_noise.disp_avg.rolling(8*7,win_type='boxcar').mean()*1e9,'-',linewidth=2,color='black')
ax1.plot([nyc_SAH, nyc_SAH],[0, 2.1],'--k',linewidth=3)
ax1.text(nyc_SAH+timedelta(4.5),0.1,'Stay at \nhome order',fontsize=18,horizontalalignment='center')
ax1.plot([nyc_1st, nyc_1st],[0, 2.1],'--',linewidth=3,color='gray')
ax1.text(nyc_1st-timedelta(3.5),0.1,'First NYC \nfatality',color='gray',fontsize=18,horizontalalignment='center')
ax1.set_ylabel('Average Ground Displacement (nm) 5-15 Hz',fontsize=23,color=color)
ax1.set_xlabel('Date',fontsize=23)
ax1.set_xlim([tmin, tmax])
ax1.set_ylim(0,2.1)
ax1.tick_params(axis='y', labelcolor=color)
# ax1.grid(True)
ax1.set_title('Seismic Noise in Central Park and N.Y.C. Electricity Consumption',fontsize=25)
ax1.tick_params('both', length=10, which='major')

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
color = 'tab:red'
ax2.plot(df_load.Date,df_load.load_resid,'-',linewidth=2,color=color)
# ax2.plot(df_load.Date,df_load.load_resid.rolling(24*7,win_type='boxcar').mean(),'-',linewidth=2,color=color)
ax2.plot()
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylabel('Electricity Use Relative to Previous 4 Years (%)',fontsize=23,color=color)
ax2.set_ylim(-40,15)
ax2.tick_params('both', length=10, which='major')

# Rotate tick marks on x-axis
plt.setp(ax1.get_xticklabels(), rotation=45, horizontalalignment='right')

plt.tight_layout()
plt.show()
fig.savefig('CPNY.5_15Hz.NYCelectricityanomaly.pdf')

