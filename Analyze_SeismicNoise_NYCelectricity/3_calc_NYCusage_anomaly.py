# %% markdown
# # Calculate daily change in electricity consumption for NYC
# Data from 2016-2019 is used to subtract a baseline from the 2020 data. http://www.energyonline.com/Data/GenericData.aspx?DataId=13&NYISO___Hourly_Actual_Load
# %% codecell
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
% matplotlib inline
plt.rcParams.update({'font.size': 15})

# Set x-axis limits for plotting: datetime(YEAR, MONTH, DAY)
tmin = datetime(2020, 2, 7)
tmax = datetime(2020, 4, 10)

# %% (UNCOMMENT IF RUNNING FOR THE FIRST TIME)
# # Save NYC data file.
# fname = 'Data/20160101-20200409_NYISO_Hourly_Actual_Load.csv'
# df = pd.read_csv(fname,parse_dates=['Date'])
# df_NYC = df[df.Zone=='N.Y.C.']
# df_NYC.to_csv('20160101-20200409_NYISO_Hourly_Actual_Load_NYC.csv')

# %% 
# Load data into pandas DataFrame (load in megawatt hours)
fname = 'Data/20160101-20200409_NYISO_Hourly_Actual_Load_NYC.csv'
df = pd.read_csv(fname,parse_dates=['Date'])

# NYC stay at home 2020/3/22 8pm EST (UTC - 4)
nyc_SAH = datetime(2020,3,22,20,0) + timedelta(0,4*60*60)

# %% markdown
# ## Remove yearly trend
# Calculate hourly averages for years 2016-2019 and subtract from 2020 values.
# %%

# Reorganize dataframe by Date (month, day, hour) with columns in years
df = df.set_index('Date')
pv = pd.pivot_table(df, index=[df.index.month, df.index.day, df.index.hour], columns=[df.index.year], values=['Load_megawatthours'])
# pv

# Calculate hourly load averages excluding 2020
load_avg = pv.loc[1:4].Load_megawatthours.iloc[:,0:4].median(axis=1)
# Save 2020 load values
load_2020 = pv.loc[1:4].Load_megawatthours.iloc[:,4]
# Calculate percent change in load used
load_2020pct_trend_removed = (load_2020-load_avg)/load_avg*100
# Remake index with datetime values
d = load_2020pct_trend_removed
d.index = pd.to_datetime('2020-'+d.index.get_level_values(0).astype(str) + '-' +
                          d.index.get_level_values(1).astype(str) + '-' +
                          d.index.get_level_values(2).astype(str),
               format='%Y-%m-%d-%H')
# Convert series to dataframe
d = d.to_frame('load_resid')
d['load_avg'] = load_avg.values
# Set date column with index values
d['Date'] = d.index
df['Date'] = df.index

# %%
# Plot Data
fig, ax = plt.subplots(2, 1, figsize=(15,10), sharex=True)

ax[0].plot(df.Date,df.Load_megawatthours,'-',linewidth=2,label='2020')
ax[0].plot(d.Date,d.load_avg,'-',linewidth=2,label='2016-2019 avg.')
ax[0].plot([nyc_SAH, nyc_SAH],[3000, 7000],'--r')
ax[0].set_ylabel('Total Load (Mwh)',fontsize=23)
ax[0].grid(True)
ax[0].set_xlim([tmin, tmax])
ax[0].set_ylim(3000,7000)
ax[0].legend()
ax[0].set_title('N.Y.C. Electrity Use',fontsize=23)

ax[1].plot(d.Date,d.load_resid,'-',linewidth=2)
ax[1].plot([nyc_SAH, nyc_SAH],[-30, 10],'--r')
ax[1].set_ylabel('Change in Electricity Use',fontsize=23)
ax[1].set_xlabel('Date',fontsize=23)
ax[1].grid(True)
ax[1].set_xlim([tmin, tmax])
# Rotate tick marks on x-axis
plt.setp(ax[1].get_xticklabels(), rotation=45)

plt.show()

# %%
# Save hourly load averages to csv
d.to_csv('Data/load_reduction_hourly_NYC.csv', 
            columns=['Date','load_resid','load_avg'], index=False)
