#!/bin/bash
set -u -e

# put logo if corresponding command is provided
#cd $scriptdir/delme || exit 234

#Acquire and polt

picture_dir=$OUTPUT_DIR/webloads/${fcdate}

python3 Plot_SILAM_forecast.py


nproc=`nproc`
if [  -z ${PUTLOGOCMD+x}  ]; then
   echo PUTLOGOCMD is not set
else
   echo Putting logos
   ls ${picture_dir}/*.png |grep -v AQI_ |grep -v POLI_| xargs  -I XXX -P 10 ${PUTLOGOCMD} XXX XXX  
   if [  -n ${PUTLOGOCMDINDEX+x}  ]; then
      #separate logo for AQI
      ls ${picture_dir}/*[AO][QL]I_???.png | xargs  -I XXX -P 10 ${PUTLOGOCMDINDEX} XXX XXX  
   fi
   echo compressing pics
   ls ${picture_dir}/*.png  | xargs  -I XXX -P $nproc convert XXX PNG8:XXX
fi
#echo waiting..
#wait



echo Done with logos!
[ -n "$outsuff" ] && exit 0 #No publish for modified runs


if $publish; then
    keepdays=7
    pushd $picture_dir/..
    for d in `find . -type d -name '20??????'|sort|head -n -$keepdays`; do
       echo removing $d
       rm -rf $d
    done
    ii=0
    for d in `find . -type d -name '20??????'|sort -r`; do
       linkname=`printf  %03d $ii`
       rm -f $linkname
       echo ln -s  $d $linkname
       ln -sf  $d $linkname
       ii=`expr $ii + 1`  
    done

    #deploy animation if not yet...
    rsync -av $scriptdir/www/*.html $scriptdir/www/logos .
    if [ !  -d Napit ]; then
     tar -xvf  $scriptdir/www/Napit.tar
    fi

    popd
    fmi_data_path=eslogin:/fmi/data/silam.fmi.fi/partners/$suitename
    echo Syncing $OUTPUT_DIR/webloads to $fmi_data_path
#    mkdir -p $fmi_data_path
    rsync -a --delete  $OUTPUT_DIR/webloads/* $fmi_data_path/
fi
exit 0

