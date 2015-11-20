import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import math

def alignmentDetailsReport(zmwFixture):
    pass

def plot2C2AScatterTimeSeries(zmwFixture, frameInterval=4096):
    """
    Plot a 2C2A scatter plot for every `frameInterval` frames; overlay
    information about HQRegion and alignment(s), if found in the dataset.
    """
    t = zmwFixture.cameraTrace
    df = pd.DataFrame(np.transpose(t), columns=["C1", "C2"])

    # what is the extent of the data?
    xmin, ymin = df.min()
    xmax, ymax = df.max()

    def fracX(frac): return xmin + (xmax - xmin) * frac
    def fracY(frac): return ymin + (ymax - ymin) * frac

    numPanes = int(math.ceil(float(zmwFixture.numFrames) / frameInterval))
    numCols = 6
    numRows = int(math.ceil(float(numPanes) / numCols))
    paneSize = np.array([3, 3])

    matplotlib.rcParams['figure.figsize'] = np.array([numCols, numRows]) * paneSize
    fig, ax = plt.subplots(numRows, numCols, sharex=True, sharey=True, )
    axr = ax.ravel()

    details = "" # TODO
    fig.suptitle("%s\n%s" % (zmwFixture.zmwName, details), fontsize=20)

    for i in xrange(numPanes):
        frameSpan = startFrame, endFrame = i*frameInterval, (i+1)*frameInterval
        axr[i].set_xlim(xmin, xmax)
        axr[i].set_ylim(ymin, ymax)
        axr[i].plot(df.C1[startFrame:endFrame], df.C2[startFrame:endFrame], ".")

        baseSpan = zmwFixture.baseIntervalFromFrames(*frameSpan)
        axr[i].text(fracX(0.1), fracY(0.9), "/%d_%d" %  baseSpan)

        # alignment...

    return axr
