#!/usr/bin/env python
"""
Usage: traceViewer1.py [--debug]
                       [--pulse=PLXFILE]
                       --hole=HOLENUMBER
                       TRXFILE
"""
import numpy as np
import pyqtgraph as pg
from docopt import docopt
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.stack import TrxH5Reader, PlxH5Reader

def debug_trace():
  # http://stackoverflow.com/questions/1736015/debugging-a-pyqt4-app
  from ipdb import set_trace
  QtCore.pyqtRemoveInputHook()
  set_trace()


class PulseOverlayItem(pg.GraphicsObject):
    """
    The pulses!
    """
    def __init__(self, plsZmw, plot):
        # The `plot` argument is just used to determine the
        # effective visible area.  Not sure if there is a better way!
        pg.GraphicsObject.__init__(self)
        self.plsZmw = plsZmw
        self.plot = plot
        self.generatePicture()
        self._textItems = []

    def generatePicture(self):
        # Precompute a QPicture object
        allPulses = self.plsZmw.pulses()
        startFrame    = allPulses.startFrame()
        widthInFrames = allPulses.widthInFrames()
        channel       = allPulses.channel()
        base          = allPulses.channelBases()

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pens  = [ pg.mkPen((i, 4), width=2) for i in xrange(4) ]
        y = -5
        for i in xrange(len(channel)):
            c     = channel[i]
            start = startFrame[i]
            width = widthInFrames[i]

            p.setPen(pens[c])
            p.drawLine(QtCore.QPointF(start, y), QtCore.QPointF(start+width, y))

    def pulsesToLabel(self):
        """
        Returns None, or a ZmwPulses if we are focused on a small enough window for labeling
        """
        viewRange = self.plot.viewRange()[0]
        if viewRange[1] - viewRange[0] >= 500:
            return None
        pulsesToDraw = self.plsZmw.pulsesByFrameInterval(viewRange[0], viewRange[1])
        if len(pulsesToDraw) > 20:
            return None
        else:
            return pulsesToDraw

    def labelPulses(self, pulsesToLabel):
        # Remove the old labels from the scene
        for ti in self._textItems:
            ti.scene().removeItem(ti)
        self._textItems = []

        if pulsesToLabel is None: return

        print pulsesToLabel.channelBases()

        start   = pulsesToLabel.startFrame()
        width   = pulsesToLabel.widthInFrames()
        channel = pulsesToLabel.channel()
        base    = pulsesToLabel.channelBases()
        mid     = start + width / 2.0

        y = 800
        for i in xrange(len(base)):
            ti = pg.TextItem(base[i])
            ti.setParentItem(self)
            ti.setPos(mid[i], 800)
            self._textItems.append(ti)

    def paint(self, p, *args):
        # Draw the pulse blips
        p.drawPicture(0, 0, self.picture)
        # Draw pulse labels if the focus is small enough (< 500 frames)
        self.labelPulses(self.pulsesToLabel())

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())



class CustomViewBox(pg.ViewBox):
    """
    CustomViewBox implements the following behavior:
      - prevents scaling or panning in the y direction
      - ?
    """

    def __init__(self):
        super(CustomViewBox, self).__init__()

    def scaleBy(self, s=None, center=None, x=None, y=None):
        return super(CustomViewBox, self).scaleBy([s[0], 1.0], center, x, y)

    def translateBy(self, t=None, x=None, y=None):
        return super(CustomViewBox, self).translateBy(t, x, 0)


class TraceViewer(QtGui.QMainWindow):

    def __init__(self, trc, pls=None):
        """
        trc:        a TrxH5Reader object
        pls:        a PlxH5Reader object (or None)
        holeNumber: integer holenumber
        """
        super(TraceViewer, self).__init__()
        self.trc = trc
        self.pls = pls
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

    def renderTrace(self, traceData):
        # Clear plot1 first?
        for i in xrange(4):
            self.plot1.plot(traceData[i,:], pen=(i,4))

    def renderPulses(self, plsZmw):
        self.plot1.addItem(PulseOverlayItem(plsZmw, self.plot1))

    def setFocus(self, holeNumber, frameBegin=None, frameEnd=None):
        # TODO later: enable reusing data already loaded!
        traceData = self.trc[holeNumber]
        traceFrameExtent = (0, traceData.shape[1])

        if self.pls is not None:
            plsZmw = self.pls[holeNumber]
        else:
            plsZmw = None

        if (frameBegin is None) or (frameEnd is None):
            frameBegin, frameEnd = traceFrameExtent

        self.plot1.vb.setLimits(
            xMin=traceFrameExtent[0], xMax=traceFrameExtent[1],
            maxXRange=traceFrameExtent)

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


def main(argv):
    args = docopt(__doc__)
    if args["--debug"] is not None:
        print "Args: ", args
    trcFname = args["TRXFILE"]
    trc = TrxH5Reader(trcFname)
    holeNumber = int(args["--hole"])
    if args["--pulse"] is not None:
        pls = PlxH5Reader(args["--pulse"])
    else:
        pls = None

    app = QtGui.QApplication([])
    traceViewer = TraceViewer(trc, pls)
    traceViewer.setFocus(holeNumber)

    print args
    if args["--debug"]:
        debug_trace()
    app.exec_()

if __name__ == "__main__":
    import sys
    main(sys.argv)



# Thoughts:
#   A good start.  Things that would help:
#   - ability to pan with l/r buttons
#   - start with good defaults for x/y zoom, otherwise it looks like noise


# Look at CustomGraphics example for shapes
# Look at LabeledGraph example for text overlay

# Tooltips for pulses?
