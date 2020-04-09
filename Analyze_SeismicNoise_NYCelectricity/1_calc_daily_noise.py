# %% markdown
# # Calculate Average Ground Displacement
# Seismic data retrieved from the IRIS DMC (https://ds.iris.edu/ds/nodes/dmc/)
# %% codecell
import matplotlib.pyplot as plt
import obspy
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import numpy as np
from datetime import datetime, timedelta
import calendar
import pandas as pd
% matplotlib inline
plt.rcParams.update({'font.size': 15})

# %% codecell
webservice = "IRIS" # Do not edit

# network = "CI" # LA
# station = "USC" # LA

# network = "LD" # LDEO
# station = "PAL" # LDEO

network = "LD" # Central Park
station = "CPNY" # Central Park

tstart = "2020-02-09T00:00:00" # Start time of range
tend = "2020-04-09T12:00:00" # End time of range
comp = "BHZ" # Component to download
fmin = 5 # [Hz] minimum frequency
fmax = 15 # [Hz] maximum frequency
winlen_hr = 3  # [hr] Length of windows

# %% codecell
# LOAD CLIENT
client = Client(webservice)
print(client)

# %% codecell
# LOAD STATIONS
t1 = UTCDateTime(tstart)
t2 = UTCDateTime(tend)
inventory = client.get_stations(network=network, station=station, channel=comp, starttime=t1, endtime=t2)
inventory.plot(projection="local",label=False)
fig = inventory.plot(method="basemap", show=True) 
# %% codecell
winlen_s = winlen_hr*60*60
tvec = np.arange(tstart,tend,winlen_s,dtype='datetime64[s]').astype('O')
t_cent = tvec[0:-1]+timedelta(0,winlen_s/2)
disp_avg = np.zeros(t_cent.shape)

# Loop through time segements and find average amplitude of filtered envelope
for iday, t in enumerate(t_cent): 
    st = client.get_waveforms(network=network, station=station, location="*", channel=comp, starttime=UTCDateTime(tvec[iday]), endtime=UTCDateTime(tvec[iday+1]), attach_response=True)
    sr = st[0].stats.sampling_rate
    # Remove instrument response
    st.remove_response(output="DISP", zero_mean=True, taper=True, taper_fraction=0.05, pre_filt=[0.001, 0.005, sr/3, sr/2], water_level=60)
    st.detrend(type='demean')
    st.detrend(type='linear')
    st.taper(type="cosine",max_percentage=0.05)
    # Filter
    st.filter('bandpass', freqmin=fmin, freqmax=fmax, corners=2, zerophase=True)
    # Envelope of filtered data
    data_env = obspy.signal.filter.envelope(st[0].data)
    disp_avg[iday] = np.median(data_env)

# %% Save to text file
df = pd.DataFrame({'t_cent': t_cent,
                   'disp_avg': disp_avg})
filename = 'Data/'+network+'.'+station+'.'+str(t1)[0:10]+'.'+str(t2)[0:10]+'.'+str(fmin)+'_'+str(fmax)+'Hz'+'.'+comp+'.csv'
df.to_csv(filename,index=False)

# %% Plot daily average displacements
fig = plt.figure(figsize=(15,10))
plt.plot(df.t_cent,df.disp_avg*1e9,'-',linewidth=2)
plt.ylabel('Displacement [nm]')
plt.setp(plt.gca().get_xticklabels(), rotation=45)

