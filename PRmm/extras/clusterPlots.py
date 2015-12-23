import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import math
from intervaltree import IntervalTree

from PRmm.model.regions import Region

def alignmentDetailsReport(zmwFixture):
    pass

def plot2C2AScatterTimeSeries(zmwFixture, frameInterval=4096):
    """
    Plot a 2C2A scatter plot for every `frameInterval` frames; overlay
    information about HQRegion and alignment(s), if found in the dataset.
    """
    t = zmwFixture.cameraTrace
    df = pd.DataFrame(np.transpose(t), columns=["C1", "C2"])

    # what is the extent of the data?  force a square perspective so
    # we don't distort the spectral angle
    xmin = ymin = min(df.min())
    xmax = ymax = max(df.max())

    def fracX(frac): return xmin + (xmax - xmin) * frac
    def fracY(frac): return ymin + (ymax - ymin) * frac

    numPanes = int(math.ceil(float(zmwFixture.numFrames) / frameInterval))
    numCols = 6
    numRows = int(math.ceil(float(numPanes) / numCols))
    paneSize = np.array([3, 3])

    figsize = np.array([numCols, numRows]) * paneSize
    fig, ax = plt.subplots(numRows, numCols, sharex=True, sharey=True,
                           figsize=figsize)
    axr = ax.ravel()

    details = "" # TODO
    fig.suptitle("%s\n%s" % (zmwFixture.zmwName, details), fontsize=20)


    alnIntervals = IntervalTree()
    for r in zmwFixture.regions:
        if r.regionType == Region.ALIGNMENT_REGION:
            alnIntervals.addi(r.startFrame, r.endFrame)

    def overlapsAln(frameStart, frameEnd):
        if alnIntervals.search(frameStart, frameEnd):
            return True
        else:
            return False

    for i in xrange(numPanes):
        frameSpan = startFrame, endFrame = i*frameInterval, (i+1)*frameInterval
        axr[i].set_xlim(xmin, xmax)
        axr[i].set_ylim(ymin, ymax)
        axr[i].plot(df.C1[startFrame:endFrame], df.C2[startFrame:endFrame], ".")

        baseSpan = zmwFixture.baseIntervalFromFrames(*frameSpan)
        axr[i].text(fracX(0.6), fracY(0.9), "/%d_%d" %  baseSpan)

        if overlapsAln(*frameSpan):
            axr[i].hlines(fracY(1.0), xmin, xmax, colors=["red"], linewidth=4)


    return axr
