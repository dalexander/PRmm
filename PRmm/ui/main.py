#!/usr/bin/env python
"""
Usage: traceViewer1.py [--debug]
                       [--pls=PLXFILE]
                       [--bas=BAXFILE]
                       [--aln=ALNFILE]
                       --hole=HOLENUMBER
                       TRXFILE
"""
import numpy as np
import pyqtgraph as pg
from docopt import docopt
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.io import TrxH5Reader, PlxH5Reader, BasecallsUnavailable
from PRmm.ui.overlays import *
from PRmm.ui.tracePlot import *


def debug_trace():
    # http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
    from ipdb import set_trace
    QtCore.pyqtRemoveInputHook()
    set_trace()


class TraceViewer(QtGui.QMainWindow):

    def __init__(self, trc,
                 pls=None, bas=None, aln=None):
        """
        trc:        a TrxH5Reader object
        pls:        a PlxH5Reader object (or None)
        """
        super(TraceViewer, self).__init__()
        self.trc = trc
        self.pls = pls
        self.bas = bas
        self.aln = aln
        self.holeNumber = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PRmm Trace Viewer")
        self.glw = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.glw)
        self.plot1 = pg.PlotItem(viewBox=CustomViewBox(), title="")
        self.glw.addItem(self.plot1)
        self.glw.nextRow()
        self.plot2 = pg.PlotItem(viewBox=CustomViewBox(), title="")
        self.glw.addItem(self.plot2)
        self.show()

    def renderTrace(self, traceData):
        numChannels = traceData.shape[0]
        for i in xrange(numChannels):
            self.plot1.plot(traceData[i,:], pen=(i,numChannels))

    def renderPulses(self, plsZmw):
        self.plot1.addItem(PulsesOverlayItem(plsZmw, self.plot1))

    @property
    def movieName(self):
        return self.trc.movieName

    @property
    def zmwName(self):
        return self.movieName + "/" + str(self.holeNumber)

    def setFocus(self, holeNumber, frameBegin=None, frameEnd=None):
        self.holeNumber = holeNumber

        # TODO later: enable reusing data already loaded!
        traceData = self.trc[holeNumber]
        traceFrameExtent = (0, traceData.shape[1])

        if self.pls is not None:
            plsZmw = self.pls[holeNumber]
        else:
            plsZmw = None

        if (frameBegin is None) or (frameEnd is None):
            frameBegin, frameEnd = traceFrameExtent

        # Disallow zooming out beyond the trace extent
        self.plot1.vb.setLimits(
            xMin=traceFrameExtent[0], xMax=traceFrameExtent[1],
            maxXRange=traceFrameExtent)

        self.plot1.setTitle(self.zmwName)

        # TODO: actually use the extent to set the viewable range
        self.renderTrace(traceData)
        if self.pls is not None:
            self.renderPulses(plsZmw)


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

    # mouse event?


def main():
    args = docopt(__doc__)
    if args["--debug"] is not None:
        print "Args: ", args
    trcFname = args["TRXFILE"]
    trc = TrxH5Reader(trcFname)
    holeNumber = int(args["--hole"])

    # Optional readers
    if args["--pls"] is not None:
        if args["--bas"] is not None:
            pls = PlxH5Reader(args["--pls"], args["--bas"])
        else:
            pls = PlxH5Reader(args["--pls"])
    else:
        pls = None
    if args["--aln"] is not None:
        aln = (args["--aln"])
    else:
        aln = None
    app = QtGui.QApplication([])
    traceViewer = TraceViewer(trc, pls)
    traceViewer.setFocus(holeNumber)

    print args
    if args["--debug"]:
        debug_trace()
    app.exec_()


# Thoughts:
#   A good start.  Things that would help:
#   - ability to pan with l/r buttons
#   - start with good defaults for x/y zoom, otherwise it looks like noise


# Look at CustomGraphics example for shapes
# Look at LabeledGraph example for text overlay

# Tooltips for pulses?
