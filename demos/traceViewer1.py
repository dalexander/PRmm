import numpy as np
import pyqtgraph as pg

from PRmm.stack import TrxH5Reader

def render(trc, holeNumber):
    traceData = trc[holeNumber]
    plotWidget = pg.plot(title="Trace!")
    for i in range(4):
        plotWidget.plot(traceData[i,:], pen=(i,4))


def main(argv):
    trcFname = argv[1]
    holeNumber = int(argv[2])
    trc = TrxH5Reader(trcFname)
    render(trc, holeNumber)
    # Event loop:
    from pyqtgraph.Qt import QtCore, QtGui
    QtGui.QApplication.instance().exec_()

if __name__ == "__main__":
    import sys
    main(sys.argv)



# Thoughts:
#   A good start.  Things that would help:
#   - ability to pan with l/r buttons
#   - restrict region clipping to the x axis---usually not interested in changing y span
#   - restrict spans to be within the bounds of the data
#   - start with good defaults for x/y zoom, otherwise it looks like noise
#   - overlay the pulses somehow (underline them maybe--y axis not a big deal)
#
# Can we reliably load the a whole trace in RAM?  Worst case?
#  - 6hr x 100fps x 4 x float32 = 35MB --- should work OK.
#
