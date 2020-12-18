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
varlistsfc="BLH AQI AQISRC".split()
#varlist="cnc_CO_gas".split() 
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

def getNC(URL, ncfile):
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
                print(e)
                print(type(e))

        if attempts > 2:
            print ("Failed to get the data")
            sys.exit(255)

#
# Plot the results with GrADs
# 
gradsscripthead="""
    set gxout shaded
    set mpdset mpd_taj
    set mpt 1 1 1 1
    set mpt 2 off
    set mpt 3 1 1 1
    set mproj scaled
"""
#   set mpt 1 1 1 1
#   * grid off
#   set mpt 2 off
#   ** Inland borders thick dark green
#   *   'set rgb  250  0  50  0'
#   *   'set mpt 3 15 1 2'
#   *   'set mpt 3 250 1 2'
#   * Thin short dash
#    set mpt 3 1 1 1
#   * rivers -- blue 
#   * set rgb  251  200  200  255
#   * set mpt 4 4 1 0.1

def PlotCNC(ncfile, v, outtempl, tstart, tend):

    gradsbin=os.getenv("gradsnc", "/usr/bin/grads")
    gradsp=subp.Popen((gradsbin+" -b  -l").split(), shell=False, bufsize=100000, stdin=subp.PIPE, stdout=subp.PIPE)
    grads_scr = gradsscripthead
    grads_scr += """
    sdfopen %(ncfile)s
    """%dict(ncfile=ncfile)

    clev,snam2,colors = lev_nam_col[v]
    grads_scr += "run colors.gs %s\n"%(colors,)
    if v.startswith("cnc_"):
        title="%s concentration (ug/m3)"%(snam2)
    elif v == 'BLH':
        title="ABL heoght (m)"

    for it in range((tend-tstart).days*24 + 1):
       plottime = tstart + dt.timedelta(hours=it)
       gradstime=plottime.strftime("%H:%MZ%d%b%Y")
       date=plottime.strftime("%d%b%Y")
       hour=plottime.strftime("%H")
       outname = outtempl%(it,)
       #print(outname)

       grads_scr += """
              set time %(t)s
              set clevs %(levs)s
              set grads off
              d  %(v)s
              labels
              cbarn
              draw title %(title)s, %(date)s hour: %(hour)sZ 
              printim %(outname)s x800 y600 white
              clear
            """%dict(t=gradstime, v=v, title=title, date=date , hour=hour, outname=outname, levs=clev)
    grads_scr += 'quit\r\n'

    gradsout,gradserr = gradsp.communicate(grads_scr.encode('utf-8'))
    print(gradserr)
    #os.unlink(ncfile)

    if  os.path.isfile(outname):
    #if  os.path.exists(outname):
        print ("pictures for %s created in %s"%(v, picdir))
    else:
        print ("grads failed!")
        os.system('rm -r '+picdir+' '+ncdir)
        raise IOError("grads failed!")  
    
def PlotAQI(ncfile, outtempl, tstart, tend):
      ## Two-pannel AQI and AQISRC

    gradsbin=os.getenv("gradsnc", "/usr/bin/grads")
    gradsp=subp.Popen((gradsbin+" -b  -p").split(), shell=False, bufsize=100000, stdin=subp.PIPE, stdout=subp.PIPE)

    grads_scr = gradsscripthead
    grads_scr += """
        set gxout grfill
        set rgb 29 40 130 240
        set rgb 30 102 229 102
        set rgb 31 255 240 85
        set rgb 32 255 187 87
        set rgb 33 255 68 68
        set rgb 34 182 70 139
        set rgb 40 200 200 200
        set rgb 41 100 100 100

        sdfopen %(ncfile)s
    """%dict(ncfile=ncfile)

    for it in range((tend-tstart).days*24 + 1):
         plottime = tstart + dt.timedelta(hours=it)
         gradstime=plottime.strftime("%H:%MZ%d%b%Y")
         date=plottime.strftime("%d%b%Y")
         hour=plottime.strftime("%H")
         outname = outtempl%(it,)
         #print(outname)

         grads_scr += """
              set time %(t)s
                    set vpage 0.25 8.25 5.25 10.75
                    set grads off
                    set clevs  1.5 2.5 3.5 4.5
                    set rbcols 30 31 32 33 34
                    d AQI
                    draw title AQI, %(date)s hour: %(hour)sZ
                    labels
                    ccbar Good Fair Moderate Poor VeryPoor

                    set vpage 0.25 8.25 0 5.5
                    set grads off
                    set clevs 1.5 2.5 3.5 4.5
                    set rbcols 40 41  3  4  12
                    d AQISRC
                    draw title Component responsible for poor AQ
                    ccbar PM2.5 PM10 NO2 O3 SO2

                    printim %(outname)s x800 y1100 white
                    clear
                  """%dict(t=gradstime, date=date , hour=hour, outname=outname, levs=clev)
    grads_scr += 'quit\r\n'



    gradsout,gradserr = gradsp.communicate(grads_scr.encode('utf-8'))
    #print(gradserr)
    #print(gradsout.decode("utf-8"))
    #os.unlink(ncfile)

    if  os.path.isfile(outname):
    #if  os.path.exists(outname):
        print ("pictures for AQI created in %s"%(picdir))
    else:
        print ("grads failed!")
        os.system('rm -r '+picdir+' '+ncdir)
        raise IOError("grads failed!")  


print ("Checking if NetCDF files are available at FMI")

#
# NetCDF subset ca't get a level and a sub-level
#

ncfile=ncdir+"/SILAM4%s-%s.nc"%(domain,tstart.strftime("%Y%m%d"))
URL="%s%s?var=%s&temporal=range&time_start=%s&time_end=%s&%s&vertCoord=12&accept=netcdf&%s"%(urlbase,runTstr,",".join(varlist),startTstr,endTstr,bbox,requestmark)
getNC(URL, ncfile)

ncfileAQI=ncdir+"/SILAM4%s-%s-AQI.nc"%(domain,tstart.strftime("%Y%m%d"))
URL="%s%s?var=%s&temporal=range&time_start=%s&time_end=%s&%s&accept=netcdf&%s"%(urlbase,runTstr,"AQI,AQISRC,BLH",startTstr,endTstr,bbox,requestmark)
getNC(URL, ncfileAQI)

print('Creating pictures at '+picdir)
for v in varlist:
    clev,snam2,colors = lev_nam_col[v]
    outtempl = picdir+snam2+"_surf_%03d.png"
    PlotCNC(ncfile, v, outtempl, tstart, tend)

outtempl = picdir+"BLH_%03d.png"
PlotCNC(ncfileAQI, "BLH", outtempl, tstart, tend)

outtempl = picdir+"AQI_%03d.png"
PlotAQI(ncfileAQI,  outtempl, tstart, tend)

