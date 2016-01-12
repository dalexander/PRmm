#!/usr/bin/env python


import numpy as np
import pyqtgraph as pg
from docopt import docopt
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.ui.overlays import *
from PRmm.ui.tracePlot import *
from PRmm.ui.alignmentView import *
from PRmm.ui.styles import *

from PRmm.model import *

def debug_trace():
    # http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
    from ipdb import set_trace
    QtCore.pyqtRemoveInputHook()
    set_trace()


class TraceViewer(QtGui.QMainWindow):

    def __init__(self, readers):
        """
        readers: a readers fixture
        """
        super(TraceViewer, self).__init__()
        self.readers = readers
        self.style = styleForData(self.readers)
        self.zmw = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PRmm Trace Viewer")
        self.glw = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.glw)

        self.plot1 = TracePlotItem()
        self.glw.addItem(self.plot1)

        if self.readers.hasAlignments:
            self.glw.nextRow()
            self.alnView = AlignmentViewBox()
            self.glw.addItem(self.alnView)
        else:
            self.alnView = None

        if self.alnView is not None:
            # Only so this if we are showing base labels
            def xRangeChangedHandler(x):
                self.alnView.focus(*self.baseInterval)
            self.plot1.sigXRangeChanged.connect(xRangeChangedHandler)

        self.show()


    def renderTrace(self, traceData):
        numChannels = traceData.shape[0]
        for i in xrange(numChannels):
            self.plot1.plot(traceData[i,:], pen=self.style.tracePens[i])

    def renderPulses(self):
        self.plot1.addItem(PulsesOverlayItem(self.zmw, self.plot1, self.style))


    def renderRegions(self):
        self.plot1.addItem(RegionsOverlayItem(self.zmw.traceRegions, self.plot1))

    @property
    def movieName(self):
        return self.readers.movieName

    @property
    def zmwName(self):
        return self.zmw.zmwName

    @property
    def holeNumber(self):
        return self.zmw.holeNumber

    @property
    def frameInterval(self):
        return tuple(self.plot1.visibleSpanX)

    @property
    def baseInterval(self):
        if not (self.zmw.hasBases and self.zmw.hasPulses):
            raise Exception, "Base interval unavailable"
        return self.zmw.baseIntervalFromFrames(*self.frameInterval)

    def setFocus(self, holeNumber, frameBegin=None, frameEnd=None):
        # remove any items previously added to the plots (plot itself;
        # overlays, etc):
        self.plot1.clear()

        self.zmw = self.readers[holeNumber]
        traceData = self.zmw.cameraTrace
        traceFrameExtent = (0, traceData.shape[1])

        if (frameBegin is None) or (frameEnd is None):
            frameBegin, frameEnd = traceFrameExtent

        # Disallow zooming out beyond the trace extent
        self.plot1.vb.setLimits(
            xMin=traceFrameExtent[0], xMax=traceFrameExtent[1],
            maxXRange=traceFrameExtent)

        self.plot1.setTitle(self.zmwName)

        self.renderTrace(traceData)

        if self.zmw.hasPulses:
            self.renderPulses()

        if self.zmw.hasRegions:
            self.renderRegions()

        if self.zmw.hasBases and self.zmw.hasAlignments:
            self.alnView.setAlignments(self.zmw.multiAlignment)
            self.alnView.show()
        else:
            if self.alnView is not None:
                self.alnView.hide()


    @property
    def holeNumbersOfInterest(self):
        # TODO: cache this!
        return self.readers.holeNumbers

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


__doc__ = \
"""
Usage:
    main.py [--debug] --fixture=INIFILE::SECTION --hole=HOLENUMBER
"""

def main():
    args = docopt(__doc__)
    if args["--debug"] is not False:
        print "Args: \n", args
    fixtureArg = args["--fixture"]
    if "::" not in fixtureArg:
        fixtureIni, fixtureSection = "~/.pacbio/data-fixtures.ini", fixtureArg
    else:
        fixtureIni, fixtureSection = fixtureArg.split("::")
    fixture = Fixture.fromIniFile(fixtureIni, fixtureSection)

    holeNumber = int(args["--hole"])

    app = QtGui.QApplication([])
    traceViewer = TraceViewer(fixture)
    traceViewer.setFocus(holeNumber)

    if args["--debug"]:
        debug_trace()
    app.exec_()
