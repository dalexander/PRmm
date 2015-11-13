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
from bisect import bisect_left, bisect_right
import pyqtgraph as pg
from docopt import docopt
from pyqtgraph.Qt import QtCore, QtGui

from pbcore.io import BasH5Reader, CmpH5Reader

from PRmm.io import TrcH5Reader, PlsH5Reader, BasecallsUnavailable
from PRmm.ui.overlays import *
from PRmm.ui.tracePlot import *
from PRmm.ui.alignmentView import *

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

        self.plot1 = TracePlotItem()
        self.glw.addItem(self.plot1)

        if self.aln is not None:
            self.glw.nextRow()
            self.alnView = AlignmentViewBox._uninitialized()
            self.glw.addItem(self.alnView)
        else:
            self.alnView = None

        if self.alnView is not None:
            # Only so this if we are showing base labels
            def xRangeChangedHandler(x):
                print "The x-axis was changed!"
                print self.frameInterval
                print self.baseInterval
                self.alnView.focus(*self.baseInterval)
            self.plot1.sigXRangeChanged.connect(xRangeChangedHandler)

        self.show()


    def renderTrace(self, traceData):
        numChannels = traceData.shape[0]
        for i in xrange(numChannels):
            self.plot1.plot(traceData[i,:], pen=(i,numChannels))

    def renderPulses(self, plsZmw):
        self.plot1.addItem(PulsesOverlayItem(plsZmw, self.plot1))

    def renderRegions(self, regions):
        self.plot1.addItem(RegionsOverlayItem(regions, self.plot1))

    @property
    def movieName(self):
        return self.trc.movieName

    @property
    def zmwName(self):
        return self.movieName + "/" + str(self.holeNumber)

    @property
    def frameInterval(self):
        return tuple(self.plot1.visibleSpanX)

    @property
    def baseInterval(self):
        if self.basZmw is None:
            raise Exception, "Base interval unavailable"
        else:
            frameStart, frameEnd = self.frameInterval
            return (bisect_left(self.basEndFrame, frameStart),
                    bisect_right(self.basStartFrame, frameEnd))

    def setFocus(self, holeNumber, frameBegin=None, frameEnd=None):
        # remove any items previously added to the plots (plot itself;
        # overlays, etc):
        self.plot1.clear()

        self.holeNumber = holeNumber
        traceData = self.trc[holeNumber]
        traceFrameExtent = (0, traceData.shape[1])

        if self.pls is not None:
            self.plsZmw = self.pls[holeNumber]
        else:
            self.plsZmw = None

        if self.bas is not None:
            self.basZmw = self.bas[holeNumber]
        else:
            self.basZmw = None

        if (self.bas is not None) and (self.pls is not None):
            pulseStartFrame = self.plsZmw.pulses().startFrame()
            pi = self.basZmw.readNoQC().PulseIndex()
            self.basStartFrame = pulseStartFrame[pi]
            self.basEndFrame = self.basStartFrame + self.basZmw.readNoQC().WidthInFrames()

        if (frameBegin is None) or (frameEnd is None):
            frameBegin, frameEnd = traceFrameExtent

        # Disallow zooming out beyond the trace extent
        self.plot1.vb.setLimits(
            xMin=traceFrameExtent[0], xMax=traceFrameExtent[1],
            maxXRange=traceFrameExtent)

        self.plot1.setTitle(self.zmwName)

        self.renderTrace(traceData)
        if self.plsZmw is not None:
            self.renderPulses(self.plsZmw)

        if self.aln is not None:
            self.alns = self.aln.readsByHoleNumber(holeNumber)
        else:
            self.alns = []

        if (self.basZmw is not None) and (self.plsZmw is not None):
            regions = Region.fetchRegions(self.basZmw, self.plsZmw, self.alns)
            self.renderRegions(regions)

        if (self.basZmw is not None and self.alns):
            self.alnView.setAlignments(self.basZmw, self.alns)
            self.alnView.show()
        else:
            self.alnView.hide()


    @property
    def holeNumbersOfInterest(self):
        # TODO: cache this!
        return self.trc.holeNumbers

    def nextHoleNumber(self, hns, curHn):
        iNext = hns.searchsorted(curHn, side="right")
        print curHn, iNext, hns[iNext]
        if iNext == len(hns):
            print "No next holenumber"
            return None
        else: return hns[iNext]

    def prevHoleNumber(self, hns, curHn):
        iPrev = hns.searchsorted(curHn, side="left") - 1
        print curHn, iPrev, hns[iPrev]
        if iPrev == -1:
            print "No previous holenumber"
            return None
        else: return hns[iPrev]

    def keyPressEvent(self, e):
        # GOAL:
        # * L/R: scroll
        # * -/=: zoom
        # * [/]: go back and forth in history
        print "Key pressed!"

        key = e.key()

        if key == QtCore.Qt.Key_N:
            self.setFocus(self.nextHoleNumber(self.holeNumbersOfInterest, self.holeNumber))
        elif key == QtCore.Qt.Key_P:
            self.setFocus(self.prevHoleNumber(self.holeNumbersOfInterest, self.holeNumber))

        elif key == QtCore.Qt.Key_Left:
            print "Left!"

        elif key == QtCore.Qt.Key_Right:
            print "Right!"

        elif key == QtCore.Qt.Key_Escape:
            self.close()

    # mouse event?


def main():
    args = docopt(__doc__)
    if args["--debug"] is not False:
        print "Args: ", args
    trcFname = args["TRXFILE"]
    trc = TrcH5Reader(trcFname)
    holeNumber = int(args["--hole"])

    # -- Optional readers
    if args["--bas"] is not None:
        bas = BasH5Reader(args["--bas"])
    else:
        bas = None

    if args["--pls"] is not None:
        pls = PlsH5Reader(args["--pls"], bas)
    else:
        pls = None

    if args["--aln"] is not None:
        aln = CmpH5Reader(args["--aln"])
    else:
        aln = None
    # --

    app = QtGui.QApplication([])
    traceViewer = TraceViewer(trc, pls, bas, aln)
    traceViewer.setFocus(holeNumber)

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
