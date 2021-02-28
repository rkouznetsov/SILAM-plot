#!/usr/bin/env python3

import csv

inf="SILAM_points.csv"
outf="labels.gs"

with open(inf, 'rt') as csvfile:
    csvreader = csv.reader(csvfile)
    head=next(csvreader)
    with open(outf,"wt") as gsfile:
        gsfile.write("function labels (args)\n")
        gsfile.write("'set line 1'\n")
        for row in csvreader:
            [label,lat,lon] = row[:3]
            if label.endswith("'"):
                label=label[:-1]

            gsfile.write("'q w2xy %s %s'\n"%(lon,lat))
            gsfile.write("xpos1=subwrd(result,3)\n")
            gsfile.write("ypos1=subwrd(result,6)\n")

            if label == "Eslamshahr":
               gsfile.write("'set string 1 tl'\n")
               gsfile.write("'draw string 'xpos1+0.05' 'ypos1' %s'\n"%(label))
            elif label == "Karaj":
               gsfile.write("'set string 1 br'\n")
               gsfile.write("'draw string 'xpos1-0.05' 'ypos1' %s'\n"%(label))
            else:
               gsfile.write("'set string 1 bl'\n")
               gsfile.write("'draw string 'xpos1' 'ypos1' .%s'\n"%(label))

            gsfile.write("'draw mark 2 'xpos1' 'ypos1' 0.05'\n")


