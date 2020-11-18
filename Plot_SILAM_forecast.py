#!/usr/bin/env python3

import datetime as dt
import subprocess as subp
import atexit
import urllib.request, urllib.error, urllib.parse
import signal
import os
import sys

"""
# Pretend that the forecast starts at the fcdate
# Actual date of global forecast is globfcdate

"""

# Get environment
OUTPUT_DIR=os.getenv("OUTPUT_DIR",None)
fcdate=os.getenv("fcdate",None)
globfcdate=os.getenv("globfcdate",None)
maxhours=int(os.getenv("maxhours",None))
email=os.getenv("email",None)
lonrange=os.getenv("lonrange",None)
latrange=os.getenv("latrange",None)
domain=os.getenv("suitename",None)
#=os.getenv("",None)
#=os.getenv("",None)



#urlbase="https://silam.fmi.fi/thredds/ncss/grid/silam_glob_v5_7_1/runs/silam_glob_v5_7_1_RUN_"
urlbase=os.getenv("urlpref",None)
lons=lonrange.split(',')
lats=latrange.split(',')
bbox="spatial=bb&north=%s&west=%s&east=%s&south=%s"%(lats[1],lons[0],lons[1],lats[0]);
# list of variables and levels according to MKD AQ index
varlist="cnc_PM2_5 cnc_PM10 cnc_O3_gas cnc_NO2_gas cnc_SO2_gas cnc_CO_gas".split() 
#varlist="cnc_PM2_5".split() 
lev_nam_col=dict(
          cnc_PM2_5=("1 2 5 10 20 50 100 200 500",             "PM2_5",  'def_lowwhite'), 
          cnc_PM10=("3 6 15 30 60 150 300 600 1500 3000",                      "PM10",  'def_lowwhite'), 
          cnc_O3_gas=("10 20 40 60 80 100 120 140 160 180 200",                "O3", 'def_lowwhite'),
          cnc_NO2_gas=(".1 .2 .5 1 2 5 10 20 50 100",               "NO2", "def_lowblue"),
          cnc_SO2_gas=(".1 .2 .5 1 2 5 10 20 50 100",                "SO2", "def_lowblue"),
          cnc_CO_gas=("15 25 40 70 150 250 400 700 1500 2500",  "CO", 'def_lowwhite'),
          BLH = ("10 20 40 80 150 250 400 700 1500 2500",  "BLH", 'def_lowgrey'),
          )

# area to be plotted: Macedonian domain
#bbox="spatial=bb&north=43.5&west=19&east=24.5&south=40"
# descriptor of the user requesting the data, mail of the contact person in case someone changes on FMI side
requestmark="email="+email
# dates for the request 
one_hour=dt.timedelta(hours=1)
basedate=dt.datetime.strptime(globfcdate,"%Y%m%d")
tstart=dt.datetime.strptime(fcdate,"%Y%m%d")
tend=tstart + dt.timedelta(hours=maxhours)
runTstr =basedate.strftime("%FT00:00:00Z")
startTstr=tstart.strftime("%FT00:00:00Z")
endTstr=tend.strftime("%FT%H:%M:%SZ")
# request the data
URL="%s%s?var=%s&temporal=range&time_start=%s&time_end=%s&%s&vertCoord=12&accept=netcdf&%s"%(urlbase,runTstr,",".join(varlist),startTstr,endTstr,bbox,requestmark)

#print(URL)
#
# Create directory to where the pictures should be stored for publishing
#
tstr=tstart.strftime("%Y%m%d")
picdir=OUTPUT_DIR+"/webloads/%s/"%(fcdate)
ncdir=OUTPUT_DIR+"/%s/"%(fcdate)
try:
    os.makedirs(picdir)
    print("Creating directory for today's pictures "+picdir)
except OSError:
    if not os.path.isdir(picdir):
        raise
try:
    os.makedirs(ncdir)
    print("Creating directory for today's netcdf files "+ncdir)
except OSError:
    if not os.path.isdir(ncdir):
        raise

def killchild(child):
    try:
        child.kill()
    except:
        pass

#
# Check if the data is available at the THREAD server at FMI
#
print ("Checking if NetCDF files are available at FMI")

ncfile=ncdir+"/SILAM4%s-%s.nc"%(domain,tstart.strftime("%Y%m%d"))

if os.path.exists(ncfile):
    print("Already exists: "+ ncfile)
else:
    print("Getting "+ ncfile)

    for  attempts in range(3):

        try:
            response = urllib.request.urlopen(URL) #, timeout = 600)
            with open( ncfile+'tmp', 'wb' ) as f:
                f.write( response.read() )
            os.rename(ncfile+'tmp',ncfile)
            print(ncfile + " created!")
            
            break
        except urllib.error.URLError as e:
            attempts += 1
            print("Download attampt %d failes"%(attempts))
            print(type(e))

    if attempts > 2:
        print ("Failed to get the data")
        sys.exit(255)

#
# Plot the results with GrADs
# 
print('Creating pictures at '+picdir)

#Taken from the v5_4 script (It Works!)
gradsbin=os.getenv("gradsnc", "/usr/bin/grads")
gradsp=subp.Popen((gradsbin+" -b  -l").split(), shell=False, bufsize=100000, stdin=subp.PIPE, stdout=subp.PIPE)

grads_scr="""
set gxout shaded
set mpdset mpd_irantaj
## draw shoreline
set mpt 1 1 1 1
* grid off
set mpt 2 off
** Inland borders thick dark green
*   'set rgb  250  0  50  0'
*   'set mpt 3 15 1 2'
*   'set mpt 3 250 1 2'
* Thin short dash
 set mpt 3 1 1 1
* rivers -- blue 
* set rgb  251  200  200  255
* set mpt 4 4 1 0.1

set mproj scaled
*set xlab off
*set ylab off
*set frame off
*set rbcols 11 5 13 10 3 7 8 9
*set parea 0 11 0 8.5
sdfopen %(ncfile)s
"""%dict(ncfile=ncfile)
for v in varlist:
  #print(t)
  clev,snam2,colors = lev_nam_col[v]
  grads_scr += "run colors.gs %s\n"%(colors,)
  for it in range((tend-tstart).days*24 + 1):
     plottime = tstart + dt.timedelta(hours=it)
     gradstime=plottime.strftime("%H:%MZ%d%b%Y")
     date=plottime.strftime("%d%b%Y")
     hour=plottime.strftime("%H")
     outname=picdir+snam2+"_surf_%03d.png"%(it,)
     #print(outname)
     grads_scr += """
                set time %(t)s
                set clevs %(levs)s
                set grads off
                d  %(v)s
                labels_%(domain)s
                cbarn
                draw title %(vS)s concentration (ug/m3), %(date)s hour: %(hour)s 
                printim %(outname)s x800 y600 white
                clear
              """%dict(t=gradstime, v=v, vS=snam2, date=date , hour=hour, outname=outname, levs=clev, domain=domain)
grads_scr += 'quit\r\n'


#with open("tmp.grads_in","w") as f:
#    f.write(grads_scr)

#os.unlink(ncfile)


gradsout,gradserr = gradsp.communicate(grads_scr.encode('utf-8'))
print(gradserr)
#os.unlink(ncfile)

if  os.path.isfile(outname):
#if  os.path.exists(outname):
    print ("pictures created in %s"%(picdir))
else:
    print ("grads failed!")
    os.system('rm -r '+picdir+' '+ncdir)
    raise IOError("grads failed!")  

