from pbcore.io import FastaReader, M4Reader
from TraceIO import TrxH5Reader
from PulseIO import PlxH5Reader

import numpy as np
from matplotlib.pyplot import *

data_root = "~/Data/2591006/0001/"
reports   = "~/Data/2591006/0001/Analysis_Results"
partName  = "m150324_213748_42194_c100643252550000001823124510151496_s1_X0.1"

t = TrxH5Reader(data_root + "/" + partName + ".trx.h5")
p = PlxH5Reader(reports + "/" + partName + ".plx.h5")
m4s = M4Reader(reports + "/hits.1.m4")


def extractHoleNumber(readName):
    return int(readName.split("/")[1])

hitReadNames = [m4.qName for m4 in m4s]
hnsInHits = set(map(extractHoleNumber, hitReadNames))
isect = hnsInHits.intersection(t.holeNumbers)

fs, fe = (124*75), (136*75)

z = t[109]
xs = z[:, fs:fe]

# 109, 182, 259
plz = p[109].pulsesByFrameInterval(fs, fe)



frames = np.arange(fs, fe)
time = frames/75.0

starts = plz.startFrame()/75.0
ends = plz.endFrame()/75.0


plot(time, np.transpose(xs), linewidth=2)

vlines(starts, 0, 500, linestyles="dashed")
vlines(ends, 0, 500, linestyles="dashed")


show()
