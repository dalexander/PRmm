import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.stack import TrxH5Reader

class CustomViewBox(pg.ViewBox):

    def __init__(self):
        super(CustomViewBox, self).__init__()

    def scaleBy(self, s=None, center=None, x=None, y=None):
        return super(CustomViewBox, self).scaleBy([s[0], 1.0], center, x, y)


    # TODO: handle attempts to pan up/down as well

class TraceViewer(QtGui.QMainWindow):

    def __init__(self, trc):
        """
        trc:        a TrxReader object
        holeNumber: integer holenumber
        """
        super(TraceViewer, self).__init__()
        self.trc = trc
        self.initUI()


    def initUI(self):
        self.setWindowTitle("PRmm Trace Viewer")
        self.glw = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.glw)

        self.plot1 = pg.PlotItem(viewBox=CustomViewBox(), title="Plot1")
        self.glw.addItem(self.plot1)

        self.glw.nextRow()

        self.plot2 = pg.PlotItem(viewBox=CustomViewBox(), title="Plot2")
        self.glw.addItem(self.plot2)

        self.show()

    def renderPlots(self, traceData, frameBegin, frameEnd):
        for i in xrange(4):
            self.plot1.plot(traceData[i,:], pen=(i,4))

    def setFocus(self, holeNumber, frameBegin=None, frameEnd=None):
        # TODO later: enable reusing data already loaded!
        traceData = self.trc[holeNumber]
        traceFrameExtent = (0, traceData.shape[1])

        if (frameBegin is None) or (frameEnd is None):
            frameBegin, frameEnd = traceFrameExtent
        # TODO
        # Set the limits (view box)
        #  - no zooming past the data extent
        #  - no zooming in the y-axis
        self.plot1.vb.setLimits(
            xMin=traceFrameExtent[0], xMax=traceFrameExtent[1],
            maxXRange=traceFrameExtent)

        self.renderPlots(traceData, frameBegin, frameEnd)

    def keyPressEvent(self, e):
        # GOAL:
        # * L/R: scroll
        # * -/=: zoom
        # * [/]: go back and forth in history

        print "Key pressed!"

        if e.key() == QtCore.Qt.Key_Left:
            print "Left!"

        elif e.key() == QtCore.Qt.Key_Right:
            print "Right!"

        elif e.key() == QtCore.Qt.Key_Escape:
            self.close()

    # scroll event?

    # mouse event?


def main(argv):
    trcFname = argv[1]
    holeNumber = int(argv[2])
    trc = TrxH5Reader(trcFname)
    app = QtGui.QApplication([])
    traceViewer = TraceViewer(trc)
    traceViewer.setFocus(holeNumber)
    if "--debug" in argv:
        print "Debugging!"*100
        import ipdb
        ipdb.set_trace()
    else:
        app.exec_()

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


# Look at plotwidget
# Look at "plot customization" example
# Look at "GRaphics layout example" to see nesting, etc.
# Look at "graphitem" to see how to put shapes
