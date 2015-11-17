import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from PRmm.io import BasecallsUnavailable
from PRmm.model import Region

class RegionsOverlayItem(pg.GraphicsObject):
    """
    Region display
    """
    pens =    { Region.ADAPTER_REGION   : pg.mkPen(pg.mkColor(255,255,255), width=2),
                Region.INSERT_REGION    : pg.mkPen(pg.mkColor(  0,100,  0), width=2),
                Region.HQ_REGION        : pg.mkPen(pg.mkColor(100,  0,  0), width=2),
                Region.ALIGNMENT_REGION : pg.mkPen(pg.mkColor(100,100,  0), width=2)  }

    heights = { Region.ADAPTER_REGION   : 0.97,
                Region.INSERT_REGION    : 0.97,
                Region.HQ_REGION        : 0.98,
                Region.ALIGNMENT_REGION : 1.00 }

    def __init__(self, regions, plot):
        pg.GraphicsObject.__init__(self)
        self.plot = plot
        self.regions = regions
        self.generatePicture()

    def regionOverlayY(self, regionType):
        f = self.heights[regionType]
        a, b = self.plot.visibleSpanY
        return a + (b - a) * f

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)

        # Make this a checkbox in GUI
        regionTypesOfInterest = ( Region.ALIGNMENT_REGION, Region.ADAPTER_REGION )

        for region in self.regions:
            if region.regionType in regionTypesOfInterest:
                p.setPen(self.pens[region.regionType])
                y = self.regionOverlayY(region.regionType)
                p.drawLine(QtCore.QPointF(region.startFrame, y),
                           QtCore.QPointF(region.endFrame, y))

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())



class PulsesOverlayItem(pg.GraphicsObject):
    """
    The pulses!
    """
    def __init__(self, zmwFixture, plot):
        pg.GraphicsObject.__init__(self)
        self.zmw = zmwFixture
        self.plot = plot
        self.generatePicture()
        self._textItems = []

    @property
    def pulseLabelY(self):
        a, b = self.plot.visibleSpanY
        return a + (b - a) * 0.84

    def generatePicture(self):
        # Precompute a QPicture object
        startFrame    = self.zmw.pulseStartFrame
        widthInFrames = self.zmw.pulseWidth
        channel       = self.zmw.pulseChannel
        base          = self.zmw.pulseLabel

        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        pens  = [ pg.mkPen((i, 4), width=2) for i in xrange(4) ]
        y = -5
        for i in xrange(len(channel)):
            c     = channel[i]
            start = startFrame[i]
            width = widthInFrames[i]
            end = start + width
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

    def labelPulses(self):
        # Remove the old labels from the scene
        for ti in self._textItems:
            ti.scene().removeItem(ti)
        self._textItems = []

        start      = self.zmw.pulseStartFrame
        width      = self.zmw.pulseWidth
        channel    = self.zmw.pulseChannel
        base       = self.zmw.pulseLabel
        mid        = start + width / 2.0
        try:
            isBase = self.zmw.pulseIsBase
        except BasecallsUnavailable:
            isBase = np.ones_like(channel, dtype=bool)

        y = self.pulseLabelY
        for i in xrange(len(base)):
            pulseLabel = base[i] if isBase[i] else "-"
            ti = pg.TextItem(pulseLabel, anchor=(0.5, 0.5))
            ti.setParentItem(self)
            ti.setPos(mid[i], y)
            self._textItems.append(ti)

    def paint(self, p, *args):
        # Draw the pulse blips
        p.drawPicture(0, 0, self.picture)
        # Draw pulse labels if the focus is small enough (< 500 frames)
        self.labelPulses()

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
